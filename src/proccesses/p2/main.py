from concurrent import futures
import grpc
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from process import Process
import processes_pb2_grpc
    

class P2(Process):
    def __init__(self, process_id, logger):
        super().__init__(process_id, logger)

        p3_channel = grpc.insecure_channel(f"p3:50053")
        self.p3 = processes_pb2_grpc.ProcessesStub(p3_channel)


    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(message=process_msg_rcv.message, timestemp=process_msg_rcv.timestemp, p_origin=process_msg_rcv.sender)

        self._execute_event()

        p3_msg_snd = self._send_message(message="Another message from process 2", p_target="P3")
        future = self.p3.ExecuteProcess.future(p3_msg_snd)

        # Chamada nao-bloqueante: P2 continua executando localmente enquanto aguarda
        # a resposta de P3, em vez de ficar parado esperando a rede.
        self._execute_event()

        p3_msg_rcv = future.result()
        self._receive_message(message=p3_msg_rcv.message, timestemp=p3_msg_rcv.timestemp, p_origin=p3_msg_rcv.sender)

        self._execute_event()

        process_msg_snd =self._send_message(message=process_msg_rcv.message, p_target=process_msg_rcv.sender)
        return process_msg_snd

    def warm_up(self, n):
        for _ in range(n):
            self._execute_event()


def serve():
    process = P2(PROCESS_ID, logger)

    # P2 acumula eventos internos antes de aceitar conexoes, deixando L2 maior que o
    # timestamp que vira de P1. Isso testa se RECEIVE aplica max(Lj, tm) + 1 corretamente,
    # preservando o avanco local de P2 em vez de retroceder o relogio para tm + 1.
    process.warm_up(5)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50052')
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