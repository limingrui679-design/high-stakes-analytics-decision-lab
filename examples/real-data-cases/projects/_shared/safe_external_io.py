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
from typing import Any, BinaryIO, Iterator

DEFAULT_USER_AGENT = "High-Stakes-Analytics-Decision-Lab/1.0"
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
    if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
        raise ValueError("External URLs must not target a local hostname.")
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("External URLs must not target a non-public IP address.")
    return url


class HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep every redirect on HTTPS and stop redirect chains at five hops."""

    max_redirections = MAX_REDIRECTS
    max_repeats = 2

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: BinaryIO,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        ensure_https_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _BoundedReader(io.RawIOBase):
    def __init__(
        self,
        raw: BinaryIO,
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

    def readinto(self, buffer: bytearray | memoryview) -> int:
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
    timeout: int = 180,
    maximum_bytes: int = DEFAULT_RESPONSE_LIMIT_BYTES,
    user_agent: str = DEFAULT_USER_AGENT,
    accept: str = "*/*",
) -> Iterator[io.BufferedReader]:
    """Open a bounded HTTPS stream whose redirects remain on HTTPS."""

    if timeout <= 0:
        raise ValueError("timeout must be positive.")
    if maximum_bytes < 0:
        raise ValueError("maximum_bytes must be non-negative.")
    ensure_https_url(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": accept},
    )
    opener = urllib.request.build_opener(HttpsOnlyRedirectHandler())
    with opener.open(request, timeout=timeout) as response:  # nosec B310
        ensure_https_url(response.geturl())
        _validated_content_length(response, maximum_bytes)
        bounded = io.BufferedReader(
            _BoundedReader(
                response,
                maximum_bytes,
                deadline=time.monotonic() + timeout,
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
    for attempt in range(attempts):
        try:
            with open_https_stream(
                url,
                timeout=timeout,
                maximum_bytes=maximum_bytes,
                user_agent=user_agent,
                accept=accept,
            ) as stream:
                return stream.read()
        except urllib.error.HTTPError:
            raise
        except (
            http.client.IncompleteRead,
            OSError,
            TimeoutError,
            urllib.error.URLError,
        ):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2**attempt, 2))
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
                timeout=timeout,
                maximum_bytes=maximum_bytes,
                user_agent=user_agent,
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
        ):
            partial.unlink(missing_ok=True)
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2**attempt, 2))
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
    command = [
        curl,
        "--location",
        "--max-redirs",
        str(MAX_REDIRECTS),
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
        "--connect-timeout",
        "30",
        "--max-time",
        str(timeout),
        "--max-filesize",
        str(maximum_bytes),
        "--user-agent",
        user_agent,
        "--output",
        str(partial),
        "--write-out",
        "%{url_effective}",
        url,
    ]
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout + 10,
        )
        ensure_https_url(result.stdout.strip())
        observed = partial.stat().st_size
        if observed > maximum_bytes:
            raise ValueError(
                f"HTTPS response exceeds {maximum_bytes} bytes."
            )
        os.replace(partial, destination)
        return observed
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


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


def _archive_size(source: Path | BinaryIO) -> int | None:
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
) -> None:
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


@contextlib.contextmanager
def open_safe_zip(
    source: Path | BinaryIO,
    *,
    limits: ZipLimits = DEFAULT_ZIP_LIMITS,
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
        validate_zip_archive(archive, limits=limits)
        yield archive


@contextlib.contextmanager
def open_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    *,
    maximum_bytes: int | None = None,
) -> Iterator[io.BufferedReader]:
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
