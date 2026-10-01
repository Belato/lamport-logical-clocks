from concurrent import futures
import sys
import grpc
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from process import Process
import processes_pb2_grpc


class P3(Process):
    def __init__(self, process_id, logger):
        super().__init__(process_id, logger)

        p1_channel = grpc.insecure_channel(f"p1:50051")

        self.p1 = processes_pb2_grpc.ProcessesStub(p1_channel)

    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(message=process_msg_rcv.message, timestemp=process_msg_rcv.timestemp, p_origin=process_msg_rcv.sender)

        self._execute_event()
        self._execute_event()

        p1_msg_snd = self._send_message(message="Another message from process 3", p_target="P1")
        future = self.p1.ExecuteProcess.future(p1_msg_snd)

        # Chamada nao-bloqueante: P3 continua executando localmente enquanto aguarda
        # a resposta de P1, em vez de ficar parado esperando a rede.
        self._execute_event()

        p1_msg_rcv = future.result()
        self._receive_message(message=p1_msg_rcv.message, timestemp=p1_msg_rcv.timestemp, p_origin=p1_msg_rcv.sender)

        process_msg_snd =self._send_message(message=process_msg_rcv.message, p_target=process_msg_rcv.sender)
        return process_msg_snd


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = P3(PROCESS_ID, logger)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50053')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(
        filename=f"logs/{PROCESS_ID}.log",
        filemode='w',
        format='[Processo %(name)s] %(message)s',
        level=logging.INFO
    )
    
    serve()