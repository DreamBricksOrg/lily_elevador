import unittest

from leds.animations import AnimConfig, render, to_bytes
from leds.ddp import build_packet

CFG = AnimConfig()
MID_RISE = CFG.rise_start + CFG.rise_duration / 2
HOLD = (CFG.rise_start + CFG.rise_duration + CFG.fall_start) / 2
END = CFG.fall_start + CFG.fall_duration + 1


class AnimTests(unittest.TestCase):
    def test_red_before_rise(self):
        self.assertTrue(all(p == CFG.red for p in render(0, CFG)))

    def test_rise_goes_bottom_up(self):
        f = render(MID_RISE, CFG)
        self.assertGreater(f[0][2], f[-1][2])  # base mais azul que o topo
        self.assertEqual(f[0], CFG.blue)
        self.assertEqual(f[-1], CFG.red)

    def test_never_off(self):
        for t in range(0, 60):
            for px in render(t, CFG):
                self.assertGreater(sum(px), 0)

    def test_full_blue_during_hold(self):
        self.assertTrue(all(p == CFG.blue for p in render(HOLD, CFG)))

    def test_fall_goes_top_down(self):
        f = render(CFG.fall_start + CFG.fall_duration / 2, CFG)
        self.assertEqual(f[-1], CFG.red)   # topo já voltou ao vermelho
        self.assertEqual(f[0], CFG.blue)   # base ainda azul

    def test_red_after_fall(self):
        self.assertTrue(all(p == CFG.red for p in render(END, CFG)))

    def test_front_is_gradient(self):
        f = render(MID_RISE, CFG)
        mixed = [p for p in f if p not in (CFG.red, CFG.blue)]
        self.assertGreater(len(mixed), 0)

    def test_loop_reset(self):
        self.assertTrue(all(p == CFG.red for p in render(0.5, CFG)))

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
