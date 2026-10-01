from concurrent import futures
import grpc
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from process import Process
from google.protobuf.empty_pb2 import Empty

import processes_pb2_grpc
import loggers_pb2_grpc



class P1(Process):
    def __init__(self, process_id, logger):
        super().__init__(process_id, logger)

        p2_channel = grpc.insecure_channel(f"p2:50052")
        logger_channel = grpc.insecure_channel(f"logger:50054")

        self.p2 = processes_pb2_grpc.ProcessesStub(p2_channel)
        self.p_logger = loggers_pb2_grpc.LoggersStub(logger_channel)


    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(message=process_msg_rcv.message, timestemp=process_msg_rcv.timestemp, p_origin=process_msg_rcv.sender)

        self._execute_event()

        process_msg_snd =self._send_message(message="Another message from process 1", p_target=process_msg_rcv.sender)
        return process_msg_snd


    def ExecuteTestCase(self, request, context):
        self._execute_event()

        p2_msg_snd = self._send_message(message="Process 1 sending message to process 2", p_target="P2")
        future = self.p2.ExecuteProcess.future(p2_msg_snd)

        # Chamada nao-bloqueante: P1 continua executando localmente enquanto aguarda
        # a resposta de P2, em vez de ficar parado esperando a rede.
        self._execute_event()
        self._execute_event()

        p2_msg_rcv = future.result()
        self._receive_message(message=p2_msg_rcv.message, timestemp=p2_msg_rcv.timestemp, p_origin=p2_msg_rcv.sender)

        self._execute_event()

        self.p_logger.GenerateGlobalLog(Empty())

        return Empty()



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = P1(PROCESS_ID, logger)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50051')
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