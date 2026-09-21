import numpy as np
import wave
import struct
import math
import os

sample_rate = 44100

def save_wav(filename, samples):
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())

# 1. SFX Pop
t = np.linspace(0, 0.15, int(sample_rate * 0.15), False)
freq = np.linspace(400, 1200, len(t))
pop_wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 30)
save_wav("irasutoya_shorts_generator/assets/audio/sfx_pop.wav", pop_wave * 0.8)

# 2. SFX Punchline (Comical Boing + Cymbal / Gong)
t = np.linspace(0, 0.8, int(sample_rate * 0.8), False)
# Modulated boing frequency
f_boing = 250 + 150 * np.sin(2 * np.pi * 12 * t) * np.exp(-t * 4)
boing = np.sin(2 * np.pi * f_boing * t) * np.exp(-t * 5)
noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 8) * 0.3
punchline = boing * 0.7 + noise
save_wav("irasutoya_shorts_generator/assets/audio/sfx_punchline.wav", punchline * 0.8)

# 3. Comical BGM Loop (Bouncy Marimba / Pizzicato comedy tune in C Major, 120 BPM)
bpm = 130
beat = 60.0 / bpm
bar = beat * 4
total_bars = 8
duration = bar * total_bars
t_total = np.linspace(0, duration, int(sample_rate * duration), False)
bgm = np.zeros_like(t_total)

# Marimba note synthesis helper
def add_note(audio, start_time, duration_note, pitch, amp=0.5):
    idx_start = int(start_time * sample_rate)
    n_samples = int(duration_note * sample_rate)
    if idx_start + n_samples > len(audio):
        n_samples = len(audio) - idx_start
    if n_samples <= 0: return
    t_n = np.linspace(0, duration_note, n_samples, False)
    # Marimba-like harmonics (fundamental + sharp transient + gentle decay)
    sig = (np.sin(2 * np.pi * pitch * t_n) +
           0.4 * np.sin(2 * np.pi * pitch * 2 * t_n) +
           0.2 * np.sin(2 * np.pi * pitch * 3 * t_n) +
           0.1 * np.sin(2 * np.pi * pitch * 4 * t_n))
    env = np.exp(-t_n * 12)
    audio[idx_start:idx_start + n_samples] += sig * env * amp

# Note pitches (Hz)
notes = {
    'C3': 130.81, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
    'D5': 587.33, 'E5': 659.25, 'G5': 783.99
}

# Fun bouncy comedy melody pattern (Japanese anime / manzai style)
# Bar 1: C - E - G - E
# Bar 2: F - A - G - E
# Bar 3: D - F - E - D
# Bar 4: C - G3 - C4 - rest
melody = [
    # Bar 1
    (0 * beat, 'C4'), (0.5 * beat, 'E4'), (1.0 * beat, 'G4'), (1.5 * beat, 'E4'),
    (2.0 * beat, 'C4'), (2.5 * beat, 'E4'), (3.0 * beat, 'G4'), (3.5 * beat, 'C5'),
    # Bar 2
    (4 * beat, 'A4'), (4.5 * beat, 'C5'), (5.0 * beat, 'A4'), (5.5 * beat, 'G4'),
    (6.0 * beat, 'E4'), (6.5 * beat, 'G4'), (7.0 * beat, 'E4'), (7.5 * beat, 'D4'),
    # Bar 3
    (8 * beat, 'D4'), (8.5 * beat, 'F4'), (9.0 * beat, 'A4'), (9.5 * beat, 'F4'),
    (10.0 * beat, 'D4'), (10.5 * beat, 'F4'), (11.0 * beat, 'G4'), (11.5 * beat, 'B4'),
    # Bar 4
    (12 * beat, 'C5'), (12.5 * beat, 'G4'), (13.0 * beat, 'E4'), (13.5 * beat, 'D4'),
    (14.0 * beat, 'C4'), (15.0 * beat, 'C4'),
    
    # Bar 5 (Repeat with variation / octave up)
    (16 * beat, 'C5'), (16.5 * beat, 'E5'), (17.0 * beat, 'G5'), (17.5 * beat, 'E5'),
    (18.0 * beat, 'C5'), (18.5 * beat, 'E5'), (19.0 * beat, 'G5'), (19.5 * beat, 'C5'),
    # Bar 6
    (20 * beat, 'A4'), (20.5 * beat, 'C5'), (21.0 * beat, 'A4'), (21.5 * beat, 'G4'),
    (22.0 * beat, 'E4'), (22.5 * beat, 'G4'), (23.0 * beat, 'C5'),
    # Bar 7
    (24 * beat, 'D5'), (24.5 * beat, 'C5'), (25.0 * beat, 'B4'), (25.5 * beat, 'A4'),
    (26.0 * beat, 'G4'), (26.5 * beat, 'A4'), (27.0 * beat, 'B4'),
    # Bar 8
    (28 * beat, 'C5'), (29.0 * beat, 'G4'), (30.0 * beat, 'C4')
]

for t_pos, n in melody:
    add_note(bgm, t_pos, 0.4, notes[n], amp=0.35)

# Bouncy staccato bassline (pizzicato)
for bar_idx in range(8):
    b_start = bar_idx * bar
    root = 'C3' if bar_idx in [0, 1, 3, 4, 5, 7] else ('F3' if bar_idx in [2] else 'G3')
    fifth = 'G3'
    add_note(bgm, b_start + 0 * beat, 0.3, notes.get(root, 130), amp=0.45)
    add_note(bgm, b_start + 1 * beat, 0.3, notes.get(fifth, 196), amp=0.35)
    add_note(bgm, b_start + 2 * beat, 0.3, notes.get(root, 130), amp=0.45)
    add_note(bgm, b_start + 3 * beat, 0.3, notes.get(fifth, 196), amp=0.35)

save_wav("irasutoya_shorts_generator/assets/audio/bgm_comical.wav", bgm * 0.7)
print("Generated BGM and SFX audio files successfully!")
