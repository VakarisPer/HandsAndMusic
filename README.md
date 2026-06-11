# Hands & Music

A hand gesture–controlled rhythm game. Point your fingers at falling tiles to catch them, open your palm to clear whole rows, and chase golden tiles for bonus points — all tracked live through your webcam.

Built with **Python**, **Pygame**, **OpenCV**, and **MediaPipe**.

<img width="962" height="542" alt="Gameplay screenshot" src="https://github.com/user-attachments/assets/e66ada72-23ec-4fbd-9445-1a445eb65f96" />

<img width="478" height="493" alt="Menu screenshot" src="https://github.com/user-attachments/assets/53c452e5-7565-4e76-b094-a6b6692d0a52" />

## Features

- **Real-time hand tracking** — your index finger is the controller (MediaPipe, two hands supported)
- **Open Palm gesture** — catches chord rows across all 5 lanes at once
- **Golden tiles** — rare glowing tiles worth a +100 bonus
- **Timing judgement** — Perfect / Good / Late windows with combo-based scoring
- **Manual level editor** — record your own beatmaps by tapping along to any song
- **Auto mode** — generates a chart from BPM for any `.mp3` / `.wav` you select
- **Persistent leaderboard** — top 10 scores with player names and max combos
- **Particles & animated HUD** — catch bursts, floating hit feedback, rainbow combo counter

## Requirements

- Python **3.10+**
- A **webcam**
- Dependencies (see [requirements.txt](requirements.txt)):
  - `pygame`
  - `opencv-python`
  - `mediapipe`
  - `numpy`

## Installation

```bash
git clone https://github.com/VakarisPer/HandsAndMusic.git
cd HandsAndMusic
pip install -r requirements.txt
python main.py
```

## How to Play

1. Open **Settings**, enter your name, and pick a music track (or select a recorded level).
2. Hit **START** and show your hands to the camera.
3. Catch tiles as they reach the receptors at the bottom:

| Input | Action |
|-------|--------|
| Point finger at a receptor | Catch tiles in that lane |
| Open palm | Catch a full 5-lane chord row |
| Keys `1`–`5` | Keyboard fallback for lanes |
| `P` | Pause |
| `ESC` | Back to menu |

**Scoring:** Perfect +10, Good +5, Late/Miss −5 and combo reset. Golden tiles add +100.

## Creating Your Own Levels

1. Go to **Settings → RECORD LEVEL**
2. **Browse** for an audio file and enter a level name
3. Press **START RECORDING** — the song plays while you tap:
   - `1`–`5` to place a note in a lane
   - `0` for a full chord row
   - `U` to undo, `Q` to save and quit
4. The level is saved to `levels/<name>.json` — select it in Settings to play it

## Project Structure

```
HandsAndMusic/
├── main.py                  # Entry point — menu ↔ game loop
├── hand_tracking/           # Webcam capture + gesture recognition (MediaPipe)
├── src/
│   ├── core/                # GameApp orchestrator, system factory, state machine
│   ├── systems/             # Rendering, scoring, spawning, timing, input, particles
│   ├── audio/               # Song playback clock
│   ├── vision/              # Hand tracker adapter (smoothing, gesture debounce)
│   ├── ui/                  # Menu, settings, level recorder, camera overlay
│   ├── io/                  # Score + session persistence
│   ├── config/              # Game settings
│   └── domain/              # Data models (Note, ChartEvent, ScoreState)
├── tools/create_chart.py    # Standalone chart creator CLI
├── levels/                  # Saved beatmaps (JSON)
├── music/, audio/           # Audio files
├── fonts/                   # Pixel font
└── tests/                   # Unit tests
```

## Running Tests

```bash
python -m unittest discover -s tests
```
