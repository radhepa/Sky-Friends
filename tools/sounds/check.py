#!/usr/bin/env python3
"""Checks the synthesized sounds and draws tools/sounds/out/spectro.png.

    python tools/sounds/check.py

Decodes every OGG with ffmpeg and prints duration, peak, RMS, spectral centroid and a pitch estimate
(YIN, 5th-95th percentile of voiced frames). Fails if a file is not mono 44.1 kHz, clips, carries DC,
starts/ends with a click, is missing from sounds.json (or vice versa), or the folder passes 6 MB.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import signal
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from synth import ASSETS, SOUND_DIR, SR, find_ffmpeg  # noqa: E402

OUT = HERE / "out"


def decode(ffmpeg, ogg, wav):
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(ogg),
                    "-c:a", "pcm_f32le", str(wav)], check=True)
    sr, x = wavfile.read(wav)
    return sr, x.astype(np.float64)


def yin_f0(x, fmin=45.0, fmax=1100.0, W=1024, hop=256, thr=0.15):
    """Per-frame pitch (Hz) or nan; frames 10%-loudness-gated."""
    maxlag, minlag = int(SR / fmin), int(SR / fmax)
    starts = range(0, max(0, len(x) - W - maxlag), hop)
    rms = np.array([np.sqrt(np.mean(x[s:s + W] ** 2)) for s in starts]) if len(starts) else np.array([])
    gate = 0.1 * rms.max() if len(rms) else 0.0
    out, times = [], []
    lags = np.arange(maxlag + 1)
    for i, s in enumerate(starts):
        times.append((s + W / 2) / SR)
        if rms[i] < gate:
            out.append(np.nan)
            continue
        seg = x[s:s + W + maxlag]
        a = seg[:W]
        r = signal.fftconvolve(seg, a[::-1], mode="valid")
        cs = np.concatenate([[0.0], np.cumsum(seg ** 2)])
        d = cs[W] + (cs[W + lags] - cs[lags]) - 2 * r
        dd = d[1:]
        cm = dd * np.arange(1, maxlag + 1) / np.maximum(np.cumsum(dd), 1e-12)
        cand = np.where(cm[minlag - 1:] < thr)[0]
        if not len(cand):
            out.append(np.nan)
            continue
        k = cand[0] + minlag - 1
        while k + 1 < len(cm) and cm[k + 1] < cm[k]:
            k += 1
        out.append(SR / (k + 1))
    return np.array(times), np.array(out)


MAGMA = [(0.0, (0, 0, 4)), (0.25, (59, 15, 112)), (0.5, (140, 41, 129)), (0.75, (222, 73, 104)),
         (1.0, (252, 253, 191))]


def colormap(v):
    v = np.clip(v, 0, 1)
    xs = [s for s, _ in MAGMA]
    return np.stack([np.interp(v, xs, [c[i] for _, c in MAGMA]) for i in range(3)], axis=-1).astype(np.uint8)


def tile(x, title, w=420, h=150, fmin=40.0, fmax=12000.0):
    nfft, hop = 2048, 256
    f, tt, Z = signal.stft(x, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    S = 20 * np.log10(np.abs(Z) + 1e-9)
    S = np.clip((S - S.max() + 80) / 80, 0, 1)
    fr = fmin * (fmax / fmin) ** (1 - (np.arange(h) + 0.5) / h)
    bins = fr / (SR / nfft)
    cols = np.round(np.linspace(0, S.shape[1] - 1, w)).astype(int)
    img = np.stack([np.interp(bins, np.arange(S.shape[0]), S[:, j]) for j in cols], axis=1)
    rgb = colormap(img)
    pad_l, pad_t = 34, 18
    canvas = Image.new("RGB", (w + pad_l + 6, h + pad_t + 4), (20, 20, 24))
    canvas.paste(Image.fromarray(rgb), (pad_l, pad_t))
    dr = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    dur = len(x) / SR

    def yof(fq):
        return pad_t + h * (1 - np.log(fq / fmin) / np.log(fmax / fmin))

    for fq, lab in ((100, "100"), (200, "200"), (500, "500"), (1000, "1k"), (2000, "2k"), (5000, "5k"),
                    (10000, "10k")):
        y = yof(fq)
        dr.line([(pad_l, y), (pad_l + w, y)], fill=(90, 90, 110))
        dr.text((2, y - 6), lab, fill=(200, 200, 210), font=font)
    times, f0 = yin_f0(x)
    for tm, fq in zip(times, f0):
        if np.isfinite(fq) and fmin < fq < fmax:
            px, py = pad_l + tm / dur * w, yof(fq)
            dr.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(80, 255, 255))
    dr.text((pad_l, 2), title, fill=(235, 235, 240), font=font)
    return canvas


def main():
    ffmpeg = find_ffmpeg()
    sj = json.loads((ASSETS / "sounds.json").read_text(encoding="utf-8"))
    lang = json.loads((HERE / "lang.json").read_text(encoding="utf-8"))
    problems = []
    referenced = set()
    for event, body in sj.items():
        if lang.get(body.get("subtitle")) is None:
            problems.append(f"{event}: subtitle {body.get('subtitle')} missing from lang.json")
        for s in body["sounds"]:
            name = s["name"] if isinstance(s, dict) else s
            rel = name.split(":", 1)[1]
            referenced.add(rel)
            if not (SOUND_DIR / f"{rel}.ogg").exists():
                problems.append(f"{event}: {rel}.ogg missing")
    files = sorted(SOUND_DIR.rglob("*.ogg"))
    for p in files:
        rel = p.relative_to(SOUND_DIR).with_suffix("").as_posix()
        if rel not in referenced:
            problems.append(f"{rel}.ogg not in sounds.json")

    OUT.mkdir(parents=True, exist_ok=True)
    tiles = []
    print(f"{'file':24s} {'dur':>5s} {'peak':>6s} {'rms':>6s} {'centr':>6s}  f0 (5-95%)")
    with tempfile.TemporaryDirectory() as tmp:
        decoded = {}
        for p in files:
            rel = p.relative_to(SOUND_DIR).with_suffix("").as_posix()
            sr, x = decode(ffmpeg, p, Path(tmp) / "x.wav")
            if x.ndim != 1:
                problems.append(f"{rel}: {x.shape[1]} channels, not mono")
                x = x.mean(axis=1)
            if sr != SR:
                problems.append(f"{rel}: sample rate {sr}")
            peak = np.abs(x).max()
            rms = np.sqrt(np.mean(x ** 2))
            spec = np.abs(np.fft.rfft(x))
            centroid = np.sum(np.fft.rfftfreq(len(x), 1 / SR) * spec) / np.sum(spec)
            _, f0 = yin_f0(x)
            f0 = f0[np.isfinite(f0)]
            f0s = f"{np.percentile(f0, 5):4.0f}-{np.percentile(f0, 95):4.0f} Hz" if len(f0) > 3 else "-"
            print(f"{rel:24s} {len(x) / SR:5.2f} {20 * np.log10(peak):6.1f} {20 * np.log10(rms):6.1f} "
                  f"{centroid:6.0f}  {f0s}")
            if peak >= 0.999:
                problems.append(f"{rel}: clips (peak {peak:.4f})")
            if not -4.5 < 20 * np.log10(peak) < -1.5:
                problems.append(f"{rel}: peak {20 * np.log10(peak):.1f} dBFS, expected about -3")
            if abs(x.mean()) > 2e-3:
                problems.append(f"{rel}: DC offset {x.mean():.4f}")
            edge = int(0.001 * SR)
            if np.abs(x[:edge]).max() > 0.03 or np.abs(x[-edge:]).max() > 0.03:
                problems.append(f"{rel}: not faded at an end")
            decoded[rel] = x
        for event, body in sj.items():
            s = body["sounds"][0]
            rel = (s["name"] if isinstance(s, dict) else s).split(":", 1)[1]
            tiles.append(tile(decoded[rel], f"{event}  ({rel}, {len(decoded[rel]) / SR:.2f}s)"))

    cols = 3
    tw, th = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (10, 10, 12))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
    sheet.save(OUT / "spectro.png")

    total = sum(p.stat().st_size for p in files)
    print(f"\n{len(sj)} events, {len(files)} files, {total / 1e6:.2f} MB -> spectrograms in {OUT / 'spectro.png'}")
    if total > 6e6:
        problems.append(f"sound folder is {total / 1e6:.2f} MB (> 6 MB)")
    if problems:
        print("\nPROBLEMS:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
