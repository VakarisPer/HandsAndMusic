# Hand-Gesture-Controlled Rhythm Game

Version: `0.1.0`

A rhythm game controlled by hand gestures (MediaPipe + OpenCV) with deterministic BPM-grid timing and a modular OOP architecture.

## Project Description

This project combines:
- camera-based hand gesture recognition,
- a lane-based rhythm gameplay loop,
- deterministic beat scheduling based on BPM,
- Pygame rendering and audio playback.

The runtime design favors consistent playability over heavy music analysis. Notes are scheduled from a BPM grid so the same song configuration always produces the same gameplay chart.

## Setup (Step by Step)

1. Use Python 3.11+.
2. Create and activate a virtual environment.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Ensure your webcam is connected.
5. Place your song file in the project root (default `song_fred.mp3`).
6. Run the game:
   - `python main.py`

## How It Works

### Gesture -> Detection -> Gameplay Loop

1. `HandTrackerAdapter` polls gestures from MediaPipe landmarks.
2. `InputSystem` maps gestures (and keyboard fallback) to lane actions.
3. `BeatGrid` generates beat timestamps from BPM (`BEAT_INTERVAL = 60 / BPM`).
4. `ChartGenerator` converts beats into chart events (`tap` / `hold`).
5. `SpawnSystem` spawns notes when `current_time >= note.time - spawn_offset`.
6. `TimingJudge` evaluates hit timing (`perfect`, `good`, `miss`).
7. `ScoreSystem` updates score, combo, and accuracy.
8. `RenderSystem` draws notes, receptors, and HUD.

## Controls / Demo

- Hand gestures are mapped to 5 lanes via `src/config/settings.py`.
- Keyboard fallback:
  - `1`, `2`, `3`, `4`, `5` -> lanes 0..4
- `P` toggles pause.
- `ESC` exits.

## Architecture

```
src/
  core/       # GameApp, state machine, system factory
  domain/     # Note, ChartEvent, ScoreState
  systems/    # beat grid, chart generation, spawn, input, judge, score, render
  vision/     # hand tracking adapter
  audio/      # deterministic audio clock
  io/         # calibration/results persistence
  config/     # gameplay and timing configuration
  version.py  # semantic version
tests/
```

## OOP and Coursework Mapping

- **Encapsulation**: stateful systems hide internals (`AudioClock`, `SpawnSystem`, `ScoreSystem`).
- **Abstraction**: `GameApp` coordinates subsystems through clear interfaces.
- **Inheritance / Polymorphism**: domain uses typed model hierarchies (`NoteKind`) and extensible system factory creation paths.
- **Composition/Aggregation**: `GameApp` composes independent systems.
- **Design Pattern**: `SystemFactory` implements Factory Method for runtime component creation.
- **File Read/Write**: `SessionStore` saves calibration and run results to JSON.

## Testing

Run:
- `python -m unittest discover -s tests -p "test_*.py"`

Current tests cover:
- BPM beat grid generation,
- spawn scheduling,
- timing judgement windows,
- scoring/combo logic,
- persistence file I/O.

## Future Improvements

- Add in-game calibration UI.
- Add difficulty presets and chart authoring.
- Improve gesture smoothing and camera latency compensation.
- Add menu scene with song selection.
- Add richer hold-note mechanics and visual FX.
