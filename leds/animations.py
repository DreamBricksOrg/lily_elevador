"""Animações puras: render(video_time, cfg) -> lista de (r, g, b) por LED.

Pixel 0 é a base da barra. Sem I/O, testável sem hardware.
"""
from dataclasses import dataclass

Color = tuple


@dataclass(frozen=True)
class AnimConfig:
    num_leds: int = 60
    rise_start: float = 12.0
    rise_duration: float = 6.0
    fade_red_start: float = 20.0
    fade_red_duration: float = 2.0
    fade_out_start: float = 28.0
    fade_out_duration: float = 2.0
    blue: Color = (0, 90, 255)
    red: Color = (255, 0, 0)
    edge_softness: float = 4.0  # LEDs de gradiente na borda da água


def _clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _progress(t, start, duration):
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return _clamp01((t - start) / duration)


def _lerp(a, b, p):
    return tuple(a[i] + (b[i] - a[i]) * p for i in range(3))


def _scale(c, k):
    return tuple(v * k for v in c)


def _water(level, color, cfg):
    """Preenche de 0 até `level` (em LEDs), com borda suave no topo."""
    pixels = []
    for i in range(cfg.num_leds):
        # cobertura do LED i: 1 abaixo da borda, cai linear até 0
        cover = _clamp01((level - i) / max(cfg.edge_softness, 1e-6)) if level < cfg.num_leds else 1.0
        pixels.append(_scale(color, cover))
    return pixels


def render(t, cfg):
    """Frame para o instante `t` (segundos do vídeo). Função só do tempo."""
    n = cfg.num_leds
    if t < cfg.rise_start:
        return [(0, 0, 0)] * n

    rise_p = _progress(t, cfg.rise_start, cfg.rise_duration)
    # a água sobe até cobrir também a borda suave
    level = rise_p * (n + cfg.edge_softness)

    fade_p = _progress(t, cfg.fade_red_start, cfg.fade_red_duration)
    color = _lerp(cfg.blue, cfg.red, fade_p)

    out_p = _progress(t, cfg.fade_out_start, cfg.fade_out_duration)
    color = _scale(color, 1.0 - out_p)

    return _water(level, color, cfg)


def to_bytes(pixels):
    return bytes(max(0, min(255, int(round(v)))) for px in pixels for v in px)
