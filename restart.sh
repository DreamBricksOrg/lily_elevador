#!/bin/bash
# Reinicia o player (VLC + LEDs). Uso: ./restart.sh
cd "$(dirname "$(readlink -f "$0")")" || exit 1

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"

pkill -f "^python3 player.py"
for _ in $(seq 1 10); do
    pgrep -f "^python3 player.py" > /dev/null || break
    sleep 0.5
done

: > /tmp/lily.log
setsid -f python3 player.py >> /tmp/lily.log 2>&1 < /dev/null

sleep 4
if pgrep -f "^python3 player.py" > /dev/null; then
    echo "player rodando (log em /tmp/lily.log)"
else
    echo "player nao subiu:"
    tail -5 /tmp/lily.log
    exit 1
fi
