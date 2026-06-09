# Hands & Music — Project Changes Summary

## Overview

Transformed the project from a broken two-architecture codebase into a clean, working hand-gesture rhythm game with leaderboard, username support, and audio-synced gameplay.

---

## 1. Leaderboard System

**New features:**
- Persistent leaderboard displayed on the left side of the main menu
- Top 3 places styled with gold/silver/bronze colors and tinted backgrounds
- Shows rank, player name, score, and max combo for each entry
- Leaderboard persists to `scores.json` via `ScoreManager`

**Files changed:**
- `score_manager.py` — Added `max_combo` field to `add_score()`
- `menu.py` — Added `_draw_leaderboard()` function with gold/silver/bronze styling
- `config.py` — Added `LEADERBOARD_*` color constants

---

## 2. Username System

**New features:**
- Username input in Settings page (keyboard-based, no clash with hand gestures)
- Name persists in `GameConfig.USERNAME` across sessions
- Player name displayed on the main menu
- Saved with each score entry

**Files changed:**
- `config.py` — Added `USERNAME` field
- `menu.py` — Added `TextInput` widget class, integrated into `run_settings()`
- `main.py` — Passes `config.USERNAME` to `GameApp` and `ScoreManager`

---

## 3. UI Overhaul (Main Menu)

**Changes:**
- Rainbow-animated "Hands & Music" title with glow effect
- START button **disabled** (grayed out, unresponsive) when name or music is missing
- Persistent warning text above START showing what needs to be set
- Player/track info displayed with warning colors when not configured
- Leaderboard panel shrunk to 340x500 (was 420x600)
- Settings page now includes Volume slider, Username input, and Track browser

**Design decisions:**
- Settings → mouse + keyboard (no hand tracking interference)
- Main menu → hand gestures only (no text input)
- This separation prevents input conflicts

**Files changed:**
- `menu.py` — Complete rewrite of `run_menu()`, `run_settings()`, `Button` class
- `config.py` — Added `UI_BUTTON_DISABLED`, `USERNAME_INPUT_*`, `LEADERBOARD_*` constants

---

## 4. Button Disabled State

**New feature:**
- `Button` class now has `enabled` property
- Disabled buttons render in dim gray, no hover glow, no pulse
- `MenuButton.point_inside()` returns `False` when disabled — hand gestures ignored
- Enforced at both visual and interaction level

**File changed:**
- `menu.py` — `Button` and `MenuButton` classes

---

## 5. Architecture Cleanup

**Problem:** Two competing architectures existed:
1. Flat/legacy: `GameLoop.py`, `menu.py`, `config.py`, `score_manager.py`
2. Structured/new: `src/core/game_app.py`, `src/systems/*`, `src/config/settings.py`

**Solution:**
- **Removed then restored** the `src/` game engine (proper audio-synced gameplay)
- **Bridged** the menu/UI layer with the `src/` game engine via `main.py`
- Kept `GameLoop.py` as a utility module (camera display helpers used by menu)

**Clean architecture:**

```
main.py              → Orchestrator (menu ↔ game)
menu.py              → Menu UI, leaderboard, settings, username
GameLoop.py          → Camera/indicator helpers (used by menu)
config.py            → GameConfig singleton (UI settings)
score_manager.py     → Score persistence (scores.json)
audio.py             → Standalone charting tool (not used at runtime)
src/                 → Game engine
  core/game_app.py   → GameApp — main game orchestrator
  core/factory.py    → SystemFactory — creates game systems
  core/state_machine.py → Game state management
  systems/           → Spawn, scoring, timing, input, rendering
  audio/             → AudioClock — beat-synced playback
  vision/            → HandTrackerAdapter — wraps hand tracking
  config/settings.py → Frozen dataclass settings for game
  domain/models.py   → Note, ChartEvent, ScoreState, etc.
  io/session_store.py → Detailed results persistence
```

**Deleted files:**
- `test_game.py` — Referenced non-existent APIs from old GameLoop
- `OOP_COURSEWORK_DOCUMENTATION.md` — Coursework doc, not app code
- `particles.py` — Unused
- `data/` — Stale data from old architecture (auto-recreated if needed)
- `tests/` — Tests for deleted architecture

---

## 6. Game Engine Integration

**Bridged `GameApp` with the menu:**

- `GameApp.__init__()` accepts optional `audio_file` parameter
- `GameApp.run()` accepts `username` parameter and returns `(score, max_combo)`
- `SystemFactory.create_audio_clock()` accepts optional `audio_file` override
- `main.py` passes the menu-selected track to the game engine

**Files changed:**
- `src/core/game_app.py` — Modified `__init__` and `run()` signatures
- `src/core/factory.py` — Modified `create_audio_clock()` signature
- `main.py` — Complete rewrite to wire menu ↔ GameApp ↔ ScoreManager

---

## 7. Gameplay Improvements

**Combo system:**
- Combo increments on successful catches
- Combo resets on missed clicks/wrong gestures
- `max_combo` tracked per session
- Score and combo displayed on-screen during gameplay

**Exit handling:**
- `ESC` key exits game back to menu (was only window close)
- Camera properly released between menu and game sessions
- Pygame reinitialized cleanly between menu ↔ game transitions

**Files changed:**
- `GameLoop.py` — Added combo tracking, ESC exit, helper functions
- `main.py` — Camera release logic, pygame reinit cycle

---

## 8. Naming

- "RhythmForge" renamed to "Hands & Music" throughout:
  - `main.py` — Window captions
  - `menu.py` — Title text
  - `GameLoop.py` — Window caption

---

## 9. Bug Fixes

- Fixed `audio.py` — Removed dead `from src.config.settings import PROJECT` import
- Fixed `GameLoop.py` — Removed unused `import audio` causing startup crash
- Fixed `main.py` — Indentation errors on `set_caption` lines
- Fixed `display_user_camera` — Removed tracker argument mismatch
- Added `draw_finger_indicators()` and `to_screen_coordinates()` to `GameLoop.py`

---

## Runtime Flow

```
1. main.py
   ├── pygame.init()
   ├── Create GameConfig (Singleton)
   ├── Create ScoreManager
   └── Loop:
       ├── run_menu(screen, config, score_manager)
       │   ├── User: Settings → set name + track (mouse/keyboard)
       │   └── User: START with hand gesture
       ├── _release_camera() + pygame.quit()
       ├── GameApp(audio_file=config.AUDIO_FILE)
       │   └── app.run(config.USERNAME) → (score, max_combo)
       ├── score_manager.add_score(score, username, max_combo)
       └── pygame.init() → back to menu
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Settings uses mouse/keyboard | Avoids hand-gesture conflicts with text input |
| Main menu uses hand gestures | Immersive, no keyboard needed for navigation |
| START disabled when unconfigured | Clear UX: user knows exactly what to do |
| Two config systems coexist | Menu config (flat `config.py`) for UI, game config (frozen `src/config/settings.py`) for gameplay — no coupling |
| Camera released between sessions | Prevents webcam device conflicts |
| `data/` auto-created | `SessionStore.mkdir(parents=True, exist_ok=True)` |
