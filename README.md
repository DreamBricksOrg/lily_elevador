# lily_elevador

Playlist de vídeos em loop (VLC) com animação de LEDs (WS2811 via QuinLED/WLED) sincronizada por tempo do vídeo.

## Rodar

```
pip install -r requirements.txt   # no Pi: sudo apt install vlc
python player.py [config.yaml]
python -m unittest discover -s tests -t .
```

Os vídeos `video_elevador__v5_1.mp4`, `video_elevador__v5_2.mp4` e `video_elevador__v5_3.mp4` ficam em `videos/` e são tocados nessa ordem, em loop. Todos têm 30 fps e 27,7 s. Ajuste tempos e duração das animações em `config.yaml` (iguais para todos os vídeos). Os gatilhos aceitam segundos decimais. `0:00:05:02` vira `rise_start: 5.066667`, `0:00:12:21` marca o fim da subida em `12.7` s (`rise_duration: 7.633333`) e `0:00:24:21` vira `fall_start: 24.7`; o vídeo permanece mais 3 s com a tela vermelha.

Em `leds.length_m`, informe o comprimento real **de cada tira**, em metros. Em `leds.physical_leds_per_meter`, informe a densidade de LEDs físicos indicada para a fita. O programa divide por 3 porque cada chip WS2811 controla um grupo de 3 LEDs: com os 2,05 m e 60 LEDs físicos/m confirmados, cada tira tem 41 pixels endereçáveis. O mesmo quadro é enviado às 4 saídas.

`sync_offset_seconds` faz o ajuste fino da sincronia: valor positivo adianta os LEDs em relação ao vídeo; valor negativo atrasa. Comece em `0.0` e ajuste em passos pequenos, por exemplo `0.050`. O relógio interpola o tempo do VLC sem recuar em atualizações atrasadas e reinicia ao detectar seek ou loop.

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

- Config > LED Preferences: tipo WS281x (WS2811), 4 saídas com **o mesmo número de pixels endereçáveis** calculado acima. Configure 41 pixels por saída (total 164), em quatro faixas contíguas: 0–40, 41–81, 82–122, 123–163. A ordem de cor depende da fita (RGB/GRB/BRG).
- Config > Sync Interfaces: habilitar DDP/realtime (porta 4048) em Receive.
- Se a fita ficar com cores trocadas, ajuste a ordem de cor no WLED, não no código.
- Se a água descer em vez de subir, `reverse: true` em `config.yaml`.

## Autostart (desktop labwc com autologin)

Em `~/.config/labwc/autostart`:
```
(sleep 5; cd /home/db/prj/lily_elevador && exec python3 player.py >> /tmp/lily.log 2>&1) &
```
Log em `/tmp/lily.log`. Para reiniciar (depois de editar o `config.yaml` ou dar `git pull`): `./restart.sh`. Para parar: `pkill -f "^python3 player.py"`.

## Como está configurado no Pi

- `dnsmasq` só como DHCP na eth0 (`/etc/dnsmasq.d/leds.conf`), reservando 192.168.50.2 para o MAC da QuinLED (`dhcp-host=<MAC>,192.168.50.2`). Se trocar a placa, troque o MAC.
- Tela na vertical (9:16): `~/.config/kanshi/config` com `output HDMI-A-1 enable mode 1920x1080@60Hz transform 90`. Se a imagem ficar de cabeça para baixo, use `transform 270` e `pkill -HUP -x kanshi`.
- WLED ligado ao Pi: 4 saídas WS281x (GPIO 16, 3, 1, 4), com 41 pixels cada e inícios em 0, 41, 82 e 123 (164 no total). A configuração anterior de 60 pixels por saída foi preservada em um backup fora do repositório.

## Estrutura

- `leds/animations.py`: `render(video_time, cfg)`, função pura do tempo (seek/loop não dessincronizam).
- `leds/ddp.py`: envio DDP/UDP.
- `player.py`: VLC + relógio interpolado + loop de 50 Hz e compensação de latência configurável. No Pi, o VLC mantinha o último quadro por cerca de 27 s após o fim de cada arquivo; o player avança explicitamente ao fim da mídia.
