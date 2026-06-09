# Hands & Music

<img width="962" height="542" alt="Screenshot 2026-06-09 163347" src="https://github.com/user-attachments/assets/e66ada72-23ec-4fbd-9445-1a445eb65f96" />

<img width="478" height="493" alt="Screenshot 2026-06-09 163359" src="https://github.com/user-attachments/assets/53c452e5-7565-4e76-b094-a6b6692d0a52" />

Hand gesture-controlled rhythm game using MediaPipe + OpenCV + Pygame + Robotika pixel font.

Catch falling tiles by pointing your fingers at the correct lane, trigger burst rows with Open Palm, and score big with golden tiles. Features real-time hand tracking, animated combo scoring, particle effects, a persistent leaderboard, and a built-in **manual level editor** for creating your own beatmaps.

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Requires Python 3.8+, a webcam, and a microphone/speakers.

---

## Gameplay

### Two Game Modes

| Mode | How it works |
|------|-------------|
| **Random (Auto)** | Tiles auto-generated from BPM analysis. Select any `.mp3`/`.wav` file in Settings. |
| **Manual Level** | Play a level you recorded yourself. Tiles hit exactly on your tapped beats — perfectly synced to the music. |

### Controls

| Input | Action |
|-------|--------|
| Point finger at a catcher | Activate lane, catch tiles |
| Open Palm gesture | Catch all 5 lanes (burst rows) |
| `ESC` | Exit game back to menu |
| Keys `1-5` | Keyboard lane catch (fallback) |

### Scoring

| Action | Points |
|--------|--------|
| Catch at combo 1 | +10 |
| Catch at combo 5 | +50 |
| Golden tile | +200 bonus |
| Miss / bad click | -5 |

Combo multiplies per-lane: `points = 10 × combo`. Golden tiles spawn randomly (6% chance) with a pulsing gold glow — catch them for a massive 200-point bonus.

### Visual Effects
- **Particles** burst on every catch — golden tiles get 2x gold + glow particles
- **Animated HUD** — score bounces on change, combo cycles rainbow colors
- **Receptor glow** — green on catch, red on miss
- **Golden tile glow** — pulsing aura effect

---

## Menu & Leaderboard

| Feature | Details |
|---------|---------|
| **Leaderboard** | Left side of main menu, top 10 scores with gold/silver/bronze styling |
| **Username** | Set in Settings, displays on menu and saves with scores |
| **Disabled START** | Button grays out until name + music/level are configured |
| **Rainbow title** | Animated "Hands & Music" title with glow |

---

## Creating Manual Levels

1. Open **Settings → RECORD LEVEL**
2. Click **BROWSE** to pick an audio file
3. Enter a **level name**
4. Click **START RECORDING** — the song plays
5. Tap keys `1-5` on the beat, `0` for a full 5-lane chord, `U` to undo
6. Press `Q` to save — chart saved to `levels/<name>.json`

Back in Settings, click the level name to select it. The main menu shows `Level: <name>` and the level's original audio plays automatically. Click again to deselect and return to **Random (Auto)** mode.

---

## Project Structure

```
HandsAndMusic/
├── main.py                 # Entry point — menu ↔ game orchestration
├── menu.py                 # Menu UI, leaderboard, settings, recording flow
├── GameLoop.py             # Camera display helpers for menu
├── config.py               # GameConfig singleton — all UI/game settings
├── score_manager.py        # Score persistence to scores.json
├── audio.py                # Standalone chart creator (python audio.py song.mp3)
├── particles.py            # Particle system for catch effects
├── hand_tracking/          # Hand gesture recognition (MediaPipe)
│   ├── Tracking.py         # HandTracker — webcam + detection pipeline
│   ├── HandGesture.py      # 5-gesture classifier from landmarks
│   └── HelperFunctions.py  # Distance math utilities
├── src/                    # Game engine
│   ├── core/
│   │   ├── game_app.py     # GameApp — main game loop orchestrator
│   │   ├── factory.py      # SystemFactory — creates all subsystems
│   │   └── state_machine.py # Game state (PLAYING / PAUSED / RESULTS)
│   ├── systems/
│   │   ├── render_system.py # Pygame rendering + animated HUD
│   │   ├── scoring_system.py # Combo-based scoring
│   │   ├── spawn_system.py  # Note spawning from charts
│   │   ├── chart_generator.py # Auto chart generation from BPM
│   │   ├── beat_grid.py     # Beat timeline from BPM
│   │   ├── timing_judge.py  # Hit accuracy classification
│   │   └── input_system.py  # Gesture/keyboard → lane mapping
│   ├── audio/
│   │   └── audio_clock.py  # Song playback clock
│   ├── vision/
│   │   └── hand_tracker_adapter.py # HandTracker wrapper
│   ├── config/
│   │   └── settings.py     # Frozen dataclass game settings
│   ├── domain/
│   │   └── models.py       # Note, ChartEvent, ScoreState, etc.
│   └── io/
│       └── session_store.py # Results & calibration persistence
├── fonts/                  # RobotikaPixelGreek.otf
├── audio/                  # Default audio files
├── music/                  # Music files
├── levels/                 # Saved manual levels (auto-created)
├── data/                   # Runtime data (results, calibration)
├── tests/                  # Unit tests
└── requirements.txt        # Python dependencies
```

---

## Recognized Gestures

| Gesture | Description |
|---------|-------------|
| Pointing_Up | Only index finger extended |
| Thumb_Up | Only thumb extended |
| Victory | Index + middle extended |
| Open_Palm | All 5 fingers extended |
| Closed_Fist | No fingers extended |
| None | Unknown/transitional |

---

## Configuration

Edit `config.py` for UI settings (colors, volume, layout, particle count, golden tile chance).

Edit `src/config/settings.py` for game engine settings (BPM, timing windows, lane count, spawn offset).

---

## Dependencies

```
pygame==2.5.2
opencv-python==4.8.1.78
mediapipe==0.10.9
numpy==1.24.3
librosa==0.10.0
scipy==1.11.3
```
