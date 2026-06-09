"""Project entrypoint.

Flow: Menu -> GameApp -> Save Score -> Menu (loop)
"""

import pygame

from config import GameConfig
from score_manager import ScoreManager
from GameLoop import display_user_camera


def _release_camera():
    if hasattr(display_user_camera, 'tracker') and display_user_camera.tracker:
        display_user_camera.tracker.release()
        del display_user_camera.tracker


def main():
    config = GameConfig()
    score_manager = ScoreManager(config.SCORES_FILE)

    pygame.init()
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Hands & Music")

    from menu import run_menu

    while True:
        username, action = run_menu(screen, config, score_manager)

        if action == "exit":
            break

        if action == "start" and username:
            # Release menu's camera and pygame before launching game
            _release_camera()
            pygame.quit()

            from src.core.game_app import GameApp
            audio_file = config.AUDIO_FILE if config.AUDIO_FILE else None
            app = GameApp(audio_file=audio_file)
            score, max_combo = app.run(username)
            score_manager.add_score(score, username, max_combo)

            # Re-init pygame for menu
            pygame.init()
            screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            pygame.display.set_caption("Hands & Music")

    pygame.quit()


if __name__ == "__main__":
    main()
