# Simulação dos Relógios Lógicos de Lamport

Implementação da Abordagem A do trabalho (sistemas distribuídos reais via gRPC
+ Docker). Três processos independentes (P1, P2, P3) simulam uma frota de
rastreamento veicular:

```
P1 (rastreador GPS) --SendLocation--> P2 (geofencing) --SendAlert--> P3 (monitoramento)
```

Toda a manutenção do relógio de Lamport (incrementar antes de EXEC/SEND,
anexar o timestamp na mensagem, aplicar `max(L_j, t_m) + 1` no recebimento)
está isolada em **interceptors gRPC** (`src/process/interceptors.py`) — os
métodos de negócio de cada processo nunca tocam no relógio diretamente.

## Requisitos de Ambiente

- Docker e Docker Compose (v2, `docker compose ...`).
- Alternativamente, para rodar sem Docker: Python 3.12+ e as dependências de
  `src/process/requirements.txt` (`grpcio`, `protobuf`, `grpcio-tools`).

## Como executar (Docker)

```bash
cd src
docker compose up --build
```

Isso sobe os 3 containers (`p3`, `p2`, `p1`, nessa ordem). Cada um imprime no
stdout e grava em `src/process/logs/<PID>/<PID>.log` uma linha por evento, no
formato exigido:

```
[Processo P1] Evento: EXEC | Relogio Logico: 1 | Detalhes: ...
```

O cenário roda uma única vez e termina sozinho (os processos continuam de pé
servindo gRPC; encerre com `docker compose down`).

Para gerar a lista unificada de eventos ordenada pelo relógio de Lamport
(com desempate por ID do processo), após a execução:

```bash
cd src
python merge_logs.py --out unified_log.txt
```

## Como executar sem Docker (3 terminais)

```bash
cd src/process
pip install -r requirements.txt

# terminal 1
PROCESS_ID=P3 GRPC_PORT=50053 python process.py

# terminal 2
PROCESS_ID=P2 GRPC_PORT=50052 PEER_ID=P3 PEER_HOST=localhost:50053 python process.py

# terminal 3
PROCESS_ID=P1 GRPC_PORT=50051 PEER_ID=P2 PEER_HOST=localhost:50052 \
  START_DELAY_SECONDS=1 GPS_DRIFT_SECONDS=-5 python process.py
```

## Variáveis de ambiente

| Variável              | Uso                                                              |
|-----------------------|-------------------------------------------------------------------|
| `PROCESS_ID`          | Identificador do processo (`P1`, `P2`, `P3`)                      |
| `PEER_ID`             | Id do processo de destino, se houver saída (`P2`, `P3`)           |
| `PEER_HOST`           | `host:porta` do destino (ex.: `p2:50051`)                         |
| `GRPC_PORT`           | Porta em que o servidor gRPC deste processo escuta (default 50051)|
| `START_DELAY_SECONDS` | Espera antes de iniciar o roteiro do cenário (default 2s)         |
| `GPS_DRIFT_SECONDS`   | Drift simulado do relógio físico do GPS de P1 (só ilustrativo)    |

## Estrutura

- `src/process/lamport.proto` — contrato gRPC do serviço `Tracker`.
- `src/process/clock.py` — `LamportClock` (tick / update_on_receive).
- `src/process/interceptors.py` — interceptors cliente/servidor que aplicam as
  regras de Lamport e logam SEND/RECEIVE.
- `src/process/process.py` — lógica de negócio e roteiro do cenário de cada
  processo (EXEC, e reação a SendLocation/SendAlert).
- `src/merge_logs.py` — gera a lista unificada de eventos ordenada por
  relógio lógico, com desempate por ID do processo.
