import numpy as np
import librosa
import scipy.signal
import pygame
import time

AUDIO_FILE = "song_fred.mp3"

# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────

def bandpass(signal, sr, low_hz, high_hz, order=2):
    """Apply bandpass filter to signal"""
    nyq = sr / 2.0
    b, a = scipy.signal.butter(order, [low_hz / nyq, high_hz / nyq], btype='band')
    filtered = scipy.signal.filtfilt(b, a, signal)
    return np.nan_to_num(filtered, nan=0.0, posinf=0.0, neginf=0.0)


def analyze_audio(audio_file):
    """
    Analyze audio file and extract rhythm data
    Returns: dict with beat_times, kick_times, bpm, duration, onset data
    """
    print(f"[Audio] Analyzing {audio_file}...")
    
    y, sr = librosa.load(audio_file, sr=44100, mono=True)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)
    duration = librosa.get_duration(y=y, sr=sr)
    
    # Beat detection
    hop_length = 512
    tempo_dynamic = librosa.feature.tempo(y=y, sr=sr, aggregate=None, std_bpm=2)
    _, beat_times = librosa.beat.beat_track(
        y=y, sr=sr, bpm=tempo_dynamic, units='time', trim=False, hop_length=hop_length
    )
    bpm = int(round(60.0 / np.median(np.diff(beat_times))))
    
    # Onset strength (melody/complexity)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.times_like(onset_env, sr=sr, hop_length=hop_length)
    
    # Kick detection (bass)
    y_kick = bandpass(y, sr, 50, 150)
    kick_env = librosa.onset.onset_strength(y=y_kick, sr=sr, hop_length=hop_length, fmax=200)
    kick_times = librosa.onset.onset_detect(
        onset_envelope=kick_env, sr=sr, hop_length=hop_length,
        backtrack=True, units='time',
        pre_max=3, post_max=3, pre_avg=10, post_avg=10, delta=0.3, wait=8
    )
    
    print(f"[Audio] BPM: {bpm} | Beats: {len(beat_times)} | Kicks: {len(kick_times)} | Duration: {duration:.1f}s")
    
    return {
        'beat_times': np.array(beat_times),
        'kick_times': np.array(kick_times),
        'onset_env': onset_env,
        'onset_times': onset_times,
        'bpm': bpm,
        'duration': duration,
        'sample_rate': sr,
        'hop_length': hop_length
    }


def play_audio(audio_file):
    """Start playing audio file and return start time"""
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    start_time = time.time()
    print(f"[Audio] Playing {audio_file}")
    return start_time


def get_current_time(start_time):
    """Get elapsed time since audio started"""
    return time.time() - start_time


def stop_audio():
    """Stop audio playback"""
    pygame.mixer.music.stop()
    pygame.quit()
    print("[Audio] Stopped")