# 🎵 Hand Gesture‑Controlled Rhythm Game

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Tracking-ff69b4)](https://mediapipe.dev/)
[![Librosa](https://img.shields.io/badge/Librosa-BPM%20Detection-green)](https://librosa.org/)

A real‑time rhythm game where your **hand gestures** control the action.  
Choose a song → the game detects its **BPM** → tiles fall in perfect sync with the beat.  
Use your **index finger** to catch regular tiles, and an **open palm** to collect special 5‑tile bursts.

<p align="center">
  <img src="https://github.com/user-attachments/assets/cd2ac3a9-7b90-4ac7-88c6-cd97e0597fc9" width="30%">
  <img src="https://github.com/user-attachments/assets/1d6c053e-25fc-40be-b532-e2ebcc9f9f41" width="30%">
</p>

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [How to Play](#how-to-play)
  - [Music Selection](#music-selection)
  - [Gesture Controls](#gesture-controls)
  - [Rhythm Mechanics](#rhythm-mechanics)
- [Project Structure](#project-structure)
- [OOP Implementation](#oop-implementation)
- [Design Patterns](#design-patterns)
- [Technical Documentation](#technical-documentation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Screenshots](#screenshots)

---

## Overview

**Hand Gesture‑Controlled Rhythm Game** turns your webcam into a motion controller.  
Pick a music file – the program analyses its **BPM** using `librosa`. Tiles are generated on beat boundaries, and their falling speed matches the music’s tempo.  

- 🖐️ **Index finger tip** (MediaPipe landmark #8) catches single tiles.  
- ✋ **Open palm** (all five fingers extended) catches an entire **5‑tile burst** that appears every N beats (configurable).  

Both hands are tracked simultaneously, and the game provides real‑time visual feedback and score persistence

---

## Features

| Category | Details |
|----------|---------|
| 🎵 **Music‑driven gameplay** | Load any `.mp3` or `.wav` – BPM is detected automatically. Tile fall speed and spawn timing are locked to the beat. |
| 🖱️ **Index finger catching** | Only your **index fingertip** (landmark 8) catches regular falling tiles. Dual‑hand support – use one or both hands. |
| ✋ **Open palm burst** | Every **N beats** (set in config), a special group of **5 tiles** appears. Extend **all five fingers** of either hand to catch all five at once for a massive +5 points. |
| 📈 **BPM‑synchronised tiles** | Higher BPM = faster falling tiles, keeping the challenge rhythmically consistent. |
| 🎨 **Visual feedback** | Tiles flash **green** when caught, **red** when missed. Burst tiles glow with a special effect. |
| 💾 **Score persistence** | High scores are saved to `scores.json`. |
| 🎮 **Main menu (in config file)** | Choose your song, adjust burst frequency (beats per burst), and start the game. |

---

## Installation

### Prerequisites
- Python 3.8 or higher
- A working webcam
- 300+ MB free disk space (for `librosa` and dependencies)

### Setup

1. **Clone or download the project**
   ```bash
   git clone https://github.com/yourusername/Hand-Gesture-Rhythm-Game.git
   cd Hand-Gesture-Rhythm-Game
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

> `requirements.txt` includes: `pygame`, `opencv-python`, `mediapipe`, `numpy`, `librosa`, `scipy`

---

## How to Run

```bash
python main.py
```

- The **main menu** opens. Select a music file and adjust the **“burst every N beats”** setting (e.g., 8 beats = one 5‑tile wave).
- Press `Start Game` – the webcam feed appears, and tiles begin falling in sync with the music.
- Press `Q` or close the window to exit.

---

## How to Play

### Music Selection
- Supported formats: `.mp3`, `.wav`, `.ogg`
- BPM is detected using **librosa** (onset detection + tempo estimation).  
- The game automatically calculates **tile fall speed** as:  
  `speed = screen_height / (60 / BPM * beat_duration_factor)`  

### Gesture Controls

#### 🖱️ Catching Regular Tiles – Index Finger Only
- Extend your **index finger** (pointing gesture).  
- Touch the falling tile with your **index fingertip** (landmark #8).  
- Both hands work independently – you can catch two tiles at once if each hand’s index finger touches a different tile.  
- **Scoring:** +1 per tile caught. **Missed tile:** -1 (if it passes the bottom without being caught).

#### ✋ Catching the 5‑Tile Burst – Open Palm
- Every **N beats** (configurable, default = 8 beats), a swirling group of **5 tiles** appears.  
- To catch all five at once, extend **all five fingers** of **either hand** (open palm gesture).  
- The tiles are removed instantly, and you receive **+5 points**.  
- If you miss the burst (no open palm while it’s on screen), no penalty is applied – the burst simply disappears.

### Rhythm Mechanics
- Tiles are **only generated on beat positions** – never between beats.  
- The exact spawn time is aligned with the music’s beat grid using the detected BPM.  
- As BPM increases, tiles fall faster – maintaining a consistent rhythmic challenge.

---

## Project Structure

```
Hand-Gesture-Controlled-Rhythm-Game/
├── main.py                       # Entry point – menu + game launcher
├── GameLoop.py                   # Main game loop, rendering, collision
├── audio.py                      # BPM detection, music loading, playback
├── config.py                     # Centralised settings (Singleton)
├── score_manager.py              # High‑score persistence (JSON)
├── hand_tracking/
│   ├── __init__.py
│   ├── Tracking.py               # HandTracker class (Singleton)
│   ├── HandGesture.py            # Open palm detection, index finger recognition
│   └── HelperFunctions.py        # Landmark conversion, distance calculation
├── requirements.txt
├── scores.json                   # Auto‑generated high score file
└── README.md
```

---

## OOP Implementation

The project demonstrates all four pillars of object‑oriented programming:

### 1. Encapsulation
- `GameObject` bundles position, size, colour, speed, and collision methods.  
- `HandTracker` hides the complexity of MediaPipe pipeline and camera access.  
- `ScoreManager` manages file I/O and score updates with a clean public interface.

### 2. Abstraction
- `GameObject` is an abstract base class – tiles and burst groups inherit from it.  
- `HandGesture` provides an `is_open_palm()` method without exposing landmark comparison details.

### 3. Inheritance
- `Tile` and `BurstTileGroup` inherit from `GameObject`, reusing physics and rendering methods while adding their own behaviour (e.g., burst effects).

### 4. Polymorphism
- Different collision checks: `point_collision()` for index fingertip vs tile; `aabb_collision()` for open palm detection area.  
- Overridden `update()` methods for normal tiles (fall linearly) and burst tiles (wiggle effect).

---

## Design Patterns

| Pattern | Implementation | Why |
|---------|----------------|-----|
| **Singleton** | `GameConfig`, `HandTracker` | Only one configuration and one camera/MediaPipe instance. Prevents conflicts and saves resources. |
| **Factory** | `tile_generator(beat_index)` | Creates regular tiles or burst groups depending on the beat count. Encapsulates creation logic. |
| **Observer** | `ScoreManager` notifies UI on high score update | Loose coupling between scoring and display. |
| **Strategy** | Different fall speed calculation based on BPM | Allows easy swapping of rhythm algorithms. |

---

## Technical Documentation

### Hand Detection Pipeline
1. Capture frame with OpenCV → convert to RGB.  
2. MediaPipe Hands processes the frame → returns 21 landmarks per hand.  
3. Extract **index fingertip** (landmark 8) and all five fingertip landmarks (4, 8, 12, 16, 20) for gesture detection.  
4. Classify gesture:  
   - **Index pointing:** `(landmark8.y < landmark6.y)` and thumb not interfering.  
   - **Open palm:** all five tips above their respective PIP/MCP joints.  
5. Collision detection:  
   - For normal tiles: Euclidean distance between tile centre and **index fingertip** ≤ tile_radius + 15px.  
   - For burst tiles: if open palm detected, instantly mark all 5 burst tiles as caught.

### BPM Detection & Music Sync
- `librosa.load()` → `librosa.beat.beat_track()` returns tempo (BPM) and beat frames.  
- Beat timestamps are converted to game time.  
- A **beat counter** increments each time a beat occurs.  
- If `beat_counter % burst_interval == 0`, a `BurstTileGroup` is spawned; otherwise, a regular tile is spawned (random lane).  
- Tile falling speed: `base_speed = screen_height / (60 / BPM) * speed_multiplier`.

### Score Persistence
- `ScoreManager` loads/saves `scores.json` with a list of `{score, timestamp, song_name}`.  
- Only the top 10 scores are retained.

---

## Configuration

All settings are in `config.py` (Singleton). Modify to adjust:

```python
# Game settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 50
FALL_SPEED_MULTIPLIER = 0.8   # relative to BPM

# Burst settings
BEATS_PER_BURST = 8           # every N beats spawn 5-tile wave

# Gesture detection
INDEX_TIP_ID = 8
OPEN_PALM_THRESHOLD = 0.05    # landmark y‑difference

# Collision
CATCH_RADIUS = 25             # pixels from fingertip
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not found | Check `camera_index` in `config.py` (try 0, 1, 2). Ensure no other app uses the webcam. |
| BPM detection inaccurate | Use a song with a clear, steady beat. Adjust `librosa` parameters in `audio.py` (`hop_length`, `start_bpm`). |
| Tiles fall too fast/slow | Change `FALL_SPEED_MULTIPLIER` in `config.py`. |
| Index finger not recognised | Keep finger pointed upward, avoid curling. Improve lighting. |
| Open palm false triggers | Increase `OPEN_PALM_THRESHOLD` or require both hands to be open (configurable). |

---

## Future Enhancements

- 🔁 **Looping & playlists** – continuous play with multiple songs.  
- 📊 **Accuracy scoring** – “Perfect”, “Good”, “Miss” based on beat‑aligned catching.  
- 🎮 **Difficulty levels** – adjust burst frequency and fall speed multiplier.  
- 🌐 **Online leaderboards** – submit high scores to a global server.  
- 🎨 **Custom tile skins** – load your own graphics.

---

## Screenshots

<p align="center">
  <img src="https://github.com/user-attachments/assets/5ace5d50-d26a-484f-9009-5d900f89f459" width="80%"><br>
  <em>Main menu</em>

</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/e71a4454-4862-4878-ae4f-9714928bfe83" width="80%"><br>
  <em>5 burst tiles falling</em>

</p>

---

**Made with 🎵 and 🖐️** – enjoy the rhythm!
