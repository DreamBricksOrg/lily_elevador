"""Animações puras: render(video_time, cfg) -> lista de (r, g, b) por LED.

Pixel 0 é a base da barra. Sem I/O, testável sem hardware.
Padrão vermelho; o azul sobe como uma onda leve, fica, e volta ao vermelho
por `fall_mode`: "wave" (desce em onda) ou "cut" (troca seca no fall_start).
"""
import math
from dataclasses import dataclass

Color = tuple

FALL_MODES = ("wave", "cut")


@dataclass(frozen=True)
class AnimConfig:
    num_leds: int = 60
    rise_start: float = 12.0
    rise_duration: float = 6.0
    fall_start: float = 24.0
    fall_duration: float = 6.0
    fall_mode: str = "wave"      # "wave" = desce em onda; "cut" = troca seca
    blue: Color = (0, 90, 255)
    red: Color = (255, 0, 0)
    edge_softness: float = 6.0   # LEDs de gradiente na frente da onda
    wave_amplitude: float = 2.0  # ondulação da frente, em LEDs
    wave_length: float = 14.0    # comprimento da ondulação, em LEDs
    wave_speed: float = 0.6      # ciclos por segundo

    def __post_init__(self):
        if self.fall_mode not in FALL_MODES:
            raise ValueError(f"fall_mode deve ser um de {FALL_MODES}, veio {self.fall_mode!r}")


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
    rise = _progress(t, cfg.rise_start, cfg.rise_duration)
    if cfg.fall_mode == "cut":
        fall_done = 1.0 if t >= cfg.fall_start else 0.0
    else:
        fall_done = _progress(t, cfg.fall_start, cfg.fall_duration)
    wet = min(rise, 1.0 - fall_done)

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
