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

Hand Gesture-Controlled Rhythm Game is a real-time gesture recognition rhythm game that uses hand gestures detected via webcam to catch falling tiles on the screen. The game employs Google's MediaPipe for accurate hand detection and gesture recognition, combined with OpenCV for real-time video processing.

**Goal**: Catch as many falling tiles as possible by performing the correct hand gestures corresponding to each lane.

## Features

- **Real-time Hand Gesture Recognition**: Detects 5 distinct hand gestures:
  - Closed Fist
  - Open Palm
  - Pointing Up
  - Thumb Up
  - Victory Sign

- **Multi-hand Support**: Track and use both hands simultaneously

- **Dynamic Tile Spawning**: Multiple configurable spawn patterns (sequential, random, alternating, center-first, zigzag)

- **Visual Feedback**: 
  - Green feedback for successful catches
  - Red feedback for missed tiles
  - Finger position indicators (cyan for hand 0, magenta for hand 1)

- **Score Persistence**: Save and load high scores from JSON file

- **Configurable Settings**: Centralized game configuration (screen size, speeds, thresholds)

## Installation

### Prerequisites
- Python 3.8 or higher
- Webcam
- 200+ MB free disk space

### Setup

1. **Clone or download the project**
   ```bash
   cd Hand-Gesture-Controlled-Rhythm-Game
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

```bash
python main.py
```

The game window will open showing your webcam feed with hand tracking visualization and game tiles.

**To exit**: Press `Q` key or close the window

## How to Play

### Game Mechanics

1. **Watch the Screen**: Falling colored tiles will drop from the top of the screen toward 5 catcher positions at the bottom

2. **Perform Gestures**: Match each gesture to the corresponding lane:
   - **Lane 0 (Left)**: Closed Fist
   - **Lane 1**: Open Palm (activates ALL 5 catchers simultaneously)
   - **Lane 2 (Center)**: Pointing Up
   - **Lane 3**: Thumb Up
   - **Lane 4 (Right)**: Victory Sign

3. **Catch Tiles**: Position your hands so that:
   - Your index finger is within 40 pixels of a catcher
   - Perform the required gesture
   - The catcher will expand and catch nearby tiles

4. **Scoring**:
   - **+1 point**: Successfully catch a tile
   - **-1 point**: Click/gesture with available tiles but miss them
   - **No penalty**: Gesture with no tiles in range

### Tips

- **Open Palm Gesture**: Activates all 5 catchers at once, useful for catching multiple tiles or uncertain situations
- **Keep hands visible**: Ensure hands are well-lit and visible to the camera
- **Adjust camera angle**: Position camera at eye level for best tracking

## Project Structure

```
Hand-Gesture-Controlled-Rhythm-Game/
├── main.py                    # Entry point
├── GameLoop.py               # Main game logic and rendering
├── audio.py                  # Audio analysis and playback (optional)
├── config.py                 # Centralized configuration (Singleton)
├── score_manager.py          # Score persistence with file I/O
├── hand_tracking/
│   ├── __init__.py
│   ├── Tracking.py           # HandTracker class (Singleton)
│   ├── HandGesture.py        # Gesture recognition logic
│   └── HelperFunctions.py    # Utility functions
├── requirements.txt          # Project dependencies
├── scores.json              # High scores storage (auto-generated)
└── README.md                # This file
```

## OOP Implementation

This project demonstrates all 4 pillars of Object-Oriented Programming:

### 1. **Encapsulation**
- **GameObject class**: Encapsulates object properties (position, size, color, speed)
- **Private attributes**: `_instance` in Singleton patterns
- **Properties and methods**: Controlled access to internal state
- **Score Manager**: Encapsulates score management logic

**Example from GameLoop.py**:
```python
class GameObject:
    def __init__(self, name, position, size, color, speed, list_ref=None):
        self.name = name
        self.original_color = color  # Store original color
        self.feedback_color = None   # Color feedback state
        self.click_effect = 0        # Visual effect timer
    
    def point_collision(self, point_x, point_y, radius=30):
        """Check if a point (finger) collides with this object"""
        center_x = self.position.x + self.size / 2
        center_y = self.position.y + self.size / 2
        distance = (dx**2 + dy**2)**0.5
        return distance < (self.size / 2 + radius)
```

### 2. **Abstraction**
- **GameObject**: Abstract base for game entities (tiles, catchers)
- **HandTracker**: Abstracts camera and hand detection details
- **ScoreManager**: Abstracts file I/O and score management
- **Method interfaces**: `point_collision()`, `collision()`, `delete()` provide common interface

**Example from GameLoop.py**:
```python
def get_display_size(self):
    """Abstract calculation of display size with effects"""
    return self.size + (self.click_effect * 5)
```

### 3. **Inheritance**
- All game objects inherit from **GameObject**
- Tiles and catchers share common properties and methods
- **MusicSpawner** class could extend GameObject for advanced features

**Usage**:
```python
# Both tiles and catchers use the same GameObject base
tile = GameObject("tile_0", position, size, color, speed, tiles)
catcher = GameObject("catcher_0", position, size, white, 0, catchers)
```

### 4. **Polymorphism**
- **Multiple collision detection methods**: `point_collision()` vs `collision()`
- **Hand gesture recognition**: Different gestures behave differently (Pointing_Up vs Open_Palm)
- **Different tile colors and speeds**: Dynamic behavior based on type

**Example from GameLoop.py**:
```python
# Different collision checks for different scenarios
if catcher.point_collision(finger_x, finger_y, radius=40):  # Finger collision
    # ...
if catcher.collision(tile):  # Object collision
    # ...
```

## Design Patterns

### 1. **Singleton Pattern** (Configuration & Hand Tracking)
Ensures only one instance of critical resources:

```python
# config.py - GameConfig Singleton
class GameConfig:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Usage**: `config = GameConfig()` - always returns same instance
- **Why**: Prevents multiple game configurations or hand trackers
- **Benefit**: Centralized configuration, single camera resource

### 2. **Factory-like Pattern** (Tile Generation)
`tile_generator()` function creates objects based on pattern parameters:

```python
def tile_generator(tiles, screen, spawn_count, spawn_pattern):
    # Determines lane based on pattern
    if spawn_pattern == "sequential":
        lane_index = spawn_count % 5
    elif spawn_pattern == "alternating":
        lane_index = pattern_seq[spawn_count % 5]
    # Creates and adds new tile
    new_tile = GameObject(tile_name, position, size, color, speed)
    tiles.append(new_tile)
```

**Why**: Flexible object creation with different spawn patterns

### 3. **Composition Pattern** (Game Aggregation)
Game aggregates lists of objects:
- **Tiles list**: Game maintains collection of falling tiles
- **Catchers list**: Fixed set of 5 catching objects
- **ScoreManager**: Composed into main game loop

```python
# GameLoop maintains and manages collections
tiles = []
catchers = [GameObject(...) for i in range(5)]
score_manager = ScoreManager("scores.json")
```

**Why**: Clear separation of concerns, easier to manage complex systems

## Technical Documentation

### Hand Detection Pipeline

The hand tracking follows this pipeline:

1. **Capture Frame**: Read from webcam (cv2.VideoCapture)
2. **Detect Hands**: Process with MediaPipe Hands model
3. **Draw Landmarks**: Visualize hand keypoints
4. **Analyze Gestures**: Recognize gestures using landmark positions
5. **Extract Info**: Get finger positions and gesture names

**Classes**:
- `HandTracker` (hand_tracking/Tracking.py): Main tracking engine
- `recognize_hand_gesture()` (hand_tracking/HandGesture.py): Gesture recognition

### Gesture Recognition

Five gestures detected by analyzing finger extension states:

| Gesture | Condition |
|---------|-----------|
| Closed_Fist | No fingers extended |
| Open_Palm | All fingers extended |
| Pointing_Up | Only index extended |
| Thumb_Up | Only thumb extended |
| Victory | Index and middle extended |

**Detection Logic** (hand_tracking/HandGesture.py):
```python
index_extended = landmarks[8].y < landmarks[6].y  # Tip above middle joint
if index_extended and not any([thumb, middle, ring, pinky]):
    gesture_name = "Pointing_Up"
```

### Game Loop Architecture

**Main Loop** (GameLoop.py - Start() function):

```
while running:
    1. Clear screen
    2. Display camera feed
    3. Get hand gestures and finger positions
    4. Handle Open_Palm (special all-catchers gesture)
    5. Check pointer collision (hand 0)
    6. Check pointer collision (hand 1)
    7. Calculate feedback (green for catch, red for miss)
    8. Render tiles and catchers
    9. Update score display
    10. Generate new tiles on timer
    11. Render frame
```

### Score Persistence

Scores are stored in JSON format:

```json
[
  {
    "score": 42,
    "player": "Player",
    "timestamp": "2024-04-26T10:30:00.123456"
  }
]
```

**ScoreManager operations**:
- `add_score(score, player_name)`: Add and save new score
- `get_high_scores(limit)`: Retrieve top scores
- `clear_scores()`: Reset all scores

## Configuration

All game settings are defined in `config.py` using the Singleton pattern:

```python
config = GameConfig()

# Screen
config.SCREEN_WIDTH = 1280
config.SCREEN_HEIGHT = 720

# Gameplay
config.SPAWN_INTERVAL = 0.8
config.CATCHER_LANE_SPACING = 100

# Modify as needed
```

To change game settings, edit the constants in `GameConfig` class.

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pygame | 2.5.2 | Game rendering and window management |
| opencv-python | 4.8.1.78 | Video capture and image processing |
| mediapipe | 0.10.9 | Hand detection and landmark tracking |
| numpy | 1.24.3 | Numerical computations |
| librosa | 0.10.0 | Audio analysis (optional) |
| scipy | 1.11.3 | Signal processing (optional) |

## Troubleshooting

### Camera not detected
- Check webcam permissions
- Verify camera works in other applications
- Try different camera index in `Tracking.py`

### Poor gesture recognition
- Ensure good lighting
- Keep hands in camera view
- Adjust `HAND_DETECTION_CONFIDENCE` in config.py

### Low FPS
- Reduce screen resolution in config.py
- Reduce detection confidence
- Close other applications

## Future Enhancements

- Music-synchronized tile generation
- Difficulty levels
- Leaderboard with player names
- Multiple game modes
- Sound effects and music
- Tile patterns and types
- Performance metrics and statistics

## References

- [MediaPipe Hand Landmark Detection](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
- [OpenCV Documentation](https://docs.opencv.org)
- [Pygame Documentation](https://www.pygame.org)
- [Python OOP Principles](https://realpython.com/python3-object-oriented-programming/)

## Author

Created as an Object-Oriented Programming coursework project.

## License

This project is provided as-is for educational purposes.
