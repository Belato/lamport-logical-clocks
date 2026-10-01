# Simulação dos Relógios Lógicos de Lamport

Simulação de um ambiente distribuído composto por 3 processos independentes (P1, P2, P3), cada
um rodando em seu próprio container Docker e se comunicando via **gRPC**, implementando as regras
do **Algoritmo de Relógios Lógicos de Lamport**.

Um serviço adicional, **Logger**, coleta o log individual de cada processo e gera um log global
ordenado pelo timestamp de Lamport, com desempate por ID de processo (`P1 < P2 < P3`).

## Requisitos de Ambiente

- **Docker** e **Docker Compose v2** (comando `docker compose`, não `docker-compose`)
- **Python 3.10+** (para rodar o script `start.py`, que dispara o cenário de teste a partir do host)
- Dependências Python, listadas em [`src/requirements.txt`](src/requirements.txt):
  - `grpcio`
  - `protobuf`
  - `grpcio-tools`

## Estrutura do projeto

```
src/
├── docker-compose.yml       # orquestração dos 4 serviços (p1, p2, p3, logger)
├── requirements.txt         # dependências Python
├── start.py                 # dispara o cenário de teste e copia o log final para result/
├── script.sh / script.bat   # automatizam build + up + start.py + down
├── result/                  # log global copiado ao final da execução
├── rpc/                     # definições .proto e código gRPC gerado (_pb2.py / _pb2_grpc.py)
├── proccesses/
│   ├── process.py           # classe base Process (regras de Lamport, comum a P1/P2/P3)
│   ├── p1/                  # P1: inicia o cenário (ExecuteTestCase) e aciona o Logger
│   ├── p2/                  # P2
│   └── p3/                  # P3
└── logger/                  # serviço Logger: agrega e ordena os logs de P1/P2/P3
```

## Instruções
1. Crie e ative um ambiente virtual Python, e instale as dependências (necessário apenas para
   rodar o `start.py` fora dos containers):

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r src/requirements.txt
   ```

2. Suba os containers (a partir da pasta `src/`):

   ```bash
   cd src
   docker compose up -d --build
   ```

3. Aguarde todos os serviços ficarem `healthy`:

   ```bash
   docker compose ps
   ```

4. Dispare o cenário de teste (também a partir de `src/`):

   ```bash
   python start.py
   ```

5. Confira os resultados:
   - Log individual de cada processo: `src/proccesses/p1/logs/P1.log`, `p2/logs/P2.log`, `p3/logs/P3.log`
   - Log global ordenado por timestamp de Lamport: `src/logger/logs/output.log`
     (uma cópia é salva automaticamente em `src/result/output.log` pelo `start.py`)

6. Encerre os containers:

   ```bash
   docker compose down
   ```

## Como executar

O script executa todo os processos necessários para executar o caso de teste do sistema. Ele sobe os containers (buildando apenas se as imagens ainda não existirem), espera todos
ficarem saudáveis, dispara o cenário de teste e, ao final, derruba tudo automaticamente. Necesssita da utilização do ambiente virtual com as dependências instaladas, indicado sessão de instruções.

Para executar o script, é necessário que a execução seja disparada a partir da pasta `src/`:

```bash
# Linux / macOS / Git Bash no Windows
bash script.sh
```

```bat
:: Windows (cmd.exe ou PowerShell)
script.bat
```

Os resultados podem ser conferidos no diretório `src/result`, que contém o registro de log global:
   - Log global ordenado por timestamp de Lamport: `src/logger/logs/output.log`