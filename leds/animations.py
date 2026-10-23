"""Animações puras: render(video_time, cfg) -> lista de (r, g, b) por LED.

Pixel 0 é a base da barra. Sem I/O, testável sem hardware.
Padrão vermelho; o azul sobe como uma onda leve, fica, e desce.
"""
import math
from dataclasses import dataclass

Color = tuple


@dataclass(frozen=True)
class AnimConfig:
    num_leds: int = 60
    rise_start: float = 12.0
    rise_duration: float = 6.0
    fall_start: float = 24.0
    fall_duration: float = 6.0
    blue: Color = (0, 90, 255)
    red: Color = (255, 0, 0)
    edge_softness: float = 6.0   # LEDs de gradiente na frente da onda
    wave_amplitude: float = 2.0  # ondulação da frente, em LEDs
    wave_length: float = 14.0    # comprimento da ondulação, em LEDs
    wave_speed: float = 0.6      # ciclos por segundo


def _clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _progress(t, start, duration):
    if duration <= 0:
        return 1.0 if t >= start else 0.0
    return _clamp01((t - start) / duration)


def _lerp(a, b, p):
    return tuple(a[i] + (b[i] - a[i]) * p for i in range(3))


def render(t, cfg):
    """Frame para o instante `t` (segundos do vídeo). Função só do tempo."""
    n = cfg.num_leds
    # fração de azul: 0 (tudo vermelho) -> 1 (tudo azul) -> 0
    wet = min(_progress(t, cfg.rise_start, cfg.rise_duration),
              1.0 - _progress(t, cfg.fall_start, cfg.fall_duration))

    # margem para a frente da onda sair totalmente da barra nos dois extremos
    margin = cfg.edge_softness + cfg.wave_amplitude
    level = -margin + wet * (n + 2 * margin)

    pixels = []
    for i in range(n):
        ripple = cfg.wave_amplitude * math.sin(
            2 * math.pi * (i / cfg.wave_length - cfg.wave_speed * t))
        cover = _clamp01((level - i + ripple) / cfg.edge_softness)
        pixels.append(_lerp(cfg.red, cfg.blue, cover))
    return pixels


def to_bytes(pixels):
    return bytes(max(0, min(255, int(round(v)))) for px in pixels for v in px)
