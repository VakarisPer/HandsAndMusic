# Hands & Music

Hand gesture-controlled rhythm game using MediaPipe + OpenCV + Pygame.

Catch falling tiles by pointing your fingers at the correct lane. Features real-time hand tracking, combo scoring, and a persistent leaderboard.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.8+ and a webcam.

## Controls

| Input | Action |
|-------|--------|
| Point finger at a catcher | Activate lane, catch tiles |
| Open Palm gesture | Activate all 5 lanes at once |
| `ESC` | Exit game back to menu |

## Project Structure

```
HandsAndMusic/
├── main.py                 # Entry point - menu/game loop orchestration
├── menu.py                 # Menu, leaderboard, username input, settings
├── GameLoop.py             # Core game logic, rendering, collision detection
├── config.py               # GameConfig singleton - all settings
├── score_manager.py        # Score persistence (JSON)
├── audio.py                # Audio playback and charting
├── hand_tracking/          # Hand gesture recognition
│   ├── Tracking.py         # HandTracker - webcam + MediaPipe pipeline
│   ├── HandGesture.py      # Gesture classification from landmarks
│   └── HelperFunctions.py  # Math utilities
├── fonts/                  # UI fonts
├── audio/                  # Audio files
├── music/                  # Music files
└── requirements.txt        # Python dependencies
```

## Recognized Gestures

- **Closed_Fist** - Lane 0
- **Open_Palm** - Lane 1 (also activates all lanes)
- **Pointing_Up** - Lane 2
- **Thumb_Up** - Lane 3
- **Victory** - Lane 4

## Leaderboard

Scores persist to `scores.json`. The menu displays top scores with gold/silver/bronze styling for 1st/2nd/3rd place. Each entry stores score, player name, and max combo.

## Configuration

Edit `config.py` to customize tile speed, spawn interval, spawn pattern, colors, and more.
