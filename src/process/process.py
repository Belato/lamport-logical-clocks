"""Processo distribuído do cenário de rastreamento de frota (P1/P2/P3).

Cenário simulado (ver relatório para o diagrama completo):
  P1 (rastreador GPS do veículo) -> P2 (processamento/geofencing) -> P3 (central de alertas)

Toda a lógica do relógio de Lamport (incrementar antes de EXEC/SEND, anexar o
timestamp na mensagem e aplicar max(L_j, t_m) + 1 no recebimento) vive nos
interceptors gRPC (ver interceptors.py). Este módulo só contém a lógica de
negócio de cada processo e o "roteiro" do cenário de teste.
"""

from concurrent import futures
import os
import threading
import time

import grpc

import lamport_pb2
import lamport_pb2_grpc
from clock import LamportClock
from event_log import build_logger, log_event
from interceptors import LamportClientInterceptor, LamportServerInterceptor

PROCESS_ID = os.environ["PROCESS_ID"]
PEER_ID = os.getenv("PEER_ID")            # id do processo de destino (ex.: "P2"), se houver
PEER_HOST = os.getenv("PEER_HOST")        # host:porta do destino (ex.: "p2:50051"), se houver
START_DELAY_SECONDS = float(os.getenv("START_DELAY_SECONDS", "2"))
GPS_DRIFT_SECONDS = float(os.getenv("GPS_DRIFT_SECONDS", "0"))
GRPC_PORT = os.getenv("GRPC_PORT", "50051")

VEHICLE_ID = "ABC-1234"


class Process(lamport_pb2_grpc.TrackerServicer):
    def __init__(self, process_id: str):
        self.id = process_id
        self.clock = LamportClock()
        self.logger = build_logger(process_id)
        self._locations_received = 0

        self.peer_stub = None
        if PEER_ID and PEER_HOST:
            channel = grpc.insecure_channel(PEER_HOST)
            channel = grpc.intercept_channel(
                channel,
                LamportClientInterceptor(self.clock, self.id, PEER_ID, self.logger),
            )
            self.peer_stub = lamport_pb2_grpc.TrackerStub(channel)

    # ---- evento interno (regra 1: incrementa antes de executar) ----
    def execute_internal(self, details: str) -> int:
        new_clock = self.clock.tick()
        log_event(self.logger, self.id, "EXEC", new_clock, details)
        return new_clock

    def _call_with_retry(self, rpc_call, request, retries=15, delay=1.0):
        """O relógio lógico só é incrementado (SEND) dentro do interceptor,
        na primeira tentativa; um retry aqui é só para tolerar o peer ainda
        estar subindo o container - não deve re-executar a regra de Lamport
        mais de uma vez por mensagem."""
        last_error = None
        for attempt in range(retries):
            try:
                return rpc_call(request)
            except grpc.RpcError as exc:
                last_error = exc
                if exc.code() != grpc.StatusCode.UNAVAILABLE:
                    raise
                time.sleep(delay)
        raise last_error

    # ---------------------------------------------------------------
    # RPCs de negócio - o relógio já foi tratado pelo LamportServerInterceptor
    # antes deste método rodar; aqui só há regra de negócio do cenário.
    # ---------------------------------------------------------------
    def SendLocation(self, request, context):
        self._locations_received += 1
        if self._locations_received == 1:
            self.execute_internal(
                f"armazena posição inicial do veículo {request.vehicle_id} "
                f"({request.lat:.4f}, {request.lon:.4f})"
            )
        else:
            self.execute_internal(
                f"compara nova posição ({request.lat:.4f}, {request.lon:.4f}) com a anterior "
                f"e detecta saída do geofence permitido"
            )
            if self.peer_stub is not None:
                alert = lamport_pb2.GeofenceAlert(
                    vehicle_id=request.vehicle_id,
                    reason="fora da área de geofence permitida",
                )
                self._call_with_retry(self.peer_stub.SendAlert, alert)
        return lamport_pb2.Ack()

    def SendAlert(self, request, context):
        self.execute_internal(
            f"aciona notificação sonora para o operador (veículo={request.vehicle_id}, "
            f"motivo='{request.reason}')"
        )
        return lamport_pb2.Ack()

    # ---------------------------------------------------------------
    # Roteiros (cenário de teste) - um por processo, disparado em thread
    # separada após o servidor gRPC subir.
    # ---------------------------------------------------------------
    def run_scenario(self):
        time.sleep(START_DELAY_SECONDS)

        if self.id == "P1":
            self._run_p1()
        elif self.id == "P3":
            self._run_p3()
        # P2 é puramente reativo (só responde a SendLocation/SendAlert).

    def _run_p1(self):
        self.execute_internal(
            f"leitura inicial de GPS do veículo {VEHICLE_ID} (lat=-23.5500, lon=-46.6330)"
        )
        loc1 = lamport_pb2.LocationUpdate(
            vehicle_id=VEHICLE_ID,
            lat=-23.5500,
            lon=-46.6330,
            gps_time=time.time() + GPS_DRIFT_SECONDS,
        )
        self._call_with_retry(self.peer_stub.SendLocation, loc1)

        time.sleep(2)

        self.execute_internal(
            f"nova leitura de GPS do veículo {VEHICLE_ID}: movimento rápido detectado "
            f"(lat=-23.5610, lon=-46.6490)"
        )
        loc2 = lamport_pb2.LocationUpdate(
            vehicle_id=VEHICLE_ID,
            lat=-23.5610,
            lon=-46.6490,
            gps_time=time.time() + GPS_DRIFT_SECONDS,
        )
        self._call_with_retry(self.peer_stub.SendLocation, loc2)

    def _run_p3(self):
        # Evento concorrente com o EXEC inicial de P1: nenhuma mensagem os
        # relaciona, então é esperado (e didático) que os dois fiquem com o
        # mesmo relógio lógico (L=1).
        self.execute_internal("operador faz login no painel de monitoramento")


def serve():
    process = Process(PROCESS_ID)
    server_interceptor = LamportServerInterceptor(process.clock, process.id, process.logger)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=(server_interceptor,),
    )
    lamport_pb2_grpc.add_TrackerServicer_to_server(process, server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    print(f"[{PROCESS_ID}] servidor gRPC ouvindo na porta {GRPC_PORT}", flush=True)

    threading.Thread(target=process.run_scenario, daemon=True).start()

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
