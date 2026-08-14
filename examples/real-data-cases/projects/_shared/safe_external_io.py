#!/usr/bin/env python3
"""Bounded HTTPS and ZIP I/O shared by runtime and source builders."""

from __future__ import annotations

import contextlib
import http.client
import io
import ipaddress
import os
import re
import shutil
import socket
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO, Any, Iterator

DEFAULT_USER_AGENT = "High-Stakes-Analytics-Decision-Lab/1.0.5"
DEFAULT_DOWNLOAD_LIMIT_BYTES = 512 * 1024 * 1024
DEFAULT_RESPONSE_LIMIT_BYTES = 64 * 1024 * 1024
MAX_REDIRECTS = 5


def ensure_https_url(url: str) -> str:
    """Accept only absolute, credential-free HTTPS URLs."""

    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.casefold() != "https" or not parsed.hostname:
        raise ValueError(f"External URL must use HTTPS: {url!r}")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("External URLs must not embed credentials.")
    hostname = parsed.hostname.casefold()
    if (
        hostname == "localhost"
        or hostname.endswith(".localhost")
        or hostname.endswith(".local")
    ):
        raise ValueError("External URLs must not target a local hostname.")
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("External URLs must not target a non-public IP address.")
    return url


def _resolve_public_addresses(url: str) -> frozenset[str]:
    """Resolve an HTTPS endpoint and reject every non-public answer."""

    ensure_https_url(url)
    parsed = urllib.parse.urlsplit(url)
    hostname = parsed.hostname
    if hostname is None:  # guarded by ensure_https_url; retained for type checkers
        raise ValueError("External URL is missing a hostname.")
    port = parsed.port or 443
    try:
        literal = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        literal = None
    if literal is not None:
        addresses = {str(literal)}
    else:
        try:
            answers = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as error:
            raise urllib.error.URLError(
                f"Could not resolve external hostname {hostname!r}."
            ) from error
        addresses = {str(ipaddress.ip_address(answer[4][0])) for answer in answers}
    if not addresses:
        raise urllib.error.URLError(
            f"External hostname {hostname!r} returned no addresses."
        )
    non_public = sorted(
        address
        for address in addresses
        if not ipaddress.ip_address(address).is_global
    )
    if non_public:
        raise ValueError(
            "External hostname resolves to a non-public IP address: "
            + ", ".join(non_public)
        )
    return frozenset(addresses)


def _response_peer_address(response: Any) -> str | None:
    """Best-effort extraction of the connected socket peer from urllib."""

    attribute_paths = (
        ("fp", "raw", "_sock"),
        ("fp", "_sock"),
        ("raw", "_sock"),
        ("_sock",),
    )
    for path in attribute_paths:
        candidate = response
        try:
            for attribute in path:
                candidate = getattr(candidate, attribute)
            peer = candidate.getpeername()
        except (AttributeError, OSError):
            continue
        if peer:
            return str(ipaddress.ip_address(peer[0]))
    return None


def _require_public_peer(response: Any) -> str:
    """Fail closed unless the connected HTTPS peer is observable and public."""

    peer_address = _response_peer_address(response)
    if peer_address is None:
        raise ValueError("Could not verify the HTTPS connection peer address.")
    if not ipaddress.ip_address(peer_address).is_global:
        raise ValueError(
            "HTTPS connection reached a non-public peer address: "
            f"{peer_address}"
        )
    return peer_address


def _remaining_time(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("HTTPS operation exceeded its total time limit.")
    return remaining


def _sleep_before_retry(deadline: float, attempt: int, error: BaseException) -> None:
    remaining = _remaining_time(deadline)
    delay = min(float(2**attempt), 2.0)
    if delay >= remaining:
        raise TimeoutError("HTTPS operation exceeded its total time limit.") from error
    time.sleep(delay)


class HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep every redirect on HTTPS and stop redirect chains at five hops."""

    max_redirections = MAX_REDIRECTS
    max_repeats = 2

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: IO[bytes],
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        ensure_https_url(newurl)
        _require_public_peer(fp)
        _resolve_public_addresses(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _BoundedReader(io.RawIOBase):
    def __init__(
        self,
        raw: IO[bytes],
        maximum_bytes: int,
        *,
        deadline: float | None = None,
    ) -> None:
        self._raw = raw
        self._maximum_bytes = maximum_bytes
        self._observed = 0
        self._deadline = deadline

    def readable(self) -> bool:
        return True

    def read(self, size: int = -1) -> bytes:
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TimeoutError("HTTPS response exceeded its total time limit.")
        remaining = self._maximum_bytes - self._observed
        requested = remaining + 1 if size < 0 else min(size, remaining + 1)
        data = self._raw.read(requested)
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TimeoutError("HTTPS response exceeded its total time limit.")
        self._observed += len(data)
        if self._observed > self._maximum_bytes:
            raise ValueError(
                f"HTTPS response exceeds {self._maximum_bytes} bytes."
            )
        return data

    def readinto(self, buffer: Any) -> int:
        data = self.read(len(buffer))
        buffer[: len(data)] = data
        return len(data)

    def close(self) -> None:
        try:
            self._raw.close()
        finally:
            super().close()


def _validated_content_length(response: Any, maximum_bytes: int) -> None:
    header = response.headers.get("Content-Length")
    if header is None:
        return
    try:
        length = int(header)
    except ValueError as error:
        raise ValueError("HTTPS response has an invalid Content-Length header.") from error
    if length < 0 or length > maximum_bytes:
        raise ValueError(
            f"HTTPS response declares {length} bytes; limit is {maximum_bytes}."
        )


@contextlib.contextmanager
def open_https_stream(
    url: str,
    *,
    timeout: float = 180,
    maximum_bytes: int = DEFAULT_RESPONSE_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
    accept: str = "*/*",
    deadline: float | None = None,
) -> Iterator[IO[bytes]]:
    """Open a bounded HTTPS stream whose redirects remain on HTTPS."""

    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    if maximum_bytes < 0:
        raise ValueError("maximum_bytes must be non-negative.")
    ensure_https_url(url)
    if deadline is None:
        deadline = time.monotonic() + timeout
    _resolve_public_addresses(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": accept},
    )
    opener = urllib.request.build_opener(HttpsOnlyRedirectHandler())
    with opener.open(  # nosec B310
        request,
        timeout=_remaining_time(deadline),
    ) as response:
        final_url = ensure_https_url(response.geturl())
        _resolve_public_addresses(final_url)
        _require_public_peer(response)
        _validated_content_length(response, maximum_bytes)
        bounded = io.BufferedReader(
            _BoundedReader(
                response,
                maximum_bytes,
                deadline=deadline,
            )
        )
        try:
            yield bounded
        finally:
            bounded.close()


def read_https_bytes(
    url: str,
    *,
    timeout: int = 180,
    maximum_bytes: int = DEFAULT_RESPONSE_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
    accept: str = "*/*",
    attempts: int = 3,
) -> bytes:
    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    deadline = time.monotonic() + timeout
    for attempt in range(attempts):
        try:
            with open_https_stream(
                url,
                timeout=_remaining_time(deadline),
                maximum_bytes=maximum_bytes,
                user_agent=user_agent,
                accept=accept,
                deadline=deadline,
            ) as stream:
                return stream.read()
        except urllib.error.HTTPError:
            raise
        except (
            http.client.IncompleteRead,
            OSError,
            TimeoutError,
            urllib.error.URLError,
        ) as error:
            if attempt + 1 == attempts:
                raise
            _sleep_before_retry(deadline, attempt, error)
    raise AssertionError("unreachable")


def download_https(
    url: str,
    destination: Path,
    *,
    timeout: int = 900,
    maximum_bytes: int = DEFAULT_DOWNLOAD_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
    attempts: int = 3,
) -> int:
    """Download atomically, deleting a partial file on every failure."""

    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    deadline = time.monotonic() + timeout
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if destination.is_symlink() or partial.is_symlink():
        raise ValueError("Download destinations must not be symbolic links.")
    partial.unlink(missing_ok=True)
    for attempt in range(attempts):
        observed = 0
        try:
            with open_https_stream(
                url,
                timeout=_remaining_time(deadline),
                maximum_bytes=maximum_bytes,
                user_agent=user_agent,
                deadline=deadline,
            ) as source, partial.open("xb") as target:
                while True:
                    block = source.read(1024 * 1024)
                    if not block:
                        break
                    target.write(block)
                    observed += len(block)
            os.replace(partial, destination)
            return observed
        except urllib.error.HTTPError:
            partial.unlink(missing_ok=True)
            raise
        except (
            http.client.IncompleteRead,
            OSError,
            TimeoutError,
            urllib.error.URLError,
        ) as error:
            partial.unlink(missing_ok=True)
            if attempt + 1 == attempts:
                raise
            _sleep_before_retry(deadline, attempt, error)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
    raise AssertionError("unreachable")


def download_https_with_curl(
    url: str,
    destination: Path,
    *,
    timeout: int = 900,
    maximum_bytes: int = DEFAULT_DOWNLOAD_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> int:
    """Use curl for endpoints with broken HTTP framing, retaining all boundaries."""

    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    if maximum_bytes < 0:
        raise ValueError("maximum_bytes must be non-negative.")
    ensure_https_url(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    if destination.is_symlink() or partial.is_symlink():
        raise ValueError("Download destinations must not be symbolic links.")
    partial.unlink(missing_ok=True)
    curl = shutil.which("curl")
    if curl is None:
        raise RuntimeError("curl is required for this source endpoint.")
    curl = str(Path(curl).resolve(strict=True))
    headers = partial.with_name(partial.name + ".headers")
    headers.unlink(missing_ok=True)
    deadline = time.monotonic() + timeout
    current_url = url
    try:
        for redirect_count in range(MAX_REDIRECTS + 1):
            addresses = _resolve_public_addresses(current_url)
            parsed = urllib.parse.urlsplit(current_url)
            hostname = parsed.hostname
            if hostname is None:  # guarded by ensure_https_url
                raise ValueError("External URL is missing a hostname.")
            port = parsed.port or 443
            remaining = _remaining_time(deadline)
            command = [
                curl,
                "--max-redirs",
                "0",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--fail",
                "--silent",
                "--show-error",
                "--retry",
                "3",
                "--retry-all-errors",
                "--retry-delay",
                "1",
                "--retry-max-time",
                str(max(1, int(remaining))),
                "--connect-timeout",
                str(max(1, min(30, int(remaining)))),
                "--max-time",
                str(max(1, int(remaining))),
                "--max-filesize",
                str(maximum_bytes),
                "--user-agent",
                user_agent,
                "--dump-header",
                str(headers),
                "--output",
                str(partial),
                "--write-out",
                "%{http_code}\n%{url_effective}",
            ]
            for address in sorted(addresses):
                rendered_address = f"[{address}]" if ":" in address else address
                command.extend(
                    ["--resolve", f"{hostname}:{port}:{rendered_address}"]
                )
            command.append(current_url)
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=_remaining_time(deadline) + 1,
            )
            output_lines = result.stdout.strip().splitlines()
            if len(output_lines) < 2 or not output_lines[0].isdigit():
                raise ValueError("curl returned an invalid HTTP status record.")
            status = int(output_lines[0])
            effective_url = ensure_https_url(output_lines[-1])
            _resolve_public_addresses(effective_url)
            if 300 <= status < 400:
                if redirect_count == MAX_REDIRECTS:
                    raise ValueError(
                        f"HTTPS redirect chain exceeds {MAX_REDIRECTS} hops."
                    )
                location = _redirect_location(headers)
                current_url = ensure_https_url(
                    urllib.parse.urljoin(effective_url, location)
                )
                partial.unlink(missing_ok=True)
                headers.unlink(missing_ok=True)
                continue
            if not 200 <= status < 300:
                raise ValueError(f"Unexpected HTTPS status from curl: {status}")
            observed = partial.stat().st_size
            if observed > maximum_bytes:
                raise ValueError(
                    f"HTTPS response exceeds {maximum_bytes} bytes."
                )
            os.replace(partial, destination)
            headers.unlink(missing_ok=True)
            return observed
        raise AssertionError("unreachable")
    except BaseException:
        partial.unlink(missing_ok=True)
        headers.unlink(missing_ok=True)
        raise


def _redirect_location(headers: Path) -> str:
    """Return the final Location header emitted for one non-following curl call."""

    blocks = re.split(r"\r?\n\r?\n", headers.read_text(encoding="iso-8859-1"))
    for block in reversed(blocks):
        if not block.startswith("HTTP/"):
            continue
        for line in block.splitlines()[1:]:
            name, separator, value = line.partition(":")
            if separator and name.casefold() == "location":
                location = value.strip()
                if location:
                    return location
    raise ValueError("HTTPS redirect response is missing a Location header.")


def read_https_bytes_with_curl(
    url: str,
    *,
    timeout: int = 180,
    maximum_bytes: int = DEFAULT_RESPONSE_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
) -> bytes:
    with tempfile.TemporaryDirectory(prefix="hsdl-https-") as directory:
        target = Path(directory) / "response.bin"
        download_https_with_curl(
            url,
            target,
            timeout=timeout,
            maximum_bytes=maximum_bytes,
            user_agent=user_agent,
        )
        return target.read_bytes()


@dataclass(frozen=True)
class ZipLimits:
    maximum_archive_bytes: int = 512 * 1024 * 1024
    maximum_members: int = 4_096
    maximum_member_bytes: int = 256 * 1024 * 1024
    maximum_total_uncompressed_bytes: int = 1024 * 1024 * 1024
    maximum_expansion_ratio: float = 200.0
    maximum_member_name_characters: int = 4_096
    label: str = "ZIP"


DEFAULT_ZIP_LIMITS = ZipLimits()


@dataclass
class ArchiveBudget:
    """Cumulative expansion budget shared by nested archive layers."""

    maximum_depth: int = 2
    maximum_members: int = 4_096
    maximum_total_uncompressed_bytes: int = 1024 * 1024 * 1024
    observed_members: int = 0
    observed_uncompressed_bytes: int = 0

    def account(self, *, depth: int, members: int, uncompressed_bytes: int) -> None:
        if depth < 1 or depth > self.maximum_depth:
            raise ValueError(
                f"Nested archive depth {depth} exceeds limit {self.maximum_depth}."
            )
        new_members = self.observed_members + members
        if new_members > self.maximum_members:
            raise ValueError(
                "Nested archives contain "
                f"{new_members} cumulative members; limit is {self.maximum_members}."
            )
        new_bytes = self.observed_uncompressed_bytes + uncompressed_bytes
        if new_bytes > self.maximum_total_uncompressed_bytes:
            raise ValueError(
                "Nested archives expand to "
                f"{new_bytes} cumulative bytes; limit is "
                f"{self.maximum_total_uncompressed_bytes}."
            )
        self.observed_members = new_members
        self.observed_uncompressed_bytes = new_bytes


def _archive_size(source: Path | IO[bytes]) -> int | None:
    if isinstance(source, Path):
        return source.stat().st_size
    if isinstance(source, io.BytesIO):
        return source.getbuffer().nbytes
    try:
        position = source.tell()
        source.seek(0, os.SEEK_END)
        size = source.tell()
        source.seek(position)
        return size
    except (AttributeError, OSError):
        return None


def validate_zip_archive(
    archive: zipfile.ZipFile,
    *,
    limits: ZipLimits = DEFAULT_ZIP_LIMITS,
) -> tuple[int, int]:
    members = archive.infolist()
    if len(members) > limits.maximum_members:
        raise ValueError(
            f"{limits.label} contains {len(members)} members; "
            f"limit is {limits.maximum_members}."
        )
    names: set[str] = set()
    canonical_names: set[str] = set()
    total = 0
    for member in members:
        name = member.filename
        if len(name) > limits.maximum_member_name_characters:
            raise ValueError(
                f"{limits.label} member name exceeds "
                f"{limits.maximum_member_name_characters} characters."
            )
        if name in names:
            raise ValueError(f"Duplicate {limits.label} member name: {name}")
        names.add(name)
        member_path = PurePosixPath(name)
        if (
            not name
            or "\x00" in name
            or member_path.is_absolute()
            or ".." in member_path.parts
            or "\\" in name
            or re.match(r"^[A-Za-z]:", name) is not None
        ):
            raise ValueError(f"Unsafe {limits.label} member path: {name}")
        canonical_name = "/".join(
            part for part in member_path.parts if part not in {"", "."}
        ).casefold()
        if canonical_name in canonical_names:
            raise ValueError(
                f"Canonical {limits.label} member path is duplicated: {name}"
            )
        canonical_names.add(canonical_name)
        if member.flag_bits & 0x1:
            raise ValueError(f"Encrypted {limits.label} member is unsupported: {name}")
        mode = (member.external_attr >> 16) & 0xFFFF
        if mode and stat.S_ISLNK(mode):
            raise ValueError(f"Symbolic-link {limits.label} member is unsupported: {name}")
        if member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise ValueError(
                f"Unsupported {limits.label} compression method for member: {name}"
            )
        if member.file_size < 0 or member.compress_size < 0:
            raise ValueError(f"Invalid {limits.label} member size: {name}")
        if member.file_size > limits.maximum_member_bytes:
            raise ValueError(
                f"{limits.label} member exceeds {limits.maximum_member_bytes} bytes: {name}"
            )
        total += member.file_size
        if total > limits.maximum_total_uncompressed_bytes:
            raise ValueError(
                f"{limits.label} uncompressed content exceeds "
                f"{limits.maximum_total_uncompressed_bytes} bytes."
            )
        if member.file_size:
            if not member.compress_size:
                raise ValueError(f"Invalid compressed size for {limits.label} member: {name}")
            ratio = member.file_size / member.compress_size
            if ratio > limits.maximum_expansion_ratio:
                raise ValueError(
                    f"{limits.label} member expansion ratio {ratio:.1f} exceeds "
                    f"{limits.maximum_expansion_ratio:.1f}: {name}"
                )
    return len(members), total


@contextlib.contextmanager
def open_safe_zip(
    source: Path | IO[bytes],
    *,
    limits: ZipLimits = DEFAULT_ZIP_LIMITS,
    budget: ArchiveBudget | None = None,
    depth: int = 1,
) -> Iterator[zipfile.ZipFile]:
    size = _archive_size(source)
    if size is not None and size > limits.maximum_archive_bytes:
        raise ValueError(
            f"{limits.label} archive is {size} bytes; "
            f"limit is {limits.maximum_archive_bytes}."
        )
    if isinstance(source, Path) and not source.is_file():
        raise FileNotFoundError(source)
    if not zipfile.is_zipfile(source):
        raise ValueError(f"Expected a {limits.label} archive.")
    with zipfile.ZipFile(source) as archive:
        members, uncompressed_bytes = validate_zip_archive(archive, limits=limits)
        if budget is not None:
            budget.account(
                depth=depth,
                members=members,
                uncompressed_bytes=uncompressed_bytes,
            )
        yield archive


@contextlib.contextmanager
def open_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    *,
    maximum_bytes: int | None = None,
) -> Iterator[IO[bytes]]:
    try:
        member = archive.getinfo(name)
    except KeyError as error:
        raise ValueError(f"Required ZIP member is missing: {name}") from error
    limit = member.file_size if maximum_bytes is None else maximum_bytes
    if member.file_size > limit:
        raise ValueError(f"ZIP member exceeds {limit} bytes: {name}")
    raw = archive.open(member)
    bounded = io.BufferedReader(_BoundedReader(raw, limit))
    try:
        yield bounded
    finally:
        bounded.close()


def read_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    *,
    maximum_bytes: int | None = None,
) -> bytes:
    with open_zip_member(archive, name, maximum_bytes=maximum_bytes) as stream:
        return stream.read()
