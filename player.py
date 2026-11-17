"""Toca videos em loop no VLC e anima os LEDs (WLED/DDP) em sincronia."""
import sys
import time
import math
from pathlib import Path

import yaml

from leds.animations import AnimConfig, render, to_bytes
from leds.ddp import DDPSender

VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
PHYSICAL_LEDS_PER_PIXEL = 3  # WS2811: cada chip controla um grupo de 3 LEDs


def load_config(path):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    leds = raw["leds"].copy()
    length_m = float(leds.pop("length_m"))
    density = float(leds.pop("physical_leds_per_meter"))
    if not math.isfinite(length_m) or length_m <= 0:
        raise ValueError("leds.length_m deve ser maior que zero")
    if not math.isfinite(density) or density <= 0:
        raise ValueError("leds.physical_leds_per_meter deve ser maior que zero")
    num_pixels = round(length_m * density / PHYSICAL_LEDS_PER_PIXEL)
    if num_pixels < 1:
        raise ValueError("a fita deve conter pelo menos um pixel WS2811")
    leds["num_leds"] = num_pixels
    cues = raw["cues"].copy()
    for key in ("rise_start", "rise_duration", "fall_start", "fall_duration"):
        if key in cues:
            cues[key] = float(cues[key])
    anim = AnimConfig(
        **{**cues, **leds,
           "blue": tuple(leds["blue"]), "red": tuple(leds["red"])}
    )
    return raw, anim


class VideoClock:
    """Tempo do vídeo em segundos, interpolado entre as leituras (grossas) do VLC."""

    def __init__(self, player):
        self.player = player
        self.last_vt = None
        self.last_sample = None
        self.last_mono = time.monotonic()

    def now(self):
        ms = self.player.get_time()
        mono = time.monotonic()
        if ms < 0:  # sem mídia
            self.last_vt, self.last_sample, self.last_mono = None, None, mono
            return 0.0
        vt = ms / 1000.0
        if self.last_vt is None or not self.player.is_playing():
            self.last_vt, self.last_sample, self.last_mono = vt, vt, mono
            return vt
        estimated = self.last_vt + (mono - self.last_mono)
        if vt != self.last_sample:
            # Amostras grossas do VLC podem chegar atrasadas. Só reinicie o
            # relógio quando houver seek/loop ou um salto real para a frente.
            if vt < self.last_sample - 0.25 or vt > estimated + 0.25:
                estimated = vt
            else:
                estimated = max(estimated, vt)
            self.last_vt, self.last_sample, self.last_mono = estimated, vt, mono
        return estimated


def main(config_path="config.yaml"):
    import vlc

    raw, anim = load_config(config_path)
    videos = sorted(p for p in Path(raw["videos_dir"]).iterdir()
                    if p.suffix.lower() in VIDEO_EXT)
    if not videos:
        sys.exit(f"nenhum vídeo em {raw['videos_dir']}/")

    instance = vlc.Instance("--no-osd", "--mouse-hide-timeout=0")
    media_list = instance.media_list_new([str(p) for p in videos])
    lp = instance.media_list_player_new()
    lp.set_media_list(media_list)
    lp.set_playback_mode(vlc.PlaybackMode.loop)
    player = lp.get_media_player()
    player.set_fullscreen(True)
    lp.play()

    clock = VideoClock(player)
    sender = DDPSender(raw["wled_host"])
    period = 1.0 / raw["fps"]
    sync_offset = float(raw.get("sync_offset_seconds", 0.0))
    try:
        next_tick = time.monotonic()
        while True:
            pixels = render(clock.now() + sync_offset, anim)
            if raw.get("reverse"):
                pixels = pixels[::-1]
            try:
                sender.send(to_bytes(pixels) * raw["channels"])
            except OSError:
                pass  # QuinLED/cabo fora do ar: o vídeo segue tocando
            next_tick += period
            if next_tick < time.monotonic():
                next_tick = time.monotonic() + period
            time.sleep(max(0.0, next_tick - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sender.send(to_bytes(render(0, anim)) * raw["channels"])  # volta ao vermelho
        except OSError:
            pass
        sender.close()
        lp.stop()


if __name__ == "__main__":
    main(*sys.argv[1:])
