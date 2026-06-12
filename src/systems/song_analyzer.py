"""Song tempo analysis via librosa for auto-generated charts."""

from __future__ import annotations


def analyze_song(audio_file: str) -> tuple[list[float], float] | None:
    """Return (beat_times_seconds, duration_seconds) for the given audio file.

    Returns None when librosa is unavailable or the file cannot be analyzed,
    so the caller can fall back to the fixed-BPM beat grid.
    """
    try:
        import librosa
        import numpy as np
    except ImportError:
        print("[Auto] librosa not installed - falling back to fixed BPM")
        return None

    try:
        print(f"[Auto] Analyzing tempo of '{audio_file}'...")
        y, sr = librosa.load(audio_file, mono=True)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        duration = float(librosa.get_duration(y=y, sr=sr))
        bpm = float(np.atleast_1d(tempo)[0])
        print(f"[Auto] Detected {bpm:.1f} BPM, {len(beat_times)} beats, "
              f"{duration:.1f}s duration")
        if not beat_times:
            return None
        return beat_times, duration
    except Exception as exc:
        print(f"[Auto] Song analysis failed ({exc}) - falling back to fixed BPM")
        return None
