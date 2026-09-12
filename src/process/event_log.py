import logging
import os
import threading

# Formato exigido pelo enunciado:
# [Processo P_i] Evento: <TIPO> | Relógio Lógico: L_i | Detalhes: <mensagem/info>
LOG_LINE = "[Processo {process_id}] Evento: {event_type} | Relogio Logico: {clock} | Detalhes: {details}"

_print_lock = threading.Lock()


def build_logger(process_id: str) -> logging.Logger:
    """Logger de arquivo dedicado ao processo (um arquivo por execução, como já
    era feito antes), mantido em paralelo ao stdout para facilitar o `docker
    compose logs`."""
    logs_dir = os.path.join("logs")
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(process_id)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.FileHandler(
            os.path.join(logs_dir, f"{process_id}.log"), encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

    return logger


def log_event(logger: logging.Logger, process_id: str, event_type: str, clock: int, details: str) -> None:
    """Registra um evento no formato padronizado, tanto no arquivo de log do
    processo quanto no stdout (com lock só para não intercalar linhas quando
    SEND/RECEIVE disparam de threads diferentes)."""
    line = LOG_LINE.format(process_id=process_id, event_type=event_type, clock=clock, details=details)
    with _print_lock:
        print(line, flush=True)
    logger.info(line)
