# Hand Gesture-Controlled Rhythm Game

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [How to Play](#how-to-play)
- [Project Structure](#project-structure)
- [OOP Implementation](#oop-implementation)
- [Design Patterns](#design-patterns)
- [Technical Documentation](#technical-documentation)

## Overview
Hand Gesture-Controlled Rhythm Game is a real-time gesture recognition rhythm game that uses your webcam to detect hands. Catch falling tiles by touching them with the fingertips of an open palm – no extra gestures needed.

**Goal**: Catch as many falling tiles as possible by touching them with your fingertips while holding an **Open Palm**.

## Features
- **One Gesture Only – Open Palm**  
  Keep your hand open (all fingers extended) to catch tiles. No other gestures are required.
- **Fingertip Collision System**  
  Each fingertip acts as an independent catcher. When a fingertip touches a falling tile, the tile is captured instantly.
- **Catch Up to 5 Tiles at Once**  
  With all five fingers extended, you can snatch up to 5 tiles simultaneously.
- **Real-time Hand Tracking**  
  Powered by Google MediaPipe for accurate detection of hand landmarks.
- **Visual Feedback**  
  Tiles flash green when caught, red when missed.
- **Score Persistence**  
  High scores are saved to a JSON file automatically.

## Installation
### Prerequisites
- Python 3.8 or higher
- A webcam
- 200+ MB free disk space

### Setup
1. **Clone or download the project**
   ```bash
   cd Hand-Gesture-Controlled-Rhythm-Game
   ```
2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## How to Run
```bash
python main.py
```
The game window opens, displaying your webcam feed with hand tracking and falling tiles.

**To exit**: Press `Q` or close the window.

## How to Play
### Core Mechanic
- **Hold an Open Palm** – extend all five fingers (thumb, index, middle, ring, pinky).  
- **Touch the falling tiles** with your fingertips to catch them.
- Each fingertip can catch one tile at a time, so you can grab up to 5 tiles simultaneously.

### What You See
- Coloured tiles fall from the top of the screen.
- Cyan (hand 0) / Magenta (hand 1) dots mark your fingertip positions.
- A caught tile flashes green; a missed tile flashes red and disappears.

### Scoring
- **+1 point** – tile successfully touched by a fingertip.
- **-1 point** – tile falls off the screen without being caught (when your hand could have reached it).
- **No penalty** for empty gestures.

### Tips
- Keep your palm facing the camera with fingers clearly separated.
- Ensure good lighting so MediaPipe can detect all five fingers.
- Position yourself at a comfortable distance – you don't need to stretch far.

## Project Structure
```
Hand-Gesture-Controlled-Rhythm-Game/
├── main.py                    # Entry point
├── GameLoop.py                # Main game logic and rendering
├── audio.py                   # Audio analysis and playback (optional)
├── config.py                  # Centralized configuration (Singleton)
├── score_manager.py           # Score persistence with file I/O
├── hand_tracking/
│   ├── __init__.py
│   ├── Tracking.py            # HandTracker class (Singleton)
│   ├── HandGesture.py         # Gesture recognition (Open Palm detection)
│   └── HelperFunctions.py     # Utility functions
├── requirements.txt
├── scores.json               # High scores storage (auto-generated)
└── README.md
```

## OOP Implementation
This project demonstrates all 4 pillars of Object-Oriented Programming:

### 1. **Encapsulation**
- **GameObject class**: Encapsulates object properties (position, size, colour, speed).
- **Private attributes**: `_instance` in Singleton patterns.
- **Score Manager**: Encapsulates score loading/saving logic.

### 2. **Abstraction**
- **GameObject**: Abstract base for tiles and other entities.
- **HandTracker**: Hides the complexity of MediaPipe and camera handling.
- **ScoreManager**: Provides a clean interface for score persistence.

### 3. **Inheritance**
- All game objects inherit from **GameObject** (e.g. tiles share common physics and rendering).

### 4. **Polymorphism**
- Different collision detection methods: `point_collision()` for fingertips vs. tile boundaries.
- Tile colour and speed vary dynamically based on type.

## Design Patterns
### 1. **Singleton Pattern**
- **GameConfig**: Only one configuration instance.
- **HandTracker**: Single camera and MediaPipe pipeline.
- **Why**: Prevents duplicate resources and centralises control.

### 2. **Factory-like Pattern**
- `tile_generator()` spawns tiles with random lane positions and properties.
- **Why**: Flexible creation of diverse falling objects.

### 3. **Composition Pattern**
- The game loop manages collections: `tiles`, `score_manager`, etc.
- **Why**: Clear separation of responsibilities.

## Technical Documentation
### Hand Detection Pipeline
1. Capture webcam frame with OpenCV.
2. Process frame with MediaPipe Hands.
3. Extract fingertip positions (landmarks 4, 8, 12, 16, 20).
4. Recognise **Open Palm** gesture: all five fingers extended.
5. Check fingertip collision with each tile.
6. Update score and remove caught tiles.

### Gesture Recognition
Only one gesture is used – **Open Palm**. It is detected when:
- Thumb tip (landmark 4) is to the right/above the thumb IP joint.
- Index, middle, ring, and pinky tips are above their respective PIP joints.
```python
thumb_extended = landmarks[4].x > landmarks[3].x  # adjusted for left/right hand
index_extended = landmarks[8].y < landmarks[6].y
# … similarly for other fingers
if thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended:
    gesture = "Open_Palm"
```

### Fingertip Collision
Instead of fixed catchers, each fingertip acts as a catcher with a collision radius of **30 pixels**.  
When the distance between a tile’s centre and a fingertip is less than `tile_size/2 + radius`, the tile is caught.

### Score Persistence
High scores are saved in `scores.json` using the `ScoreManager` class (JSON format).

## Configuration
All settings are in `config.py` (Singleton). Modify to adjust:
- Screen dimensions
- Tile speed and spawn intervals
- Collision radius
- MediaPipe detection confidence

## Dependencies
| Package      | Purpose                              |
|--------------|--------------------------------------|
| pygame       | Game engine and rendering           |
| opencv-python| Webcam capture and image processing |
| mediapipe    | Hand landmark detection             |
| numpy        | Numerical computations              |
| librosa      | Audio analysis (optional)           |
| scipy        | Signal processing (optional)        |

## Troubleshooting
- **Camera not detected** – check permissions or try another camera index.
- **Fingertips not recognised** – improve lighting and keep fingers separated.
- **Low FPS** – reduce screen resolution or detection confidence.

## Future Enhancements
- Music‑synchronised tile spawning
- Difficulty levels
- Online leaderboard
- Multiple game modes

## Photos


Hands
<img width="795" height="823" alt="Screenshot 2026-04-26 162724" src="https://github.com/user-attachments/assets/cd2ac3a9-7b90-4ac7-88c6-cd97e0597fc9" /><img width="648" height="745" alt="Screenshot 2026-04-26 162737" src="https://github.com/user-attachments/assets/1d6c053e-25fc-40be-b532-e2ebcc9f9f41" />

Pressing the cather
<img width="870" height="707" alt="Screenshot 2026-04-26 162748" src="https://github.com/user-attachments/assets/7ccefa4c-9bb1-46ab-af43-773e5e7e8965" />

Main menu
<img width="1710" height="869" alt="Screenshot 2026-04-26 162829" src="https://github.com/user-attachments/assets/5ace5d50-d26a-484f-9009-5d900f89f459" />

5 tiles at once
<img width="970" height="378" alt="Screenshot 2026-04-26 162759" src="https://github.com/user-attachments/assets/a4628259-e8cf-4540-9447-53445cad439f" />

Overall gameplay
<img width="2407" height="1422" alt="Screenshot 2026-04-26 162700" src="https://github.com/user-attachments/assets/e71a4454-4862-4878-ae4f-9714928bfe83" />




