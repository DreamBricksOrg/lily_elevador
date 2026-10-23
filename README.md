# lily_elevador

Playlist de vídeos em loop (VLC) com animação de LEDs (WS2811 via QuinLED/WLED) sincronizada por tempo do vídeo.

## Rodar

```
pip install -r requirements.txt   # no Pi: sudo apt install vlc
python player.py [config.yaml]
python -m unittest discover -s tests -t .
```

Coloque os vídeos em `videos/`. Ajuste tempos e duração das animações em `config.yaml` (iguais para todos os vídeos).

## Rede (Pi fornece a rede na eth0)

1. IP fixo no Pi (`/etc/dhcpcd.conf`):
   ```
   interface eth0
   static ip_address=192.168.50.1/24
   ```
2. Opcional, DHCP para a QuinLED: `sudo apt install dnsmasq` e em `/etc/dnsmasq.d/leds.conf`:
   ```
   interface=eth0
   dhcp-range=192.168.50.2,192.168.50.20,12h
   dhcp-host=<MAC_DA_QUINLED>,192.168.50.2
   ```
   Alternativa: fixar o IP 192.168.50.2 no próprio WLED (Config > WiFi/Ethernet).

## WLED (QuinLED)

- Config > LED Preferences: tipo WS281x (WS2811), 4 saídas de 60 LEDs cada (total 240), ordem de cor conforme suas fitas (RGB/GRB/BRG).
- Config > Sync Interfaces: habilitar DDP/realtime (porta 4048) em Receive.
- Se a fita ficar com cores trocadas, ajuste a ordem de cor no WLED, não no código.
- Se a água descer em vez de subir, `reverse: true` em `config.yaml`.

## Autostart (desktop labwc com autologin)

Em `~/.config/labwc/autostart`:
```
(sleep 5; cd /home/db/prj/lily_elevador && exec python3 player.py >> /tmp/lily.log 2>&1) &
```
Log em `/tmp/lily.log`. Para parar: `pkill -f player.py`.

## Como está configurado no Pi

- `dnsmasq` só como DHCP na eth0 (`/etc/dnsmasq.d/leds.conf`), reservando 192.168.50.2 para o MAC da QuinLED (`dhcp-host=<MAC>,192.168.50.2`). Se trocar a placa, troque o MAC.
- Tela na vertical (9:16): `~/.config/kanshi/config` com `output HDMI-A-1 enable mode 1920x1080@60Hz transform 90`. Se a imagem ficar de cabeça para baixo, use `transform 270` e `pkill -HUP -x kanshi`.
- WLED: 4 saídas WS281x (GPIO 16, 3, 1, 4) de 60 LEDs, 240 no total. Backup da config original em `~/wled-cfg-backup.json`.

## Estrutura

- `leds/animations.py`: `render(video_time, cfg)`, função pura do tempo (seek/loop não dessincronizam).
- `leds/ddp.py`: envio DDP/UDP.
- `player.py`: VLC + relógio interpolado + loop de 50 Hz.
