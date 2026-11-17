import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from player import VideoClock, load_config


class ConfigTests(unittest.TestCase):
    def test_length_and_physical_led_density_determine_ws2811_pixels(self):
        config = {
            "leds": {
                "length_m": 2.05,
                "physical_leds_per_meter": 60,
                "blue": [0, 90, 255],
                "red": [255, 0, 0],
            },
            "cues": {
                "rise_start": 0.125,
                "rise_duration": 5.875,
                "fall_start": 20.25,
                "fall_duration": 4.5,
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            _, anim = load_config(path)

        self.assertEqual(anim.num_leds, 41)
        self.assertEqual(anim.rise_start, 0.125)
        self.assertEqual(anim.rise_duration, 5.875)
        self.assertEqual(anim.fall_start, 20.25)

    def test_invalid_strip_geometry_is_rejected(self):
        config = {
            "leds": {
                "length_m": 0,
                "physical_leds_per_meter": 60,
                "blue": [0, 90, 255],
                "red": [255, 0, 0],
            },
            "cues": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(yaml.safe_dump(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "length_m"):
                load_config(path)


class FakePlayer:
    def __init__(self, times):
        self.times = iter(times)

    def get_time(self):
        return next(self.times)

    def is_playing(self):
        return True


class VideoClockTests(unittest.TestCase):
    def test_coarse_vlc_update_does_not_move_clock_backwards(self):
        player = FakePlayer([1000, 1000, 1040])
        with patch("player.time.monotonic", side_effect=[100.0, 100.0, 100.08, 100.1]):
            clock = VideoClock(player)
            self.assertAlmostEqual(clock.now(), 1.0)
            self.assertAlmostEqual(clock.now(), 1.08)
            self.assertGreaterEqual(clock.now(), 1.1 - 1e-9)

    def test_seek_backwards_resets_video_time(self):
        player = FakePlayer([1000, 1000, 200])
        with patch("player.time.monotonic", side_effect=[100.0, 100.0, 100.08, 100.1]):
            clock = VideoClock(player)
            clock.now()
            clock.now()
            self.assertAlmostEqual(clock.now(), 0.2)


if __name__ == "__main__":
    unittest.main()
