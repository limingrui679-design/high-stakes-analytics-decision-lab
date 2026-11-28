"""Derive comparable eight-second wrist and chest summaries from two public studies."""

import pickle
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from scipy import signal


class ArrayReader(pickle.Unpickler):
    def find_class(self, mod, name):
        import _codecs

        choices = {
            ("numpy", "dtype"): np.dtype,
            ("numpy", "ndarray"): np.ndarray,
            ("_codecs", "encode"): _codecs.encode,
        }
        for module in ("numpy.core.multiarray", "numpy._core.multiarray"):
            choices[module, "_reconstruct"] = np._core.multiarray._reconstruct
            choices[module, "scalar"] = np._core.multiarray.scalar
        if (mod, name) not in choices:
            raise ValueError(f"Unsupported upstream array class: {mod}.{name}")
        return choices[mod, name]


def segments(archive, cohort):
    for member in sorted(n for n in archive.namelist() if re.search(r"/S\d+/S\d+\.pkl$", n)):
        subject = Path(member).stem
        with archive.open(member) as f:
            record = ArrayReader(f, encoding="latin1").load()
        data = record["signal"]
        bvp = np.ravel(data["wrist"]["BVP"])
        acc = data["wrist"]["ACC"]
        ecg = np.ravel(data["chest"]["ECG"])
        fs = 700
        secs = 8
        # The energy envelope supports either electrode polarity. Quality rules
        # are identical in both cohorts. This is an ECG-derived research reference.
        y = signal.sosfiltfilt(
            signal.butter(3, [5, 23], btype="bandpass", fs=fs, output="sos"), ecg
        )
        env = signal.convolve(y * y, np.ones(45) / 45, mode="same", method="auto")
        freq = np.fft.rfftfreq(2048, 1 / 64)
        band = (freq >= 0.7) & (freq <= 3.3)
        wrist = signal.sosfiltfilt(
            signal.butter(3, [0.65, 3.5], btype="bandpass", fs=64, output="sos"), bvp
        )
        labels = record["activity"] if cohort == "DaLiA" else record["label"]
        labfreq = 4 if cohort == "DaLiA" else 700
        # Attribution under the released clock alignment; no hidden resynchronization
        # on the evaluation subjects' ECG.
        limit = min(len(wrist) // 64, len(acc) // 32, len(ecg) // fs, len(labels) // labfreq)
        for t in range(0, limit - secs + 1, secs):
            label = np.asarray(labels[t * labfreq : (t + secs) * labfreq]).ravel()
            if np.min(label) != np.max(label):
                continue
            a = int(label[0])
            if (cohort == "WESAD" and a not in [1, 2, 3, 4]) or (cohort == "DaLiA" and a == 0):
                continue
            v = env[t * fs : (t + secs) * fs]
            prominence = max(1e-12, 0.12 * (np.quantile(v, 0.98) - np.median(v)))
            peaks = signal.find_peaks(
                v, prominence=prominence, distance=int(0.29 * fs), height=np.median(v) + prominence
            )[0]
            rr = np.diff(peaks) / fs
            ok = (
                len(rr) >= 4
                and np.mean((rr >= 0.30) & (rr <= 1.5)) >= 0.9
                and np.median(abs(rr - np.median(rr))) / max(0.01, np.median(rr)) < 0.20
            )
            ref = round(60 / np.median(rr), 3) if ok else ""
            w = wrist[t * 64 : (t + secs) * 64]
            power = (abs(np.fft.rfft((w - np.mean(w)) * np.hanning(len(w)), 2048)) ** 2)[band]
            peakspec = int(np.argmax(power))
            energy = max(1e-16, np.sum(power))
            quality = np.sum(power[max(0, peakspec - 3) : peakspec + 4]) / energy
            ac = np.asarray(acc[t * 32 : (t + secs) * 32], dtype=float)
            motion = np.sqrt(np.mean((ac - np.mean(ac, axis=0)) ** 2)) / max(
                1e-6, np.median(np.linalg.norm(ac, axis=1))
            )
            yield (
                f"{cohort}/{subject}/{t}",
                cohort,
                subject,
                t,
                a,
                round(freq[band][peakspec] * 60, 3),
                ref,
                round(quality, 7),
                round(motion, 7),
            )


def rows(src):
    with zipfile.ZipFile(src.get("dalia.zip")) as container, tempfile.TemporaryFile() as local:
        with container.open("data.zip") as data:
            shutil.copyfileobj(data, local)
        local.seek(0)
        with zipfile.ZipFile(local) as inner:
            yield from segments(inner, "DaLiA")
    with zipfile.ZipFile(src.get("wesad.zip")) as wesad:
        yield from segments(wesad, "WESAD")
