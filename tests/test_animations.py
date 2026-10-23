import unittest

from leds.animations import AnimConfig, render, to_bytes
from leds.ddp import build_packet

CFG = AnimConfig()


class AnimTests(unittest.TestCase):
    def test_off_before_first_cue(self):
        self.assertTrue(all(p == (0, 0, 0) for p in render(0, CFG)))

    def test_rise_goes_bottom_up(self):
        f = render(CFG.rise_start + CFG.rise_duration / 2, CFG)
        self.assertGreater(f[0][2], 0)
        self.assertEqual(f[-1], (0, 0, 0))
        self.assertGreaterEqual(f[0][2], f[30][2])

    def test_full_blue_at_end_of_rise(self):
        f = render(CFG.fade_red_start - 0.1, CFG)
        self.assertTrue(all(p == CFG.blue for p in f))

    def test_solid_red_after_fade(self):
        f = render(CFG.fade_red_start + CFG.fade_red_duration + 1, CFG)
        self.assertTrue(all(p == CFG.red for p in f))

    def test_fade_midpoint_is_mixed(self):
        r, g, b = render(CFG.fade_red_start + CFG.fade_red_duration / 2, CFG)[0]
        self.assertTrue(0 < r < 255 and 0 < b < 255)

    def test_off_after_fade_out(self):
        f = render(CFG.fade_out_start + CFG.fade_out_duration + 1, CFG)
        self.assertTrue(all(p == (0, 0, 0) for p in f))

    def test_loop_reset(self):
        self.assertEqual(render(0.5, CFG), render(0.0, CFG))

    def test_bytes_length(self):
        self.assertEqual(len(to_bytes(render(15, CFG))), 180)


class DDPTests(unittest.TestCase):
    def test_header(self):
        p = build_packet(b"\x01\x02\x03", seq=3, offset=0)
        self.assertEqual(p[0], 0x41)
        self.assertEqual(p[1], 3)
        self.assertEqual(int.from_bytes(p[8:10], "big"), 3)
        self.assertEqual(p[10:], b"\x01\x02\x03")


if __name__ == "__main__":
    unittest.main()
