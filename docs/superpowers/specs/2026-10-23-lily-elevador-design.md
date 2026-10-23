# lily_elevador: design

Data: 2026-10-23

## Objetivo

Tocar uma playlist de vídeos em loop (VLC) e, em três pontos fixos do vídeo (iguais em todos os vídeos), disparar animações em LEDs endereçáveis.

## Hardware e software

- Raspberry Pi 4, placa QuinLED (WLED), LEDs WS2811.
- 4 canais, cada um com uma barra vertical de 60 LEDs. Os 4 canais têm o mesmo comportamento.
- Python e VLC (python-vlc).
- Rede ethernet direta Pi ↔ QuinLED. O Pi fornece a rede (eth0 com IP fixo 192.168.50.1, QuinLED em 192.168.50.2 via dnsmasq ou IP fixo no WLED).

## Arquitetura

```
player.py
 ├─ VideoPlayer  (python-vlc, playlist em loop)
 ├─ VideoClock   (get_time do VLC, interpolado entre leituras)
 ├─ animations   (render: tempo do vídeo -> pixels)
 └─ DDPSender    (UDP :4048 -> WLED)
```

- Protocolo: DDP sobre UDP. Um frame de 60 LEDs (180 bytes) é repetido 4 vezes, totalizando 720 bytes, que cabem em um datagrama. No WLED, as 4 saídas formam um strip de 240 LEDs.
- Taxa: 50 Hz.
- Sincronia: o frame é função apenas do tempo atual do vídeo, sem timers próprios. Seek, pulo para o próximo vídeo e loop não dessincronizam, e voltar ao início do vídeo reinicia a sequência.

## Animações

Os LEDs nunca apagam: o padrão é vermelho estático. Pixel 0 é a base da barra (`reverse: true` inverte).

| Fase | Início | Efeito |
|---|---|---|
| Vermelho | início do vídeo | vermelho estático |
| Subida | `rise_start` | o azul sobe da base ao topo como uma onda leve (frente em gradiente de `edge_softness` LEDs, com ondulação senoidal), cobrindo o vermelho |
| Azul | fim da subida até `fall_start` | tudo azul |
| Descida | `fall_start` | o azul desce do topo à base, revelando o vermelho |
| Vermelho | fim da descida | vermelho estático até o fim do vídeo |

## Configuração (`config.yaml`)

- `videos_dir`, `wled_host`, `fps`, `channels`, `reverse`.
- `leds`: `num_leds` (60), `blue`, `red`, `edge_softness`.
- `cues`: `rise_start`, `rise_duration`, `fall_start`, `fall_duration`, comuns a todos os vídeos. O tempo parado em azul é a diferença entre `fall_start` e o fim da subida.
- `leds` também define `wave_amplitude`, `wave_length` e `wave_speed` da onda.

## Tratamento de erros

- Sem vídeos em `videos_dir`: encerra com mensagem.
- Sem mídia carregada: tempo 0, LEDs vermelhos.
- Ao encerrar (Ctrl+C): envia frame vermelho e para o VLC.
- UDP é sem conexão: se a QuinLED estiver fora do ar, o player continua rodando.

## Testes

Testes unitários (`unittest`) cobrem as animações como funções puras (vermelho antes da subida, subida de baixo para cima, LEDs nunca apagam, azul total no meio, descida de cima para baixo, vermelho no fim, frente em gradiente, reset no loop, tamanho do buffer) e o cabeçalho DDP. Não há teste automatizado de VLC nem de hardware.

## Fora de escopo

Cues diferentes por vídeo, marcadores embutidos no vídeo, firmware próprio na QuinLED.
