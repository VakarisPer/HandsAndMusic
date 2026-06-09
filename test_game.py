import json
import os
import tempfile
import unittest

import pygame

from GameLoop import (
    Catcher, GameObject, Tile, TileSpawner, MusicSpawner,
    drop_missed_tiles, handle_pointer_click, handle_open_palm,
    resolve_frame_score,
)
from config import GameConfig
from score_manager import ScoreManager


def make_frame_state():
    return {
        "lanes_clicked": set(),
        "lanes_caught": set(),
        "lanes_with_tiles": set(),
        "tiles_to_remove": [],
        "catch_positions": [],
    }


class TestGameObject(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.obj = Tile(1, pygame.math.Vector2(100, 100), (255, 0, 0), 100)
        self.obj.size = 30

    def test_point_collision_hit(self):
        self.assertTrue(self.obj.point_collision(100, 100, radius=50))

    def test_point_collision_miss(self):
        self.assertFalse(self.obj.point_collision(500, 500, radius=10))

    def test_display_size_with_click_effect(self):
        self.assertEqual(self.obj.display_size(), 30)
        self.obj.click_effect = 5
        self.assertEqual(self.obj.display_size(), 55)

    def test_object_deletion(self):
        obj_list = [self.obj]
        self.obj.list_ref = obj_list
        self.obj.delete()
        self.assertEqual(obj_list, [])


class TestInheritanceHierarchy(unittest.TestCase):
    def setUp(self):
        pygame.init()

    def test_tile_is_game_object(self):
        tile = Tile(3, pygame.math.Vector2(100, -50), (255, 0, 0), 105)
        self.assertIsInstance(tile, GameObject)
        self.assertEqual(tile.size, GameConfig.TILE_SIZE)
        self.assertEqual(tile.speed, 105)

    def test_catcher_is_game_object(self):
        catcher = Catcher(2, pygame.math.Vector2(200, 620))
        self.assertIsInstance(catcher, GameObject)
        self.assertEqual(catcher.lane_index, 2)
        self.assertEqual(catcher.speed, 0)
        self.assertEqual(catcher.pointer_armed, [True, True])

    def test_gameobject_is_abstract(self):
        with self.assertRaises(TypeError):
            GameObject("x", pygame.math.Vector2(0, 0), 10,
                       (0, 0, 0), 0, None)


class TestTileSpawner(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.lane_positions = [440, 540, 640, 740, 840]
        self.spawner = TileSpawner(1280, self.lane_positions)

    def test_sequential_pattern_walks_lanes(self):
        tiles = []
        for _ in range(5):
            self.spawner.spawn_tile(tiles, "sequential")
        lanes = [tile.position.x for tile in tiles]
        self.assertEqual(lanes, self.lane_positions)

    def test_tile_speed_is_fixed(self):
        tiles = []
        self.spawner.spawn_tile(tiles, "sequential")
        self.assertEqual(tiles[0].speed, GameConfig.TILE_SPEED)
        self.assertFalse(tiles[0].is_kick)

    def test_kick_tile_is_orange(self):
        tiles = []
        self.spawner.spawn_tile(tiles, "sequential", is_kick=True)
        self.assertTrue(tiles[0].is_kick)
        self.assertEqual(tiles[0].color, GameConfig.COLOR_ORANGE)
        self.assertEqual(tiles[0].speed, GameConfig.KICK_TILE_SPEED)

    def test_spawn_row_fills_every_lane(self):
        tiles = []
        self.spawner.spawn_row(tiles)
        self.assertEqual(len(tiles), 5)
        lanes = sorted(tile.position.x for tile in tiles)
        self.assertEqual(lanes, sorted(self.lane_positions))
        self.assertTrue(all(tile.is_burst for tile in tiles))
        self.assertTrue(all(tile.color == GameConfig.COLOR_BURST
                            for tile in tiles))

    def test_normal_tile_is_not_burst(self):
        tiles = []
        self.spawner.spawn_tile(tiles, "sequential")
        self.assertFalse(tiles[0].is_burst)

    def test_tile_update_moves_down(self):
        tiles = []
        self.spawner.spawn_tile(tiles, "sequential")
        start_y = tiles[0].position.y
        tiles[0].update(0.1)
        self.assertGreater(tiles[0].position.y, start_y)

    def test_golden_tile_flag_exists(self):
        tile = Tile(99, pygame.math.Vector2(500, 100), GameConfig.COLOR_GOLDEN,
                    200, is_golden=True)
        self.assertTrue(tile.is_golden)
        self.assertEqual(tile.color, GameConfig.COLOR_GOLDEN)


class TestMusicSpawner(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.lane_positions = [440, 540, 640, 740, 840]
        self.tile_spawner = TileSpawner(1280, self.lane_positions)
        self.music = MusicSpawner(self.tile_spawner, bpm=120,
                                  travel_time=2.0, beat_skip=1)

    def test_no_flood_at_song_start(self):
        tiles = []
        self.music.update(0.0, tiles, "sequential")
        self.assertLessEqual(len(tiles), 1)

    def test_spawning_continues_after_lead_in(self):
        tiles = []
        self.music.update(2.0, tiles, "sequential")
        self.assertEqual(len(tiles), 5)

    def test_beat_skip_drops_tiles(self):
        spawner = TileSpawner(1280, self.lane_positions)
        music = MusicSpawner(spawner, bpm=120, travel_time=2.0, beat_skip=2)
        tiles = []
        music.update(10.0, tiles, "sequential")
        self.assertGreater(len(tiles), 0)
        self.assertLess(len(tiles), 25)

    def test_burst_interval_spawns_full_row(self):
        spawner = TileSpawner(1280, self.lane_positions)
        music = MusicSpawner(spawner, bpm=120, travel_time=0.0,
                             beat_skip=1, burst_interval=4)
        tiles = []
        music.update(2.0, tiles, "sequential")
        self.assertEqual(len(tiles), 9)


class TestPointerDebounce(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = GameConfig()
        self.catcher = Catcher(0, pygame.math.Vector2(640, 600))
        self.catcher.list_ref = [self.catcher]
        self.center = (
            self.catcher.position.x + self.catcher.size / 2,
            self.catcher.position.y + self.catcher.size / 2,
        )

    def test_first_frame_inside_clicks(self):
        state = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], state, self.config)
        self.assertIn(0, state["lanes_clicked"])
        self.assertFalse(self.catcher.pointer_armed[0])

    def test_held_finger_does_not_reclick(self):
        state1 = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], state1, self.config)
        state2 = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], state2, self.config)
        self.assertNotIn(0, state2["lanes_clicked"])

    def test_releasing_rearms_for_next_click(self):
        s1 = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], s1, self.config)
        s2 = make_frame_state()
        handle_pointer_click((0, 0), 0,
                             [self.catcher], [], s2, self.config)
        self.assertTrue(self.catcher.pointer_armed[0])
        s3 = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], s3, self.config)
        self.assertIn(0, s3["lanes_clicked"])

    def test_two_hands_armed_independently(self):
        s = make_frame_state()
        handle_pointer_click(self.center, 0,
                             [self.catcher], [], s, self.config)
        self.assertFalse(self.catcher.pointer_armed[0])
        self.assertTrue(self.catcher.pointer_armed[1])
        s2 = make_frame_state()
        handle_pointer_click(self.center, 1,
                             [self.catcher], [], s2, self.config)
        self.assertIn(0, s2["lanes_clicked"])


class TestBurstRules(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = GameConfig()
        self.catcher = Catcher(0, pygame.math.Vector2(640, 600))
        self.center = (
            self.catcher.position.x + self.catcher.size / 2,
            self.catcher.position.y + self.catcher.size / 2,
        )

    def _tile_at_catcher(self, is_burst):
        return Tile(1, pygame.math.Vector2(640, 610),
                    GameConfig.COLOR_RED, 0,
                    list_ref=None, is_burst=is_burst)

    def test_pointer_ignores_burst_tile(self):
        tiles = [self._tile_at_catcher(is_burst=True)]
        state = make_frame_state()
        handle_pointer_click(self.center, 0, [self.catcher],
                             tiles, state, self.config)
        self.assertNotIn(0, state["lanes_caught"])

    def test_pointer_catches_normal_tile(self):
        tiles = [self._tile_at_catcher(is_burst=False)]
        state = make_frame_state()
        handle_pointer_click(self.center, 0, [self.catcher],
                             tiles, state, self.config)
        self.assertIn(0, state["lanes_caught"])

    def test_palm_ignores_normal_tile(self):
        tiles = [self._tile_at_catcher(is_burst=False)]
        state = make_frame_state()
        handle_open_palm([self.catcher], tiles, state,
                         screen_height=720, config=self.config)
        self.assertNotIn(0, state["lanes_caught"])

    def test_palm_catches_burst_tile(self):
        tiles = [self._tile_at_catcher(is_burst=True)]
        state = make_frame_state()
        handle_open_palm([self.catcher], tiles, state,
                         screen_height=720, config=self.config)
        self.assertIn(0, state["lanes_caught"])


class TestMissedTiles(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = GameConfig()

    def test_tile_off_bottom_is_dropped(self):
        tiles = []
        tile = Tile(1, pygame.math.Vector2(100, 800),
                    (255, 0, 0), 250, list_ref=tiles)
        tiles.append(tile)
        penalty, count = drop_missed_tiles(tiles, screen_height=720,
                                           config=self.config)
        self.assertEqual(tiles, [])
        self.assertEqual(penalty, self.config.POINTS_PER_MISS)
        self.assertEqual(count, 1)

    def test_tile_on_screen_is_kept(self):
        tiles = []
        tile = Tile(1, pygame.math.Vector2(100, 400),
                    (255, 0, 0), 250, list_ref=tiles)
        tiles.append(tile)
        penalty, count = drop_missed_tiles(tiles, screen_height=720,
                                           config=self.config)
        self.assertEqual(len(tiles), 1)
        self.assertEqual(penalty, 0)
        self.assertEqual(count, 0)


class TestScoreManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scores_file = os.path.join(self.temp_dir, "test_scores.json")
        self.manager = ScoreManager(self.scores_file)

    def tearDown(self):
        if os.path.exists(self.scores_file):
            os.remove(self.scores_file)
        os.rmdir(self.temp_dir)

    def test_add_and_persist(self):
        self.manager.add_score(100, "Player1")
        self.manager.add_score(200, "Player2")
        reloaded = ScoreManager(self.scores_file)
        self.assertEqual(len(reloaded.scores), 2)
        self.assertEqual(reloaded.scores[0]["score"], 200)

    def test_high_scores_limit(self):
        for i in range(10):
            self.manager.add_score(1000 - i * 10, f"Player{i}")
        top = self.manager.get_high_scores(5)
        self.assertEqual(len(top), 5)
        self.assertEqual(top[0]["score"], 1000)

    def test_clear_scores(self):
        self.manager.add_score(100, "Player1")
        self.manager.clear_scores()
        self.assertEqual(self.manager.scores, [])

    def test_missing_file_yields_empty(self):
        manager = ScoreManager(os.path.join(self.temp_dir, "missing.json"))
        self.assertEqual(manager.scores, [])

    def test_json_format_validity(self):
        self.manager.add_score(42, "TestPlayer")
        with open(self.scores_file) as f:
            data = json.load(f)
        self.assertIn("score", data[0])
        self.assertIn("player", data[0])
        self.assertIn("timestamp", data[0])


class TestCombo(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.config = GameConfig()

    def test_catch_increments_combo_and_scores_by_combo(self):
        catcher = Catcher(0, pygame.math.Vector2(640, 600))
        state = make_frame_state()
        state["lanes_clicked"].add(0)
        state["lanes_caught"].add(0)
        score, combo = resolve_frame_score([catcher], state, 0, 3, self.config)
        self.assertEqual(combo, 4)
        self.assertEqual(score, self.config.POINTS_PER_CATCH * 3)

    def test_bad_click_resets_combo(self):
        catcher = Catcher(0, pygame.math.Vector2(640, 600))
        state = make_frame_state()
        state["lanes_clicked"].add(0)
        state["lanes_with_tiles"].add(0)
        score, combo = resolve_frame_score([catcher], state, 10, 5,
                                           self.config)
        self.assertEqual(combo, 0)
        self.assertEqual(score, 10 - self.config.POINTS_PER_BAD_CLICK)

    def test_first_catch_with_combo_one(self):
        catcher = Catcher(0, pygame.math.Vector2(640, 600))
        state = make_frame_state()
        state["lanes_clicked"].add(0)
        state["lanes_caught"].add(0)
        score, combo = resolve_frame_score([catcher], state, 0, 1, self.config)
        self.assertEqual(combo, 2)
        self.assertEqual(score, self.config.POINTS_PER_CATCH * 1)


class TestGameConfig(unittest.TestCase):
    def test_singleton(self):
        self.assertIs(GameConfig(), GameConfig())

    def test_golden_tile_points(self):
        self.assertEqual(GameConfig.GOLDEN_TILE_POINTS, 200)

    def test_points_per_catch(self):
        self.assertEqual(GameConfig.POINTS_PER_CATCH, 10)


if __name__ == "__main__":
    unittest.main()
