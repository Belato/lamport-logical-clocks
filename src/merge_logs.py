"""Gera a lista unificada de eventos (Requisito 3 do enunciado): lê os logs
de cada processo, ordena por Relógio Lógico e, em caso de empate, pelo ID do
processo (P1 < P2 < P3), e imprime a tabela final.

Uso (a partir de src/):
    python merge_logs.py
    python merge_logs.py --out unified_log.txt
"""

import argparse
import glob
import re

LOG_LINE_RE = re.compile(
    r"^\[Processo (?P<process_id>P\d+)\] Evento: (?P<event>\w+) \| "
    r"Relogio Logico: (?P<clock>\d+) \| Detalhes: (?P<details>.*)$"
)


def parse_logs(pattern: str):
    events = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8") as f:
            for line in f:
                match = LOG_LINE_RE.match(line.strip())
                if not match:
                    continue
                events.append(
                    {
                        "process_id": match.group("process_id"),
                        "event": match.group("event"),
                        "clock": int(match.group("clock")),
                        "details": match.group("details"),
                    }
                )
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pattern",
        default="process/logs/P*/P*.log",
        help="glob dos arquivos de log de cada processo (default: process/logs/P*/P*.log)",
    )
    parser.add_argument("--out", default=None, help="arquivo opcional para salvar a tabela unificada")
    args = parser.parse_args()

    events = parse_logs(args.pattern)
    # Desempate por ID do processo em caso de L_i == L_j (regra do enunciado).
    events.sort(key=lambda e: (e["clock"], e["process_id"]))

    lines = ["L\tProcesso\tEvento\tDetalhes"]
    for e in events:
        lines.append(f"{e['clock']}\t{e['process_id']}\t{e['event']}\t{e['details']}")

    output = "\n".join(lines)
    print(output)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output + "\n")


if __name__ == "__main__":
    main()
