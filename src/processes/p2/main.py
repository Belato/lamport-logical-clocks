from concurrent import futures
import sys
import grpc
from datetime import datetime
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from processes_pb2 import ProcessMsg, ProcessLog, ProcessLogsList
import processes_pb2_grpc

from process import Process


class P1(Process):
    def __init__(self, process_id):

        super().__init__(process_id)

        p3_channel = grpc.insecure_channel(f"p3:50053")
        self.p3 = processes_pb2_grpc.ProcessesStub(p3_channel)



    def ExecuteProcess(self, process_msg_rcv, context):
        self.lamport.receive_message(process_msg_rcv)

        self.lamport.execute_event()

        p3_msg_snd = self.lamport.send_message(message="Another message from process 2")
        p3_msg_rcv = self.p3.ExecuteProcess(p3_msg_snd)
        self.lamport.receive_message(p3_msg_rcv)

        self.lamport.execute_event()

        process_msg_snd =self.lamport.send_message(process_msg_rcv.message)
        return process_msg_snd
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID, Lamport(logger))
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50052')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
#-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}
    logging.basicConfig(
        filename=f"logs/{PROCESS_ID}.log",
        filemode='w',
        format='[Processo %(name)s] %(message)s',
        level=logging.INFO
    )
    
    serve()