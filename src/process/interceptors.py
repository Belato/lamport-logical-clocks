"""Interceptors gRPC responsáveis por TODA a manutenção do relógio de Lamport.

A ideia central: os métodos de negócio (SendLocation/SendAlert) nunca tocam no
relógio diretamente. Isso é feito de forma transversal:

  - LamportClientInterceptor: intercepta toda chamada unária de SAÍDA
    (cliente -> peer). Antes de a mensagem sair, incrementa o relógio local
    (L_i = L_i + 1) e anexa esse valor como timestamp no corpo da mensagem
    (regras 1 e 2 do enunciado), além de logar o evento SEND.

  - LamportServerInterceptor: intercepta toda chamada unária de ENTRADA
    (peer -> este processo). Antes do handler da RPC rodar, atualiza o
    relógio local para max(L_j, t_m) + 1 (regra 3) e loga o evento RECEIVE.
    Só depois disso o handler de negócio é executado.
"""

import grpc

from event_log import log_event


def _describe_location(request) -> str:
    return (
        f"LOC vehicle={request.vehicle_id} lat={request.lat:.4f} lon={request.lon:.4f} "
        f"(gps_time físico={request.gps_time:.3f}, ignorado pelo algoritmo)"
    )


def _describe_alert(request) -> str:
    return f"ALERTA_GEOFENCE veiculo={request.vehicle_id} motivo='{request.reason}'"


_DESCRIBERS = {
    "LocationUpdate": _describe_location,
    "GeofenceAlert": _describe_alert,
}


def _describe(request) -> str:
    describer = _DESCRIBERS.get(request.DESCRIPTOR.name)
    return describer(request) if describer else str(request)


class LamportClientInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, clock, process_id, peer_id, logger):
        self._clock = clock
        self._process_id = process_id
        self._peer_id = peer_id
        self._logger = logger

    def intercept_unary_unary(self, continuation, client_call_details, request):
        # Regra 1: incrementa o relógio antes de enviar a mensagem.
        new_clock = self._clock.tick()
        # Regra 2: anexa o timestamp lógico atual ao corpo da mensagem.
        request.timestamp = new_clock
        request.origin = self._process_id

        details = f"enviado para {self._peer_id}: {_describe(request)} (t={new_clock})"
        log_event(self._logger, self._process_id, "SEND", new_clock, details)

        return continuation(client_call_details, request)


class LamportServerInterceptor(grpc.ServerInterceptor):
    def __init__(self, clock, process_id, logger):
        self._clock = clock
        self._process_id = process_id
        self._logger = logger

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        original = handler.unary_unary

        def wrapped(request, context):
            # Regra 3: L_j = max(L_j, t_m) + 1, registrado antes de qualquer
            # lógica de negócio rodar.
            new_clock = self._clock.update_on_receive(request.timestamp)
            details = (
                f"recebido de {request.origin}: {_describe(request)} "
                f"(t_m={request.timestamp} -> max(L,{request.timestamp})+1={new_clock})"
            )
            log_event(self._logger, self._process_id, "RECEIVE", new_clock, details)
            return original(request, context)

        return grpc.unary_unary_rpc_method_handler(
            wrapped,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
