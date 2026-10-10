#!/usr/bin/env python3
"""Sky Friends sound synthesizer.

Every sound in the mod is made here from code: no samples, no downloads. The script is deterministic
(each sound seeds its own random generator from its name), so re-running it gives the same files.

    python tools/sounds/synth.py            # everything
    python tools/sounds/synth.py whale      # only sounds whose path contains "whale" (json files still rewritten)

Writes
    src/main/resources/assets/skyfriends/sounds/<folder>/<name>.ogg   (mono, 44.1 kHz, Vorbis q5)
    src/main/resources/assets/skyfriends/sounds.json
    tools/sounds/lang.json                                           (subtitle keys -> English)

Needs numpy, scipy and ffmpeg with libvorbis (found via $FFMPEG, the WinGet path below, or PATH).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.interpolate import CubicSpline
from scipy.io import wavfile

SR = 44100
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = ROOT / "src" / "main" / "resources" / "assets" / "skyfriends"
SOUND_DIR = ASSETS / "sounds"
FFMPEG_WINGET = (r"C:\Users\minal\AppData\Local\Microsoft\WinGet\Packages"
                 r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")

# D major pentatonic (D E F# A B) everywhere, so harps, flutes, chimes and voices agree when they overlap.
PENTA_PCS = (2, 4, 6, 9, 11)


def find_ffmpeg():
    for c in (os.environ.get("FFMPEG"), FFMPEG_WINGET, shutil.which("ffmpeg")):
        if c and Path(c).exists():
            return c
    sys.exit("ffmpeg not found: set FFMPEG to its path")


def rng_for(name):
    return np.random.default_rng(zlib.crc32(name.encode("utf-8")))


# ------------------------------------------------------------------------------------------------
# small DSP toolkit
# ------------------------------------------------------------------------------------------------

def tvec(n):
    return np.arange(n) / SR


def midi_hz(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def glide_track(t, times, values, glide):
    """Step from value to value at each time (the first time is ignored), each step a smooth glide."""
    out = np.full(t.shape, float(values[0]))
    for i in range(1, len(values)):
        out += (values[i] - values[i - 1]) * smoothstep((t - times[i]) / glide + 0.5)
    return out


def keys_track(t, keys):
    """Eased piecewise curve through (time, value) keys; flat before the first and after the last."""
    ts = [k[0] for k in keys]
    vs = [float(k[1]) for k in keys]
    out = np.full(t.shape, vs[0])
    for i in range(len(ts) - 1):
        u = smoothstep((t - ts[i]) / max(ts[i + 1] - ts[i], 1e-6))
        out = np.where(t >= ts[i], vs[i] + (vs[i + 1] - vs[i]) * u, out)
    return out


def filt(x, kind, fc, order=2):
    sos = signal.butter(order, fc, btype=kind, fs=SR, output="sos")
    return signal.sosfiltfilt(sos, x)


def slow_noise(n, rng, hz):
    """Smooth random wander (about unit size) with features around `hz`."""
    m = max(4, int(n / SR * hz * 2) + 3)
    return CubicSpline(np.linspace(0, n - 1, m), rng.standard_normal(m))(np.arange(n))


def fast_noise(n, rng, hz):
    y = filt(rng.standard_normal(n), "lowpass", hz)
    return y / (y.std() + 1e-12)


def shaped_noise(n, rng, gain_fn, nfft=1024, hop=256):
    """White noise given a time-varying spectrum. gain_fn(freqs[F,1], sample_index[T]) -> gains[F,T]."""
    noise = rng.standard_normal(n + nfft)
    f, tt, Z = signal.stft(noise, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    idx = np.clip(np.round(tt * SR).astype(int), 0, n - 1)
    G = gain_fn(f[:, None], idx)
    _, y = signal.istft(Z * G, fs=SR, nperseg=nfft, noverlap=nfft - hop)
    y = y[:n]
    return y / (np.sqrt(np.mean(y ** 2)) + 1e-12)


def reson(f, F, B):
    """Magnitude of a two-pole resonance at F with bandwidth B, scaled to 1 at its peak."""
    return B * F / np.sqrt((F * F - f * f) ** 2 + (B * f) ** 2 + 1e-9)


def reverb(x, rng, rt=0.7, wet=0.18, pre=0.012, bright=0.5, damp=6500.0, hp=120.0, tail=0.0):
    """Synthetic room: decaying noise impulse response (highs die faster), convolved and mixed in."""
    m = int(SR * rt * 1.1)
    t = tvec(m)
    nz = rng.standard_normal(m)
    lo = filt(nz, "lowpass", 1500.0)
    ir = lo * np.exp(-6.91 * t / rt) + bright * (nz - lo) * np.exp(-6.91 * t / (rt * 0.45))
    ir *= 1.0 - np.exp(-t / 0.006)
    ir = np.concatenate([np.zeros(int(pre * SR)), ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    y = np.concatenate([x, np.zeros(int(tail * SR))])
    w = signal.fftconvolve(y, ir)[: len(y)]
    w = filt(filt(w, "highpass", hp), "lowpass", damp)
    return y + wet * w


def finish(x, length=None, fade_in=0.004, fade_out=0.05, hp=30.0, peak_db=-3.0):
    """Trim/pad, strip DC and rumble, fade both ends, normalise the peak."""
    x = np.asarray(x, dtype=float)
    if length is not None:
        n = int(round(length * SR))
        x = x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])
    x = filt(x, "highpass", hp)
    x = x - x.mean()
    ni, no = int(fade_in * SR), int(fade_out * SR)
    if ni:
        x[:ni] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ni))
    if no:
        x[-no:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, no))
    return x * (10 ** (peak_db / 20) / (np.abs(x).max() + 1e-12))


# ------------------------------------------------------------------------------------------------
# the Cirri voice: harmonic source + morphing formants + breath, sung wordlessly
# ------------------------------------------------------------------------------------------------

FORMANTS = {  # F1..F4 in Hz (Peterson & Barney style values; "mm" is a closed-mouth hum)
    "male": {
        "oo": (300, 870, 2240, 3300), "oh": (570, 840, 2410, 3300), "aa": (730, 1090, 2440, 3300),
        "ee": (270, 2290, 3010, 3500), "eh": (530, 1840, 2480, 3400), "uh": (640, 1190, 2390, 3300),
        "mm": (250, 1000, 2200, 3200)},
    "female": {
        "oo": (370, 950, 2670, 3900), "oh": (590, 920, 2710, 3900), "aa": (850, 1220, 2810, 3950),
        "ee": (310, 2790, 3310, 4200), "eh": (600, 2330, 2990, 4000), "uh": (760, 1400, 2780, 3900),
        "mm": (300, 1150, 2500, 3600)},
    "child": {
        "oo": (430, 1170, 3260, 4300), "oh": (680, 1060, 3180, 4300), "aa": (1030, 1370, 3170, 4300),
        "ee": (370, 3200, 3730, 4600), "eh": (690, 2610, 3570, 4500), "uh": (850, 1590, 3360, 4400),
        "mm": (340, 1300, 2800, 4000)},
}
FORMANT_AMPS = {
    "oo": (1, .32, .07, .035), "oh": (1, .55, .10, .045), "aa": (1, .72, .20, .09),
    "ee": (1, .20, .26, .11), "eh": (1, .42, .20, .09), "uh": (1, .55, .15, .07),
    "mm": (1, .06, .025, .012),
}
BASE_BW = (80.0, 95.0, 140.0, 220.0)
BW_MUL = {"mm": (0.9, 2.2, 2.2, 2.0)}

VOICE = {
    # slope: source roll-off (k^-slope); lp: where harmonics fade; bw: formant bandwidth scale
    "female": dict(slope=1.40, lp=7000.0, floor=0.035, bw=1.10, breath=0.10, vib_rate=5.4,
                   vib_depth=0.30, drift=0.07, jit=0.045, shim=0.05),
    "male": dict(slope=1.20, lp=5000.0, floor=0.035, bw=1.00, breath=0.07, vib_rate=5.1,
                 vib_depth=0.26, drift=0.07, jit=0.05, shim=0.05),
    "child": dict(slope=1.45, lp=8000.0, floor=0.035, bw=1.25, breath=0.09, vib_rate=5.9,
                  vib_depth=0.30, drift=0.08, jit=0.045, shim=0.05),
}


def vowel_tracks(t, keys, vt, glide):
    times = [k[0] for k in keys]
    names = [k[1] for k in keys]
    F = np.stack([glide_track(t, times, [FORMANTS[vt][v][i] for v in names], glide) for i in range(4)])
    B = np.stack([glide_track(t, times, [BASE_BW[i] * BW_MUL.get(v, (1, 1, 1, 1))[i] for v in names], glide)
                  for i in range(4)])
    A = np.stack([glide_track(t, times, [FORMANT_AMPS[v][i] for v in names], glide) for i in range(4)])
    return F, B, A


def render_harmonics(f0, amp, F, B, A, slope, rng, floor=0.035, lp=7000.0):
    """Band-limited additive source: harmonic k gets k^-slope times the formant envelope at k*f0."""
    n = len(f0)
    phase = 2 * np.pi * np.cumsum(f0) / SR
    kmax = int(min(2.2 * lp, 0.45 * SR) / max(f0.min(), 20.0)) + 1
    phis = rng.uniform(0, 2 * np.pi, kmax + 1)
    y = np.zeros(n)
    for k in range(1, kmax + 1):
        fk = k * f0
        mask = 1.0 / (1.0 + (fk / lp) ** 4)
        mask[fk > 0.45 * SR] = 0.0
        env = floor + sum(A[i] * reson(fk, F[i], B[i]) for i in range(F.shape[0]))
        y += np.exp(-slope * np.log(k)) * env * mask * np.sin(k * phase + phis[k])
    return y * amp


def render_voice(rng, vt, t, midi, amp, vkeys, breath, *, slope_add=0.0, vib=None, jit=1.0,
                 vowel_glide=0.1, creak=None):
    """midi/amp/breath are per-sample tracks; breath is relative to the voiced level."""
    P = VOICE[vt]
    n = len(t)
    m = midi + P["drift"] * slow_noise(n, rng, 3.0) + P["jit"] * jit * fast_noise(n, rng, 35.0)
    if vib is not None:
        m = m + vib
    f0 = 440.0 * 2.0 ** ((m - 69.0) / 12.0)
    F, B, A = vowel_tracks(t, vkeys, vt, vowel_glide)
    F = F * (1.0 + 0.012 * np.stack([slow_noise(n, rng, 2.0) for _ in range(4)]))
    F[0] = np.maximum(F[0], f0 * 1.05)  # singers lift F1 onto high notes
    B = B * P["bw"]
    env_norm = amp / (amp.max() + 1e-9)
    a = amp * (1.0 + P["shim"] * fast_noise(n, rng, 25.0))
    slope = P["slope"] + slope_add + 0.8 * (1.0 - env_norm)  # softer = darker
    voiced = render_harmonics(f0, a, F, B, A, slope, rng, P["floor"], P["lp"])
    phase = 2 * np.pi * np.cumsum(f0) / SR
    if creak is not None:  # period-doubling roughness
        voiced *= 1.0 - creak * (0.5 + 0.5 * np.cos(0.5 * phase))
    active = amp > 0.5 * amp.max()
    ref = np.sqrt(np.mean(voiced[active] ** 2)) if active.any() else 1.0

    def gain(f, idx):
        e = 0.02 + sum(A[i][idx] * reson(f, F[i][idx], 1.8 * B[i][idx]) for i in range(4))
        return e * (f / (f + 700.0)) / (1.0 + (f / 6500.0) ** 4)

    nz = shaped_noise(n, rng, gain) * (1.0 + 0.3 * env_norm * np.cos(phase))
    return voiced + ref * breath * nz


def N(m, d, v, a=1.0, art=False):
    return dict(m=m, d=d, v=v, a=a, art=art)


def sing(seed, vt, notes, *, lead=0.05, tail=0.3, glide=0.075, vib_scale=1.0, slope_add=0.0,
         breath_scale=1.0, h=0.25, art=0.5, scoop=0.6, end_fall=0.3, end_rise=0.0, att=0.07,
         rel=0.18, verb=(0.65, 0.16)):
    """A wordless sung phrase: legato pentatonic notes, morphing vowels, delayed vibrato, breath."""
    rng = rng_for(seed)
    P = VOICE[vt]
    durs = np.array([nt["d"] for nt in notes])
    starts = lead + np.concatenate([[0.0], np.cumsum(durs)[:-1]])
    end = lead + durs.sum()
    n = int((end + 0.3) * SR)
    t = tvec(n)

    midi = glide_track(t, starts, [nt["m"] for nt in notes], glide)
    midi -= scoop * (1.0 - smoothstep((t - starts[0]) / 0.12))
    midi -= end_fall * smoothstep((t - (end - 0.3)) / 0.4)
    if end_rise:
        midi += end_rise * smoothstep((t - (starts[-1] + 0.35 * durs[-1])) / (0.5 * durs[-1]))

    vd = np.zeros(n)
    for s, d in zip(starts, durs):
        vd = np.maximum(vd, smoothstep((t - s - 0.16) / 0.22) * (1.0 - smoothstep((t - (s + d) + 0.02) / 0.06)))
    rate = P["vib_rate"] * (1.0 + 0.05 * slow_noise(n, rng, 1.0))
    vib_unit = np.sin(2 * np.pi * np.cumsum(rate) / SR + rng.uniform(0, 2 * np.pi))
    vib = P["vib_depth"] * vib_scale * vd * vib_unit

    amp = glide_track(t, starts, [nt["a"] for nt in notes], 0.06)
    env = smoothstep((t - starts[0] + 0.01) / att) * (1.0 - smoothstep((t - end + rel) / rel))
    hb = h * np.exp(-((t - starts[0] + 0.015) / 0.03) ** 2)
    for nt, s in zip(notes, starts):
        if nt["art"]:
            dip = np.exp(-((t - s + 0.008) / 0.03) ** 2)
            amp *= 1.0 - art * dip
            hb += 0.6 * h * dip
    amp *= 1.0 + 0.035 * vib_unit * vd
    a = amp * env
    breath = (P["breath"] * breath_scale * (0.4 + 0.6 * env) * smoothstep((t - starts[0] + 0.06) / 0.06)
              * (1.0 - smoothstep((t - end) / 0.2)) + hb)

    vkeys = []
    for nt, s, d in zip(notes, starts, durs):
        parts = nt["v"].split(">")
        vkeys.append((s, parts[0]))
        if len(parts) > 1:
            vkeys.append((s + 0.45 * d, parts[1]))
    vkeys[0] = (0.0, vkeys[0][1])

    x = render_voice(rng, vt, t, midi, a, vkeys, breath, slope_add=slope_add, vib=vib)
    x = reverb(x, rng, rt=verb[0], wet=verb[1], tail=max(0.0, end + tail - n / SR))
    return finish(x, length=end + tail, fade_out=0.08)


def hum(seed, vt, notes):
    if vt == "child":  # bouncier and lighter
        return sing(seed, vt, notes, glide=0.05, art=0.7, vib_scale=0.8, tail=0.25, slope_add=0.05)
    return sing(seed, vt, notes, slope_add=0.1)


def greet(seed, vt, notes):
    return sing(seed, vt, notes, h=0.5, art=0.6, slope_add=-0.25, vib_scale=0.4, end_rise=0.7,
                scoop=0.4, end_fall=0.0, att=0.035, rel=0.1, glide=0.05, tail=0.25)


TOP = {"female": 71, "male": 57, "child": 76}


def hurt(seed, vt, variant):
    """Short pained 'ah!' / gasp-'uh!' / 'eh-h', human and unforced."""
    rng = rng_for(seed)
    top = TOP[vt]
    creak = None
    if variant == 1:
        L = 0.30
        t = tvec(int((L + 0.1) * SR))
        midi = keys_track(t, [(0.0, top + 0.3), (0.035, top + 1.0), (0.24, top - 5.0)])
        amp = keys_track(t, [(0.006, 0), (0.02, 1), (0.08, 0.8), (0.25, 0)])
        vk = [(0.0, "aa"), (0.13, "uh")]
        br = keys_track(t, [(0.0, 0), (0.008, 0.6), (0.03, 0.18), (0.16, 0.25), (0.25, 0.4), (0.3, 0)])
    elif variant == 2:  # quick inhaled gasp, then the cry
        L = 0.38
        t = tvec(int((L + 0.1) * SR))
        midi = keys_track(t, [(0.10, top), (0.14, top + 0.5), (0.32, top - 6.0)])
        amp = keys_track(t, [(0.105, 0), (0.125, 1), (0.2, 0.7), (0.33, 0)])
        vk = [(0.0, "ee"), (0.1, "uh")]
        br = keys_track(t, [(0.0, 0), (0.05, 0.55), (0.09, 0.6), (0.112, 0.12), (0.2, 0.2), (0.32, 0.35),
                            (0.37, 0)])
    else:  # clipped "eh-h" with a little catch at the end
        L = 0.26
        t = tvec(int((L + 0.1) * SR))
        midi = keys_track(t, [(0.0, top - 1.0), (0.02, top), (0.2, top - 4.0)])
        amp = keys_track(t, [(0.004, 0), (0.014, 1), (0.06, 0.9), (0.2, 0)])
        vk = [(0.0, "eh"), (0.08, "uh")]
        br = keys_track(t, [(0.0, 0), (0.006, 0.35), (0.02, 0.15), (0.17, 0.3), (0.25, 0)])
        creak = 0.35 * keys_track(t, [(0.09, 0), (0.15, 1), (0.2, 1)])
    x = render_voice(rng, vt, t, midi, amp, vk, br, slope_add=-0.35, jit=2.5, vowel_glide=0.06, creak=creak)
    x = reverb(x, rng, rt=0.5, wet=0.12)
    return finish(x, length=L, fade_out=0.04)


def death(seed, vt):
    """A falling sigh: 'aah-oh-uh' sliding down most of an octave, voice dissolving into breath."""
    rng = rng_for(seed)
    top = {"female": 69, "male": 55, "child": 74}[vt]
    L = 1.1
    t = tvec(int((L + 0.1) * SR))
    midi = keys_track(t, [(0.0, top), (0.07, top + 0.7), (0.9, top - 9.0)])
    n = len(t)
    rate = 6.3 * (1.0 + 0.15 * slow_noise(n, rng, 2.0))
    trem = 0.22 * smoothstep((t - 0.15) / 0.3) * np.sin(2 * np.pi * np.cumsum(rate) / SR)
    amp = keys_track(t, [(0.015, 0), (0.07, 1), (0.3, 0.8), (0.88, 0)])
    vk = [(0.0, "aa"), (0.35, "oh"), (0.7, "uh")]
    br = keys_track(t, [(0.0, 0), (0.03, 0.35), (0.09, 0.15), (0.5, 0.25), (0.85, 0.45), (1.05, 0)])
    slope_add = keys_track(t, [(0.0, -0.1), (0.9, 0.7)])
    x = render_voice(rng, vt, t, midi, amp, vk, br, slope_add=slope_add, vib=trem, jit=1.5)
    x = reverb(x, rng, rt=0.8, wet=0.2)
    return finish(x, length=L, fade_out=0.1)


SLEEP = [
    # voice, length, inhale end, exhale start, hum pitch keys, hum amplitude keys
    dict(vt="female", L=1.45, inh=0.55, exh=0.60,
         midi=[(0.6, 57), (1.35, 55.6)], amp=[(0.62, 0), (0.8, 0.55), (1.05, 0.5), (1.36, 0)]),
    dict(vt="male", L=1.50, inh=0.45, exh=0.52,
         midi=[(0.55, 52), (0.85, 52), (0.95, 50), (1.4, 49.6)],
         amp=[(0.56, 0), (0.7, 0.6), (0.86, 0.45), (0.92, 0.3), (1.0, 0.55), (1.4, 0)]),
    dict(vt="female", L=1.60, inh=0.62, exh=0.68,
         midi=[(0.7, 54), (1.5, 52.6)], amp=[(0.72, 0), (0.95, 0.5), (1.5, 0)]),
]


def sleep(seed, variant):
    """Slow breath in through the nose, then out with a faint, sleepy 'mm'."""
    c = SLEEP[variant - 1]
    rng = rng_for(seed)
    L, inh, exh = c["L"], c["inh"], c["exh"]
    t = tvec(int((L + 0.1) * SR))
    midi = keys_track(t, c["midi"])
    amp = keys_track(t, c["amp"])
    br = keys_track(t, [(0.0, 0), (inh * 0.7, 1.4), (inh, 1.0), (inh + 0.06, 0.15), (exh, 0.2),
                        (exh + 0.15, 1.1), (L - 0.2, 0.7), (L - 0.02, 0)])
    vk = [(0.0, "oo"), (exh, "mm")]
    x = render_voice(rng, c["vt"], t, midi, amp, vk, br, slope_add=0.4, jit=0.8)
    x = filt(x, "lowpass", 2800.0)  # nose breathing: soft and dark
    x = reverb(x, rng, rt=0.6, wet=0.12)
    return finish(x, length=L, fade_in=0.01, fade_out=0.1)


# ------------------------------------------------------------------------------------------------
# instruments
# ------------------------------------------------------------------------------------------------

def pluck(f, n, rng, vel):
    """Modal harp string: slightly stretched partials, pluck-position comb, highs dying first."""
    t = tvec(n)
    p = 0.12 + 0.05 * rng.random()
    tau1 = float(np.clip(0.9 * (330.0 / f) ** 0.45, 0.3, 1.6))
    y = np.zeros(n)
    for k in range(1, 40):
        fk = f * k * np.sqrt(1.0 + 1.2e-4 * k * k)
        if fk > 11000:
            break
        ak = abs(np.sin(np.pi * k * p)) / k ** (1.3 - 0.3 * vel)
        tauk = tau1 / (1.0 + 0.3 * (k - 1) + (fk / 2500.0) ** 2)
        y += ak * np.exp(-t / tauk) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 2 * np.pi))
    y *= 1.0 - np.exp(-t / 0.0015)
    nb = filt(rng.standard_normal(n), "highpass", 2500.0) * np.exp(-t / 0.004) * (1.0 - np.exp(-t / 0.0005))
    return vel * (y + 0.06 * nb)


def harp(seed, events, L):
    rng = rng_for(seed)
    n = int(L * SR)
    y = np.zeros(n)
    for tm, m, vel in events:
        tm = 0.01 + max(0.0, tm + (rng.normal(0, 0.006) if tm > 0 else 0.0))
        i0 = int(tm * SR)
        y[i0:] += pluck(float(midi_hz(m)), n - i0, rng, vel * rng.uniform(0.9, 1.05))
    y = filt(y, "lowpass", 9000.0)
    y = reverb(y, rng, rt=1.8, wet=0.28, pre=0.02, bright=0.6)
    return finish(y, length=L, fade_in=0.002, fade_out=0.5)


def arp(t0, notes, step, v0=0.7, v1=0.85):
    vs = np.linspace(v0, v1, len(notes))
    return [(t0 + i * step, m, float(vs[i])) for i, m in enumerate(notes)]


HARP = [
    (arp(0.0, [62, 66, 69, 74, 78, 81], 0.11, 0.6, 0.85), 2.4),
    (arp(0.0, [86, 83, 81, 78, 74, 71, 69], 0.09, 0.85, 0.65), 2.2),
    ([(0.0, 69, .7), (0.14, 74, .75), (0.28, 76, .8), (0.42, 81, .85), (0.6, 76, .7), (0.78, 74, .7),
      (1.0, 62, .75), (1.0, 69, .6)], 2.7),
    (arp(0.0, [50, 57, 62, 66, 69, 74], 0.035, 0.7, 0.8) + [(0.55, 78, .8), (0.8, 76, .7)], 2.5),
    ([(0.0, 74, .7), (0.18, 76, .75), (0.36, 78, .8), (0.6, 81, .85)], 1.7),
    (arp(0.0, [62, 64, 66, 69, 71, 74, 76, 78, 81, 83, 86], 0.05, 0.55, 0.8) + [(0.62, 50, .7)], 2.8),
]


def flute(seed, notes, lead=0.04, tail=0.35):
    """Breathy wooden flute: few harmonics, pitched breath halo, tongued chiffs, delayed vibrato."""
    rng = rng_for(seed)
    durs = np.array([nt[1] for nt in notes])
    starts = lead + np.concatenate([[0.0], np.cumsum(durs)[:-1]])
    end = lead + durs.sum()
    n = int((end + tail) * SR)
    t = tvec(n)
    tongued = [s for s, nt in zip(starts, notes) if nt[2]]

    midi = glide_track(t, starts, [nt[0] for nt in notes], 0.03)
    onset = np.zeros(n)
    chiff = np.zeros(n)
    dips = np.ones(n)
    for i, s in enumerate(tongued):
        midi -= 0.3 * smoothstep((t - s + 0.01) / 0.01) * (1.0 - smoothstep((t - s) / 0.05))
        rise = smoothstep((t - s + 0.008) / 0.008)
        onset += rise * np.exp(-np.maximum(t - s, 0.0) / 0.035)
        chiff += smoothstep((t - s + 0.006) / 0.006) * np.exp(-np.maximum(t - s, 0.0) / 0.02)
        if s > starts[0]:
            dips *= 1.0 - 0.85 * np.exp(-((t - s + 0.012) / 0.018) ** 2)
    vd = np.zeros(n)
    for s, d in zip(starts, durs):
        vd = np.maximum(vd, smoothstep((t - s - 0.2) / 0.25) * (1.0 - smoothstep((t - (s + d) + 0.02) / 0.05)))
    vib_unit = np.sin(2 * np.pi * np.cumsum(5.0 * (1.0 + 0.04 * slow_noise(n, rng, 1.0))) / SR)
    m = midi + 0.14 * vd * vib_unit + 0.03 * slow_noise(n, rng, 3.0) + 0.015 * fast_noise(n, rng, 30.0)
    f0 = 440.0 * 2.0 ** ((m - 69.0) / 12.0)

    amp = glide_track(t, starts, [nt[3] for nt in notes], 0.03) * dips
    amp *= smoothstep((t - starts[0] + 0.005) / 0.045) * (1.0 - smoothstep((t - end + 0.14) / 0.14))
    amp *= (1.0 + 0.05 * vd * vib_unit) * (1.0 + 0.03 * fast_noise(n, rng, 12.0))

    phase = 2 * np.pi * np.cumsum(f0) / SR
    H = (1.0, 0.30, 0.13, 0.065, 0.03, 0.015)
    y = np.zeros(n)
    for k, h in enumerate(H, start=1):
        w = h * np.maximum(amp, 0.0) ** (0.25 * (k - 1))
        if k == 2:
            w = w * (1.0 + 1.5 * onset)
        elif k == 3:
            w = w * (1.0 + 0.6 * onset)
        y += w * np.sin(k * phase + rng.uniform(0, 2 * np.pi))
    y *= amp
    ref = np.sqrt(np.mean(y[amp > 0.5 * amp.max()] ** 2))

    def halo(f, idx):
        g = sum(gk * np.exp(-0.5 * ((f - k * f0[idx]) / (0.035 * k * f0[idx])) ** 2)
                for k, gk in ((1, 1.0), (2, 0.5), (3, 0.25)))
        return g + 0.10 * (f / (f + 1500.0)) / (1.0 + (f / 6000.0) ** 2)

    air = shaped_noise(n, rng, halo)
    ch = filt(rng.standard_normal(n), "bandpass", (1500.0, 6000.0))
    ch /= ch.std()
    y += ref * (0.12 * amp * air + 0.25 * chiff * ch)
    y = reverb(y, rng, rt=1.3, wet=0.22, pre=0.015)
    return finish(y, length=end + tail, fade_out=0.12)


FLUTE = [  # (midi, seconds, tongued, level)
    [(74, .22, 1, .85), (76, .22, 1, .9), (78, .45, 1, 1), (76, .16, 0, .9), (74, .55, 1, .85)],
    [(81, .35, 1, .95), (83, .05, 0, .9), (81, .12, 0, .95), (78, .15, 0, .9), (76, .15, 0, .85), (74, .55, 1, .85)],
    [(69, .17, 1, .8), (74, .17, 1, .85), (76, .17, 1, .9), (81, .70, 1, 1)],
    [(78, .28, 1, .9), (81, .12, 0, .95), (78, .12, 0, .9), (76, .28, 1, .9), (74, .18, 1, .85), (71, .60, 1, .85)],
    [(86, .50, 1, 1), (83, .18, 0, .9), (81, .04, 0, .85), (83, .04, 0, .85), (81, .70, 0, .9)],
    [(74, .12, 1, .85), (74, .12, 1, .8), (76, .24, 1, .9), (74, .12, 1, .85), (71, .12, 1, .8), (69, .65, 1, .85)],
]

CHIME_MODES = ((1.0, 1.00, 2.2), (2.756, 0.55, 0.9), (5.404, 0.28, 0.4), (8.933, 0.12, 0.18))  # ratio, amp, tau


def chime_strike(f, n, rng, vel):
    """Free-free tube modes, each a slightly split doublet so it shimmers as it rings."""
    t = tvec(n)
    y = np.zeros(n)
    scale = (700.0 / f) ** 0.4
    for i, (r, a, tau) in enumerate(CHIME_MODES):
        fm = f * r
        if fm > 12000:
            continue
        a = a * vel ** (0.5 + 0.4 * i)
        split = rng.uniform(0.6, 2.2)
        dec = np.exp(-t / (tau * scale))
        for s, w in ((-0.5, 0.65), (0.5, 0.35)):
            y += a * w * dec * np.sin(2 * np.pi * (fm + s * split) * t + rng.uniform(0, 2 * np.pi))
    y *= 1.0 - np.exp(-t / 0.0008)
    m = min(n, 2048)
    tc = tvec(m)
    click = filt(rng.standard_normal(m), "bandpass", (1500.0, 7000.0))
    click *= np.exp(-tc / 0.0015) * (1.0 - np.exp(-tc / 0.0003)) / (click.std() + 1e-12)
    y[:m] += 0.06 * vel * click
    return vel * y


CHIMES = [
    dict(tubes=[74, 76, 78, 81, 83], L=2.6, strikes=7, gust=1.1),
    dict(tubes=[81, 83, 86, 88, 90], L=2.2, strikes=6, gust=0.8),
    dict(tubes=[69, 71, 74, 76, 78], L=3.0, strikes=8, gust=1.5),
    dict(tubes=[76, 78, 81, 83, 86, 88], L=2.4, strikes=9, gust=1.0),
    dict(tubes=[74, 78, 81, 86, 90], L=1.8, strikes=4, gust=0.6),
]


def chimes(seed, c):
    """A gust: strikes cluster, rise and fall in force, sometimes the clapper bounces."""
    rng = rng_for(seed)
    n = int(c["L"] * SR)
    y = np.zeros(n)
    times = np.concatenate([[0.01], 0.01 + np.cumsum(rng.exponential(c["gust"] / c["strikes"], c["strikes"] - 1))])
    times = np.minimum(times, c["L"] - 0.8)
    last = None
    for tm in times:
        tube = rng.choice([x for x in c["tubes"] if x != last])
        last = tube
        force = 0.55 + 0.45 * np.sin(np.pi * min(tm / max(c["gust"], 0.1), 1.0))
        vel = float(np.clip(force * rng.uniform(0.55, 1.0), 0.25, 1.0))
        hits = [(tm, vel)]
        if rng.random() < 0.3:
            hits.append((tm + rng.uniform(0.05, 0.09), vel * 0.35))
        for ht, hv in hits:
            i0 = int(ht * SR)
            y[i0:] += chime_strike(float(midi_hz(tube)), n - i0, rng, hv)
    y = filt(y, "lowpass", 10000.0)
    y = reverb(y, rng, rt=1.5, wet=0.18, pre=0.01)
    return finish(y, length=c["L"], fade_in=0.002, fade_out=0.7)


LIFTS = [  # length, start Hz, end Hz, swirl Hz
    (1.8, 220.0, 2600.0, 3.2),
    (2.2, 160.0, 2000.0, 2.4),
    (2.5, 260.0, 3400.0, 4.0),
]


def wind_lift(seed, L, f_lo, f_hi, swirl_hz):
    """Rising whoosh: a band of noise sweeping up, wobbling, with a moving phaser and a soft whistle."""
    rng = rng_for(seed)
    n = int(L * SR)
    t = tvec(n)
    rise = smoothstep(t / (0.85 * L))
    swirl = 0.22 * np.sin(2 * np.pi * swirl_hz * t + rng.uniform(0, 2 * np.pi)) * smoothstep(t / 0.4)
    c = f_lo * (f_hi / f_lo) ** rise * 2.0 ** swirl
    tau = 1.0 / (0.7 * c + 200.0)

    def gain(f, idx):
        cc = c[idx]
        lf = np.log2((f + 1.0) / cc)
        g = np.exp(-0.5 * (lf / 0.55) ** 2) + 0.15 * np.exp(-0.5 * ((lf - 1.07) / 0.4) ** 2)
        g = g + 0.06 * (f / (f + 150.0)) / (1.0 + (f / 3000.0) ** 2)
        return g * (0.65 + 0.35 * np.cos(2 * np.pi * f * tau[idx]))

    y = shaped_noise(n, rng, gain)
    env = keys_track(t, [(0.0, 0.0), (0.35 * L, 0.8), (0.7 * L, 1.0), (L - 0.03, 0.0)])
    whistle_f = c * (1.0 + 0.004 * np.sin(2 * np.pi * 5.0 * t))
    ph = 2 * np.pi * np.cumsum(whistle_f) / SR
    whistle = (np.sin(ph) + 0.3 * np.sin(2 * ph + 1.0)) * smoothstep((t - 0.2 * L) / (0.4 * L))
    y = env * (y + 0.18 * whistle * (1.0 + 0.3 * fast_noise(n, rng, 8.0)))
    y = reverb(y, rng, rt=1.0, wet=0.2)
    return finish(y, length=L, fade_in=0.02, fade_out=0.15)


# ------------------------------------------------------------------------------------------------
# creatures
# ------------------------------------------------------------------------------------------------

def whale(seed, L, f0k, ampk, f1k, *, slope=(1.15, 1.15), growl=None, breath=0.05, verb=(3.5, 0.5), fade=0.6):
    """Cloud whale: slow gliding moan, rich harmonics through a moving resonance, a detuned twin for
    gentle beating, airy breath and a big dark reverb."""
    rng = rng_for(seed)
    n = int(L * SR)
    t = tvec(n)
    f0 = np.exp(keys_track(t, [(a, np.log(b)) for a, b in f0k]))
    f0 = f0 * 2.0 ** ((0.12 * np.sin(2 * np.pi * 0.7 * t) + 0.08 * slow_noise(n, rng, 1.5)) / 12.0)
    amp = keys_track(t, ampk)
    F1 = keys_track(t, f1k)
    ones = np.ones(n)
    F = np.stack([F1, 820 * ones, 1500 * ones, 2400 * ones])
    B = np.stack([180 * ones, 260 * ones, 420 * ones, 650 * ones])
    A = np.stack([ones, 0.5 * ones, 0.22 * ones, 0.08 * ones])
    sl = np.linspace(slope[0], slope[1], n) + 0.5 * (1.0 - amp / amp.max())
    x = render_harmonics(f0, amp, F, B, A, sl, rng, floor=0.05, lp=3200.0)
    x += 0.35 * render_harmonics(f0 * 1.0035, amp, F, B, A, sl, rng, floor=0.05, lp=3200.0)
    if growl:
        x *= 1.0 - growl[1] * (0.5 + 0.5 * np.sin(2 * np.pi * growl[0] * t))
    ref = np.sqrt(np.mean(x[amp > 0.5 * amp.max()] ** 2))

    def gain(f, idx):
        e = 0.03 + sum(A[i][idx] * reson(f, F[i][idx], 2.0 * B[i][idx]) for i in range(4))
        return e / (1.0 + (f / 3500.0) ** 2)

    br = breath if np.isscalar(breath) else keys_track(t, breath)
    x += ref * shaped_noise(n, rng, gain) * (br * amp / amp.max() if np.isscalar(breath) else br)
    x = reverb(x, rng, rt=verb[0], wet=verb[1], pre=0.035, bright=0.25, damp=2600.0, hp=40.0)
    return finish(x, length=L, fade_in=0.01, fade_out=fade, hp=22.0)


WHALE_SONGS = [
    dict(L=4.6,
         f0=[(0.0, 72), (1.4, 140), (2.0, 122), (2.35, 165), (3.2, 245), (3.9, 190)],
         amp=[(0.0, 0), (0.5, 0.85), (1.5, 1.0), (2.05, 0.0), (2.35, 0.0), (2.75, 0.8), (3.5, 0.75), (4.0, 0)],
         f1=[(0.0, 260), (1.4, 420), (2.0, 330), (2.35, 300), (3.2, 520), (3.9, 380)]),
    dict(L=5.6,
         f0=[(0.0, 62), (1.6, 96), (2.6, 82), (3.0, 110), (4.6, 220), (4.9, 205)],
         amp=[(0.0, 0), (0.7, 0.9), (2.3, 1.0), (2.8, 0.0), (3.0, 0.0), (3.5, 0.7), (4.6, 0.85), (5.0, 0)],
         f1=[(0.0, 240), (1.6, 380), (2.6, 300), (3.0, 300), (4.6, 560)]),
    dict(L=3.8,
         f0=[(0.0, 255), (1.6, 150), (2.1, 120), (2.35, 88), (2.9, 112)],
         amp=[(0.0, 0), (0.35, 0.8), (1.6, 1.0), (2.15, 0.0), (2.35, 0.0), (2.55, 0.6), (2.95, 0)],
         f1=[(0.0, 520), (1.6, 360), (2.1, 300), (2.35, 260), (2.9, 340)]),
    dict(L=6.0,
         f0=[(0.0, 85), (1.2, 130), (1.5, 132), (2.3, 200), (2.9, 170), (3.25, 100), (4.6, 68)],
         amp=[(0.0, 0), (0.4, 0.8), (1.25, 0.75), (1.45, 0.5), (2.3, 1.0), (2.95, 0.0), (3.25, 0.0),
              (3.7, 0.8), (4.6, 0.6), (5.1, 0)],
         f1=[(0.0, 280), (1.2, 380), (2.3, 540), (2.9, 420), (3.25, 300), (4.6, 240)]),
]


def koi(seed, L, bubbles, flutter=0.12):
    """Airy bubble blips (rising sine chirps) over a soft fin-flutter of breathy noise."""
    rng = rng_for(seed)
    n = int(L * SR)
    t = tvec(n)
    y = np.zeros(n)
    for t0, f0, rise, dec, a in bubbles:
        tb = np.maximum(t - t0, 0.0)
        on = t >= t0
        env = on * (1.0 - np.exp(-tb / 0.003)) * np.exp(-tb / dec)
        fr = f0 * (1.0 + rise * (1.0 - np.exp(-tb / 0.02)))
        y += a * env * np.sin(2 * np.pi * np.cumsum(fr * on) / SR)
    fin = shaped_noise(n, rng, lambda f, idx: np.exp(-0.5 * (np.log2((f + 1.0) / 2500.0) / 0.6) ** 2)
                       * np.ones(len(idx)))
    am = (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(24, 32) * t)) ** 2
    fenv = keys_track(t, [(0.0, 0.0), (0.04, 1.0), (0.6 * L, 0.4), (L, 0.0)])
    y += flutter * np.sqrt(np.mean(y ** 2)) / 0.3 * fin * am * fenv
    y = filt(y, "lowpass", 7000.0)
    y = reverb(y, rng, rt=0.4, wet=0.12)
    return finish(y, length=L, fade_in=0.002, fade_out=0.04, hp=60.0)


KOI = [
    (0.28, [(0.01, 900, 0.55, 0.035, 1.0), (0.09, 1250, 0.5, 0.03, 0.7)]),
    (0.34, [(0.01, 1100, 0.6, 0.03, 0.9), (0.06, 820, 0.5, 0.04, 1.0), (0.15, 1400, 0.45, 0.025, 0.6)]),
    (0.24, [(0.01, 1000, 0.7, 0.04, 1.0)]),
]


# ------------------------------------------------------------------------------------------------
# what to make
# ------------------------------------------------------------------------------------------------

FEMALE_HUMS = [
    [N(66, .30, "mm"), N(69, .32, "mm>oo"), N(71, .22, "oo"), N(69, .55, "oo>mm")],
    [N(71, .28, "aa", .9), N(69, .24, "aa>oh"), N(66, .26, "oh"), N(64, .25, "oo"), N(66, .50, "oo>mm")],
    [N(64, .25, "mm"), N(69, .45, "mm>aa"), N(66, .30, "aa>mm")],
    [N(62, .30, "oo"), N(66, .25, "oo>ee"), N(69, .25, "ee"), N(71, .55, "ee>mm")],
    [N(69, .35, "mm>oh"), N(66, .18, "oh", art=True), N(69, .18, "oh"), N(64, .55, "oo>mm")],
]
MALE_HUMS = [
    [N(50, .35, "mm"), N(54, .30, "mm>oh"), N(57, .55, "oh>mm")],
    [N(57, .30, "mm"), N(59, .25, "mm>aa"), N(57, .22, "aa"), N(54, .25, "aa>oh"), N(52, .55, "oo>mm")],
    [N(52, .28, "oo"), N(57, .50, "oo>aa"), N(54, .40, "aa>mm")],
    [N(54, .25, "mm"), N(52, .20, "mm", art=True), N(50, .25, "mm>oo"), N(54, .60, "oo>mm")],
    [N(59, .30, "mm>oh"), N(57, .60, "oh>mm")],
]
CHILD_HUMS = [
    [N(74, .14, "mm"), N(76, .14, "mm>ee", art=True), N(74, .14, "ee", art=True), N(71, .40, "ee>oo")],
    [N(69, .18, "oo"), N(74, .18, "oo>aa"), N(76, .20, "aa", art=True), N(74, .35, "aa>mm")],
    [N(76, .12, "mm"), N(76, .12, "mm", art=True), N(74, .14, "mm>oo", art=True), N(71, .14, "oo"),
     N(74, .38, "oo>mm")],
    [N(71, .20, "mm>ee"), N(76, .40, "ee>mm")],
]
GREETS = {
    "female": [[N(66, .16, "aa", .85), N(71, .32, "oh", art=True)],
               [N(64, .12, "aa", .8), N(66, .12, "aa", .85, art=True), N(71, .30, "oh", art=True)],
               [N(62, .15, "eh>aa", .85), N(69, .34, "oo>oh", art=True)]],
    "male": [[N(52, .16, "aa", .85), N(57, .32, "oh", art=True)],
             [N(50, .12, "aa", .8), N(54, .12, "aa", .85, art=True), N(59, .30, "oh", art=True)],
             [N(54, .15, "eh>aa", .85), N(59, .33, "oo>oh", art=True)]],
    "child": [[N(71, .13, "aa", .85), N(76, .28, "oh", art=True)],
              [N(69, .11, "aa", .8), N(71, .11, "aa", .85, art=True), N(76, .26, "oh", art=True)],
              [N(71, .12, "ee>aa", .85), N(74, .10, "aa", .9, art=True), N(76, .24, "oh", art=True)]],
}


def build_registry():
    """[(event, subtitle text, [(path, maker)], extra json fields)]"""
    R = []

    def ev(event, subtitle, items, **extra):
        R.append((event, subtitle, items, extra))

    def files(folder, stem, makers):
        return [(f"{folder}/{stem}_{i}", mk) for i, mk in enumerate(makers, start=1)]

    for vt, phrases in (("female", FEMALE_HUMS), ("male", MALE_HUMS), ("child", CHILD_HUMS)):
        ev(f"cirri.{vt}.hum", "Cirri child hums" if vt == "child" else "Cirri hums",
           files("cirri", f"{vt}_hum", [lambda s, v=vt, p=p: hum(s, v, p) for p in phrases]))
    for vt in ("female", "male", "child"):
        ev(f"cirri.{vt}.greet", "Cirri child greets you" if vt == "child" else "Cirri greets you",
           files("cirri", f"{vt}_greet", [lambda s, v=vt, p=p: greet(s, v, p) for p in GREETS[vt]]))
    for vt in ("female", "male", "child"):
        ev(f"cirri.{vt}.hurt", "Cirri child hurts" if vt == "child" else "Cirri hurts",
           files("cirri", f"{vt}_hurt", [lambda s, v=vt, k=k: hurt(s, v, k) for k in (1, 2, 3)]))
    for vt in ("female", "male", "child"):
        ev(f"cirri.{vt}.death", "Cirri child dies" if vt == "child" else "Cirri dies",
           [(f"cirri/{vt}_death", lambda s, v=vt: death(s, v))])
    ev("cirri.sleep", "Cirri sleeps",
       files("cirri", "sleep", [lambda s, k=k: sleep(s, k) for k in (1, 2, 3)]), volume=0.5)

    ev("wind_harp.play", "Wind harp plays",
       files("harp", "play", [lambda s, e=e, L=L: harp(s, e, L) for e, L in HARP]))
    ev("windsong_flute.play", "Windsong flute plays",
       files("flute", "play", [lambda s, p=p: flute(s, p) for p in FLUTE]))
    ev("wind_chime.ring", "Wind chimes ring",
       files("chime", "ring", [lambda s, c=c: chimes(s, c) for c in CHIMES]))
    ev("wind_stone.lift", "Wind lifts",
       files("wind", "lift", [lambda s, a=a: wind_lift(s, *a) for a in LIFTS]))

    ev("cloud_whale.song", "Cloud whale sings",
       files("whale", "song", [lambda s, c=c: whale(s, c["L"], c["f0"], c["amp"], c["f1"], slope=(1.4, 1.4)) for c in WHALE_SONGS]))
    ev("cloud_whale.hurt", "Cloud whale groans", files("whale", "hurt", [
        lambda s: whale(s, 0.8, [(0.0, 80), (0.07, 86), (0.55, 55)], [(0.0, 0), (0.04, 1), (0.3, 0.75), (0.6, 0)],
                        [(0.0, 380), (0.55, 260)], slope=(1.1, 1.4), growl=(16.0, 0.18), breath=0.08,
                        verb=(1.8, 0.3), fade=0.15),
        lambda s: whale(s, 0.95, [(0.0, 95), (0.1, 100), (0.7, 62)], [(0.0, 0), (0.05, 1), (0.4, 0.8), (0.75, 0)],
                        [(0.0, 420), (0.7, 270)], slope=(1.1, 1.5), growl=(19.0, 0.2), breath=0.08,
                        verb=(1.8, 0.3), fade=0.15),
    ]))
    ev("cloud_whale.death", "Cloud whale dies", [("whale/death", lambda s: whale(
        s, 2.8, [(0.0, 140), (0.35, 150), (2.2, 46)], [(0.0, 0), (0.3, 1), (1.2, 0.75), (2.25, 0)],
        [(0.0, 450), (2.2, 230)], slope=(1.15, 1.9),
        breath=[(0.0, 0.0), (0.3, 0.05), (1.6, 0.06), (2.2, 0.18), (2.6, 0.0)], verb=(3.0, 0.4), fade=0.4))])
    ev("cloud_koi.flutter", "Cloud koi flutters",
       files("koi", "flutter", [lambda s, L=L, b=b: koi(s, L, b) for L, b in KOI]))
    return R


def encode(ffmpeg, x, wav_path, ogg_path):
    wavfile.write(wav_path, SR, x.astype(np.float32))
    ogg_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
                    "-ac", "1", "-ar", str(SR), "-c:a", "libvorbis", "-q:a", "5",
                    "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(ogg_path)],
                   check=True)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    ffmpeg = find_ffmpeg()
    reg = build_registry()
    sounds_json, lang = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        for event, subtitle, items, extra in reg:
            key = f"subtitles.skyfriends.{event}"
            entries = []
            for rel, maker in items:
                name = f"skyfriends:{rel}"
                entries.append(dict(name=name, **extra) if extra else name)
                if only and only not in rel:
                    continue
                x = maker(rel)
                if not np.all(np.isfinite(x)):
                    sys.exit(f"{rel}: non-finite samples")
                encode(ffmpeg, x, Path(tmp) / (rel.replace("/", "_") + ".wav"), SOUND_DIR / f"{rel}.ogg")
                print(f"  {rel:24s} {len(x) / SR:5.2f} s")
            sounds_json[event] = {"sounds": entries, "subtitle": key}
            lang[key] = subtitle
    (ASSETS / "sounds.json").write_text(json.dumps(sounds_json, indent=2) + "\n", encoding="utf-8")
    (HERE / "lang.json").write_text(json.dumps(lang, indent=2) + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in SOUND_DIR.rglob("*.ogg"))
    print(f"{len(sounds_json)} events, {sum(len(r[2]) for r in reg)} files, {total / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
