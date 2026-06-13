#!/usr/bin/env python3
"""Wavetable FFT analysis for VerbalSynth — Phase 0.

Reads WAV banks from Wavetables/ (or build/ fallback), outputs
ml/config/wavetable_doc.json with per-frame FFT data.
Fields perceptual_summary and position_map are left empty for Claude to fill.

Usage:
    python ml/scripts/wavetable_doc.py
    python ml/scripts/wavetable_doc.py --wavetables-dir path/to/Wavetables
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
from scipy.io import wavfile

# Must match WavetableBank.h
FRAME_SIZE = 2048
NUM_FRAMES = 16
FUNDAMENTAL_HZ = 261.63  # C4 — base pitch for spectral centroid
NUM_HARMONICS = 20

BANK_NAMES = ["Basic", "Organ", "Acoustic", "Vocal", "Metallic", "Digital"]

# Cosine-distance thresholds for position_evolution (mean of adjacent frame pairs).
# These wavetables are linearly interpolated between 4 key frames, so adjacent
# distances are small (1/15 of the total span). Thresholds calibrated empirically
# against the 6 actual banks (Acoustic ≈ 1e-6, Metallic ≈ 1.5e-4).
EVOLUTION_LOW = 0.000008   # < this: barely changes (Acoustic)
EVOLUTION_HIGH = 0.000070  # > this: significant change (Vocal formants, Metallic)


def find_wavetable_dir(project_root: Path) -> Path | None:
    candidates = [
        project_root / "Wavetables",
        project_root / "build" / "VerbalSynth_artefacts" / "Debug" / "Wavetables",
        project_root / "build" / "VerbalSynth_artefacts" / "Release" / "Wavetables",
    ]
    for d in candidates:
        if d.is_dir() and any(d.glob("*.wav")):
            return d
    return None


def find_bank_wav(wavetable_dir: Path, bank_name: str) -> Path | None:
    """Match file ignoring leading numeric prefix: '1 Basic.wav' → 'Basic'."""
    for wav in sorted(wavetable_dir.glob("*.wav")):
        stem = wav.stem.lstrip("0123456789").strip()
        if stem.lower() == bank_name.lower():
            return wav
    return None


def read_frames(wav_path: Path) -> np.ndarray:
    """Return float32 array of shape (NUM_FRAMES, FRAME_SIZE)."""
    rate, raw = wavfile.read(wav_path)

    if raw.dtype == np.int16:
        data = raw.astype(np.float32) / 32768.0
    elif raw.dtype == np.int32:
        data = raw.astype(np.float32) / 2_147_483_648.0
    else:
        data = raw.astype(np.float32)

    if data.ndim > 1:
        data = data[:, 0]

    needed = NUM_FRAMES * FRAME_SIZE
    if len(data) < needed:
        raise ValueError(f"need {needed} samples, got {len(data)}")

    return data[:needed].reshape(NUM_FRAMES, FRAME_SIZE)


def analyze_frame(frame: np.ndarray, idx: int) -> dict:
    n = FRAME_SIZE
    rms = float(np.sqrt(np.mean(frame ** 2)))

    # One-sided FFT, normalized so a full-amplitude sine gives magnitude 1.0
    spectrum = np.fft.rfft(frame)
    mags = np.abs(spectrum) / (n / 2)
    mags[0] /= 2  # DC bin correction

    # First NUM_HARMONICS bins (1-based harmonic numbers)
    harmonics = [
        [k, round(float(mags[k]), 4) if k < len(mags) else 0.0]
        for k in range(1, NUM_HARMONICS + 1)
    ]

    # Spectral centroid: bin k corresponds to k * FUNDAMENTAL_HZ at C4
    non_dc = mags[1:]
    mag_sum = float(non_dc.sum())
    if mag_sum > 1e-12:
        bin_freqs = np.arange(1, len(mags)) * FUNDAMENTAL_HZ
        centroid_hz = float(np.dot(bin_freqs, non_dc) / mag_sum)
    else:
        centroid_hz = 0.0

    # Noise floor: power in bins 21+ vs total non-DC power (dB)
    harmonic_power = float(np.sum(mags[1 : NUM_HARMONICS + 1] ** 2))
    total_power = float(np.sum(non_dc ** 2))
    noise_power = max(total_power - harmonic_power, 0.0)

    if total_power > 1e-12:
        noise_floor_db = 20.0 * np.log10(np.sqrt(noise_power / total_power) + 1e-10)
    else:
        noise_floor_db = -80.0

    return {
        "frame_index": idx,
        "position": round(idx / (NUM_FRAMES - 1), 4),
        "spectral_centroid_hz": round(centroid_hz, 1),
        "harmonics": harmonics,
        "noise_floor_db": round(float(noise_floor_db), 1),
        "rms": round(rms, 4),
    }


def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return float(1.0 - np.dot(a, b) / (na * nb))


def compute_evolution(frames: np.ndarray) -> str:
    """Mean pairwise cosine distance between adjacent frames → low/medium/high."""
    dists = [cosine_distance(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    mean = float(np.mean(dists))
    if mean < EVOLUTION_LOW:
        return "low"
    elif mean < EVOLUTION_HIGH:
        return "medium"
    else:
        return "high"


def analyze_bank(name: str, wav_path: Path) -> dict:
    print(f"  {name:12s}  {wav_path.name}")
    frames = read_frames(wav_path)
    fft_data = [analyze_frame(frames[i], i) for i in range(NUM_FRAMES)]
    evolution = compute_evolution(frames)
    return {
        "name": name,
        "file": wav_path.name,
        "fft_data": fft_data,
        "position_evolution": evolution,
        "perceptual_summary": "",
        "position_map": {},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="VerbalSynth wavetable FFT analysis")
    parser.add_argument(
        "--wavetables-dir", type=Path, default=None,
        help="Directory containing wavetable WAV files",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]

    wt_dir = args.wavetables_dir or find_wavetable_dir(project_root)
    if wt_dir is None:
        print("ERROR: Wavetables directory not found.", file=sys.stderr)
        print("  Searched: Wavetables/, build/.../Wavetables/", file=sys.stderr)
        print("  Use --wavetables-dir to specify the path.", file=sys.stderr)
        sys.exit(1)

    print(f"Wavetables: {wt_dir}")

    out_dir = project_root / "ml" / "config"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "wavetable_doc.json"

    banks, missing = [], []
    for name in BANK_NAMES:
        wav = find_bank_wav(wt_dir, name)
        if wav is None:
            print(f"  WARNING: {name} — WAV not found", file=sys.stderr)
            missing.append(name)
            continue
        try:
            banks.append(analyze_bank(name, wav))
        except Exception as exc:
            print(f"  ERROR {name}: {exc}", file=sys.stderr)
            missing.append(name)

    doc = {
        "version": "1.0",
        "generated_at": date.today().isoformat(),
        "frame_size": FRAME_SIZE,
        "num_frames": NUM_FRAMES,
        "fundamental_hz": FUNDAMENTAL_HZ,
        "banks": banks,
    }

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    print(f"\nOutput: {out_path}")
    print(
        f"Banks:  {len(banks)}/{len(BANK_NAMES)} processed"
        + (f" (missing: {', '.join(missing)})" if missing else "")
    )


if __name__ == "__main__":
    main()
