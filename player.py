"""Toca videos em loop no VLC e anima os LEDs (WLED/DDP) em sincronia."""
import sys
import time
from pathlib import Path

import yaml

from leds.animations import AnimConfig, render, to_bytes
from leds.ddp import DDPSender

VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}


def load_config(path):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    anim = AnimConfig(
        **{**raw["cues"], **raw["leds"],
           "blue": tuple(raw["leds"]["blue"]), "red": tuple(raw["leds"]["red"])}
    )
    return raw, anim


class VideoClock:
    """Tempo do vídeo em segundos, interpolado entre as leituras (grossas) do VLC."""

    def __init__(self, player):
        self.player = player
        self.last_vt = 0.0
        self.last_mono = time.monotonic()

    def now(self):
        ms = self.player.get_time()
        mono = time.monotonic()
        if ms < 0:  # sem mídia
            self.last_vt, self.last_mono = 0.0, mono
            return 0.0
        vt = ms / 1000.0
        if vt != self.last_vt:
            self.last_vt, self.last_mono = vt, mono
        if self.player.is_playing():
            return self.last_vt + (mono - self.last_mono)
        return self.last_vt


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
    try:
        next_tick = time.monotonic()
        while True:
            pixels = render(clock.now(), anim)
            if raw.get("reverse"):
                pixels = pixels[::-1]
            sender.send(to_bytes(pixels) * raw["channels"])
            next_tick += period
            time.sleep(max(0.0, next_tick - time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        sender.send(bytes(anim.num_leds * 3 * raw["channels"]))  # apaga
        sender.close()
        lp.stop()


if __name__ == "__main__":
    main(*sys.argv[1:])
