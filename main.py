"""Project entrypoint.

Flow: Menu -> GameApp -> Save Score -> Menu (loop)
"""

import pygame

from src.config.settings import GameConfig
from src.io.score_manager import ScoreManager
from src.ui.camera_overlay import release_camera_tracker


def main():
    config = GameConfig()
    score_manager = ScoreManager(config.SCORES_FILE)

    pygame.init()
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
        pygame.RESIZABLE | pygame.SCALED)
    pygame.display.set_caption("Hands & Music")

    from src.ui.menu import run_menu

    while True:
        username, action = run_menu(screen, config, score_manager)

        if action == "exit":
            break

        if action == "start" and username:
            release_camera_tracker()
            pygame.quit()

            from src.core.game_app import GameApp
            audio_file = config.AUDIO_FILE if config.AUDIO_FILE else None
            app = GameApp(audio_file=audio_file,
                          level_name=config.SELECTED_LEVEL,
                          volume=config.MUSIC_VOLUME)
            score, max_combo = app.run(username)
            score_manager.add_score(score, username, max_combo)

            pygame.init()
            screen = pygame.display.set_mode(
                (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                pygame.RESIZABLE | pygame.SCALED)
            pygame.display.set_caption("Hands & Music")

    pygame.quit()


if __name__ == "__main__":
    main()
