import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pygame
import scipy.signal
import time

AUDIO_FILE = "song_fred.mp3"

# ─────────────────────────────────────────
# 1. ANALYSIS (all upfront)
# ─────────────────────────────────────────
print("Analyzing...")
y, sr = librosa.load(AUDIO_FILE, sr=44100, mono=True)
y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
duration = librosa.get_duration(y=y, sr=sr)

# Mel spectrogram
melspec = librosa.power_to_db(
    librosa.feature.melspectrogram(y=y, sr=sr, hop_length=512),
    ref=np.max
)

# Onset strength envelope (full signal)
hop_length = 512
onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
onset_times = librosa.times_like(onset_env, sr=sr, hop_length=hop_length)

# Beat times
tempo_dynamic = librosa.feature.tempo(y=y, sr=sr, aggregate=None, std_bpm=2)
_, beat_times = librosa.beat.beat_track(
    y=y, sr=sr, bpm=tempo_dynamic, units='time', trim=False, hop_length=hop_length
)
bpm = int(round(60.0 / np.median(np.diff(beat_times))))

# Kick times
def bandpass(signal, sr, low_hz, high_hz, order=2):
    nyq = sr / 2.0
    b, a = scipy.signal.butter(order, [low_hz / nyq, high_hz / nyq], btype='band')
    filtered = scipy.signal.filtfilt(b, a, signal)
    return np.nan_to_num(filtered, nan=0.0, posinf=0.0, neginf=0.0)

y_kick = bandpass(y, sr, 50, 150)
kick_env = librosa.onset.onset_strength(y=y_kick, sr=sr, hop_length=hop_length, fmax=200)
kick_times = librosa.onset.onset_detect(
    onset_envelope=kick_env, sr=sr, hop_length=hop_length,
    backtrack=True, units='time',
    pre_max=3, post_max=3, pre_avg=10, post_avg=10, delta=0.3, wait=8
)

print(f"BPM: {bpm} | Beats: {len(beat_times)} | Kicks: {len(kick_times)}")

# ─────────────────────────────────────────
# 2. FIGURE SETUP  (3 rows)
# ─────────────────────────────────────────
fig, (ax_mel, ax_onset, ax_kick) = plt.subplots(
    3, 1, figsize=(14, 8), sharex=False
)
fig.patch.set_facecolor('#0e0e0e')
for ax in (ax_mel, ax_onset, ax_kick):
    ax.set_facecolor('#0e0e0e')
    ax.tick_params(colors='#aaaaaa')
    ax.xaxis.label.set_color('#aaaaaa')
    ax.yaxis.label.set_color('#aaaaaa')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')

# ── Row 1: Mel spectrogram ─────────────
librosa.display.specshow(
    melspec, sr=sr, hop_length=512,
    x_axis='time', y_axis='mel',
    ax=ax_mel, cmap='magma'
)
ax_mel.set_title(f'Mel Spectrogram  —  {bpm} BPM', color='white', fontsize=11)
ax_mel.set_xlabel('')
ax_mel.set_ylabel('Hz', fontsize=9)

# Mark beats on mel
for bt in beat_times:
    ax_mel.axvline(bt, color='cyan', alpha=0.25, linewidth=0.6)

# Mark kicks on mel
for kt in kick_times:
    ax_mel.axvline(kt, color='orange', alpha=0.35, linewidth=0.8)

# ── Row 2: Onset envelope (beats) ──────
ax_onset.plot(onset_times, onset_env, color='#00ccff', linewidth=0.8, alpha=0.9)
for bt in beat_times:
    ax_onset.axvline(bt, color='cyan', alpha=0.3, linewidth=0.7)
ax_onset.set_title('Onset Strength  (beats = cyan)', color='white', fontsize=10)
ax_onset.set_ylabel('Strength', fontsize=9)
ax_onset.set_xlim(0, duration)

# ── Row 3: Kick envelope ───────────────
kick_onset_times = librosa.times_like(kick_env, sr=sr, hop_length=hop_length)
ax_kick.plot(kick_onset_times, kick_env, color='#ff6600', linewidth=0.8, alpha=0.9)
for kt in kick_times:
    ax_kick.axvline(kt, color='orange', alpha=0.4, linewidth=0.7)
ax_kick.set_title('Kick Envelope  (kicks = orange)', color='white', fontsize=10)
ax_kick.set_ylabel('Strength', fontsize=9)
ax_kick.set_xlabel('Time (s)', fontsize=9)
ax_kick.set_xlim(0, duration)

plt.tight_layout(pad=1.5)

# ─────────────────────────────────────────
# 3. PLAYHEAD LINES  (one per row)
# ─────────────────────────────────────────
line_mel   = ax_mel.axvline(0, color='white', linewidth=1.5, alpha=0.85, zorder=10)
line_onset = ax_onset.axvline(0, color='white', linewidth=1.5, alpha=0.85, zorder=10)
line_kick  = ax_kick.axvline(0, color='white', linewidth=1.5, alpha=0.85, zorder=10)

# Scrolling window width in seconds
WINDOW = 20.0

# Time label
time_text = ax_mel.text(
    0.01, 0.93, '', transform=ax_mel.transAxes,
    color='white', fontsize=10, va='top',
    bbox=dict(facecolor='#0e0e0e', edgecolor='none', alpha=0.7)
)

# ─────────────────────────────────────────
# 4. AUDIO PLAYBACK
# ─────────────────────────────────────────
pygame.mixer.init()
pygame.mixer.music.load(AUDIO_FILE)
pygame.mixer.music.play()
start_wall = time.time()

# ─────────────────────────────────────────
# 5. ANIMATION
# ─────────────────────────────────────────
def update(frame):
    now = time.time() - start_wall

    line_mel.set_xdata([now, now])
    line_onset.set_xdata([now, now])
    line_kick.set_xdata([now, now])

    pad_left  = WINDOW * 0.3
    win_start = max(0, now - pad_left)
    win_end   = win_start + WINDOW

    ax_mel.set_xlim(win_start, win_end)
    ax_onset.set_xlim(win_start, win_end)
    ax_kick.set_xlim(win_start, win_end)

    time_text.set_text(f't = {now:.2f}s')
    # no return needed with blit=False

ani = animation.FuncAnimation(
    fig,
    update,
    interval=33,
    blit=False,          # ← was True, that's what breaks scrolling
    cache_frame_data=False
)

plt.show()
pygame.mixer.music.stop()
pygame.quit()