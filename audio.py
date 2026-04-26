"""Audio: detect BPM with librosa, play music, expose elapsed time."""

import time

import numpy as np
import librosa
import pygame


def detect_bpm(audio_file):
    """Analyze the file and return its BPM as an integer."""
    print(f"[Audio] Analyzing {audio_file}...")
    y, sr = librosa.load(audio_file, sr=44100, mono=True)
    y = np.nan_to_num(y, nan=0.0, posinf=0.0, neginf=0.0)

    tempo = librosa.feature.tempo(y=y, sr=sr, aggregate=None, std_bpm=2)
    _, beat_times = librosa.beat.beat_track(
        y=y, sr=sr, bpm=tempo, units='time', trim=False, hop_length=512,
    )
    bpm = int(round(60.0 / np.median(np.diff(beat_times))))
    print(f"[Audio] BPM={bpm}")
    return bpm


def play_audio(audio_file):
    """Start playing the file. Returns the wall-clock start time."""
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    print(f"[Audio] Playing {audio_file}")
    return time.time()


def get_current_time(start_time):
    """Seconds elapsed since play_audio()."""
    return time.time() - start_time
