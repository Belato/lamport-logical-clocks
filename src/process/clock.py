import threading


class LamportClock:
    """Relógio lógico de Lamport (L_i), thread-safe.

    Implementa exatamente as duas regras de atualização do algoritmo:
      - tick(): usado antes de um evento interno OU de um envio de mensagem.
                L_i = L_i + 1
      - update_on_receive(t_m): usado ao receber uma mensagem com timestamp t_m.
                L_j = max(L_j, t_m) + 1
    """

    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()

    def tick(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    def update_on_receive(self, received_timestamp: int) -> int:
        with self._lock:
            self._value = max(self._value, received_timestamp) + 1
            return self._value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value
