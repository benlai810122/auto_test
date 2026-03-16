import numpy as np
import soundfile as sf
from dataclasses import dataclass, asdict
import json

@dataclass
class ToneResult:
    name: str
    start_s: float
    dropout_count: int
    dropout_total_ms: float
    dropout_max_ms: float
    level_db_mean: float
    level_db_std: float

def to_mono(x: np.ndarray) -> np.ndarray:
    return x.astype(np.float32) if x.ndim == 1 else x.mean(axis=1).astype(np.float32)

def goertzel_power_frames(x: np.ndarray, fs: int, f0: float = 1000.0,
                          frame_ms: float = 20.0, hop_ms: float = 10.0):
    """Return (p, t): power at f0 per frame, and frame center times."""
    frame = int(fs * frame_ms / 1000.0)
    hop = int(fs * hop_ms / 1000.0)
    if frame <= 0 or hop <= 0 or len(x) < frame:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32)

    # Goertzel coefficient
    w = 2.0 * np.pi * f0 / fs
    cos_w = np.cos(w)
    coeff = 2.0 * cos_w

    n_frames = 1 + (len(x) - frame) // hop
    p = np.empty(n_frames, dtype=np.float32)
    t = np.empty(n_frames, dtype=np.float32)

    for i in range(n_frames):
        s = i * hop
        seg = x[s:s+frame]

        s_prev = 0.0
        s_prev2 = 0.0
        for sample in seg:
            s_curr = sample + coeff * s_prev - s_prev2
            s_prev2 = s_prev
            s_prev = s_curr

        # Power at f0
        power = s_prev2*s_prev2 + s_prev*s_prev - coeff*s_prev*s_prev2
        p[i] = float(power)
        t[i] = (s + frame/2) / fs

    return p, t

def find_start(p: np.ndarray, t: np.ndarray, thr: float, hold_frames: int = 5) -> float:
    """First time where p stays above thr for hold_frames."""
    if p.size == 0:
        return float("nan")
    above = p > thr
    for i in range(0, len(above) - hold_frames):
        if np.all(above[i:i+hold_frames]):
            return float(t[i])
    return float("nan")

def dropout_stats(p: np.ndarray, t: np.ndarray, thr: float, start_s: float,
                  min_ms: float = 50.0):
    """Dropouts after start_s where p < thr for at least min_ms."""
    if p.size < 2 or not np.isfinite(start_s):
        return 0, 0.0, 0.0
    hop_s = float(t[1] - t[0])
    min_frames = int((min_ms/1000.0) / hop_s)

    mask_after = t >= start_s
    p2 = p[mask_after]
    t2 = t[mask_after]
    below = p2 < thr

    count = 0
    total_ms = 0.0
    max_ms = 0.0

    i = 0
    while i < len(below):
        if below[i]:
            j = i
            while j < len(below) and below[j]:
                j += 1
            frames = j - i
            if frames >= min_frames:
                dur_ms = frames * hop_s * 1000.0
                count += 1
                total_ms += dur_ms
                max_ms = max(max_ms, dur_ms)
            i = j
        else:
            i += 1

    return count, total_ms, max_ms

def analyze_audio(path: str, name: str, fs_expected: int = 48000):
    x, fs = sf.read(path)
    if fs != fs_expected:
        raise ValueError(f"{name}: expected {fs_expected} Hz, got {fs} Hz")
    x = to_mono(x)

    p, t = goertzel_power_frames(x, fs, f0=1000.0, frame_ms=20, hop_ms=10)
    if p.size == 0:
        return ToneResult(name, float("nan"), 0, 0.0, 0.0, float("nan"), float("nan")), p, t

    # Threshold: robust approach
    # Use early part (first 3 seconds) as "noise floor" since buzzer starts later.
    noise_region = p[t < 3.0] if np.any(t < 3.0) else p[:max(1, len(p)//10)]
    noise_med = float(np.median(noise_region))
    noise_mad = float(np.median(np.abs(noise_region - noise_med)) + 1e-12)

    # threshold = noise + K * mad  (K=15 is conservative)
    thr = noise_med + 15.0 * noise_mad

    start_s = find_start(p, t, thr, hold_frames=5)
    dcnt, dtotal, dmax = dropout_stats(p, t, thr, start_s, min_ms=50.0)

    # Level statistics in dB (after tone start)
    valid = (t >= start_s) if np.isfinite(start_s) else np.ones_like(t, dtype=bool)
    level_db = 10.0 * np.log10(p[valid] + 1e-12)
    level_mean = float(np.mean(level_db)) if level_db.size else float("nan")
    level_std = float(np.std(level_db)) if level_db.size else float("nan")

    return ToneResult(name, start_s, dcnt, dtotal, dmax, level_mean, level_std), p, t

def analyze_tx_rx_and_get_report(ref_path: str, tx_path: str, rx_path: str, out_json="metrics.json"):
    ref_res, _, _ = analyze_audio(ref_path, "ref")
    tx_res, _, _ = analyze_audio(tx_path, "tx_mic")
    rx_res, _, _ = analyze_audio(rx_path, "rx_loopback")

    latency_tx_ms = (tx_res.start_s - ref_res.start_s) * 1000.0
    latency_rx_ms = (rx_res.start_s - ref_res.start_s) * 1000.0

    out = {
        "reference": asdict(ref_res),
        "tx_mic": {**asdict(tx_res), "latency_vs_ref_ms": latency_tx_ms},
        "rx_loopback": {**asdict(rx_res), "latency_vs_ref_ms": latency_rx_ms},
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print("Saved:", out_json)
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    pass