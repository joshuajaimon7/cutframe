import numpy as np
import scipy.io.wavfile as wavfile
from pathlib import Path

out_dir = Path("assets/sfx")
out_dir.mkdir(parents=True, exist_ok=True)
sr = 48000

# 1. Sub Thud (Cinematic deep low-end hit, 60-110Hz, warm tanh saturation)
def make_sub_thud():
    dur = 0.5
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Pitch drop from 115Hz down to 42Hz
    freq = 42.0 + (115.0 - 42.0) * np.exp(-12.0 * t)
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sig = np.sin(phase)
    # Exponential decay envelope
    env = np.exp(-7.5 * t)
    sig = sig * env
    # Warm analog saturation
    sig = np.tanh(sig * 1.8) * 0.95
    return (sig * 32767).astype(np.int16)

# 2. Paper Slide (Textured organic matte slide)
def make_paper_slide():
    dur = 0.35
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Generate pink-like noise
    noise = np.random.normal(0, 1, len(t))
    # Simple recursive low/bandpass filter
    filtered = np.zeros_like(noise)
    for i in range(1, len(noise)):
        filtered[i] = 0.85 * filtered[i-1] + 0.15 * noise[i]
    # Slide frequency modulation envelope
    env = np.sin(np.pi * (t / dur) ** 0.7)
    sig = filtered * env
    # Add subtle friction scrape texture
    sig += 0.3 * np.sin(2 * np.pi * (800 - 300 * (t/dur)) * t) * env
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.8
    return (sig * 32767).astype(np.int16)

# 3. Soft Pop / Tactile Click (Apple UI style)
def make_soft_pop():
    dur = 0.06
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # 2.2kHz snap + 320Hz body
    click = np.sin(2 * np.pi * 2200 * t) * np.exp(-70 * t)
    body = np.sin(2 * np.pi * 320 * t) * np.exp(-40 * t)
    sig = 0.6 * click + 0.7 * body
    sig = sig / (np.max(np.abs(sig)) + 1e-6) * 0.85
    return (sig * 32767).astype(np.int16)

# 4. Cinematic Riser (Building swell that abruptly cuts off)
def make_riser():
    dur = 1.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    # Exponential swell curve
    env = (np.exp(3.0 * t / dur) - 1.0) / (np.exp(3.0) - 1.0)
    # Rising filtered tone
    freq = 120 + 350 * (t / dur)**2
    phase = 2 * np.pi * np.cumsum(freq) / sr
    sig = np.sin(phase) + 0.35 * np.sin(2 * phase)
    # Add subtle rising noise
    noise = np.random.normal(0, 0.25, len(t)) * env
    sig = (sig * env + noise) * 0.85
    # Smooth fade out at the very end (last 5ms) to prevent click
    fade_len = int(0.005 * sr)
    sig[-fade_len:] *= np.linspace(1, 0, fade_len)
    return (sig * 32767).astype(np.int16)

wavfile.write(out_dir / "sub_thud.wav", sr, make_sub_thud())
wavfile.write(out_dir / "paper_slide.wav", sr, make_paper_slide())
wavfile.write(out_dir / "pop_soft.wav", sr, make_soft_pop())
wavfile.write(out_dir / "riser.wav", sr, make_riser())
print("Generated studio SFX pack successfully!")
