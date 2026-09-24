from concurrent import futures
import sys
import grpc
from datetime import datetime
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from processes_pb2 import ProcessMsg
import processes_pb2_grpc


class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id):
        self.id = process_id
        self.timestemp = 0
        processes_channel = grpc.insecure_channel(
            f"p2:50052"
        )
        self.client = processes_pb2_grpc.ProcessesStub(processes_channel)

    def __clockwork_increment(self):
        self.timestemp += 1
        logger.info(f"Process {self.id} timestamp incremented to {self.timestemp}.")

    def _send_message(self, message=None):

        self.__clockwork_increment()
        
        logger.info(f"Process {self.id} sent message: {message} with timestamp {self.timestemp}.")
        return ProcessMsg(
            message=message,
            timestemp=self.timestemp
        )

    def _receive_message(self, process_msg):
        self.timestemp = max(self.timestemp, process_msg.timestemp) + 1
        logger.info(f"Process {self.id} received message: {process_msg.message} with timestamp {self.timestemp}.")


    def _execute_event(self):
        self.__clockwork_increment()
        logger.info(f"Process {self.id} executed an internal event with timestamp {self.timestemp}.")


    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(process_msg_rcv)

        self._execute_event()

        process_msg_snd =self._send_message(process_msg_rcv.message)
        return process_msg_snd


    def flow(self):
        self._execute_event()

        process_msg_snd = self._send_message(message="Hello from process")
        process_msg_rcv = self.client.ExecuteProcess(process_msg_snd)
        self._receive_message(process_msg_rcv)
        
        self._execute_event()

        logger.warning(f"Timestemp: {self.timestemp}")



def serve(method_name):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50051')
    server.start()
    print(method_name)
    if method_name and hasattr(Process, method_name):
        print(method_name)
        method = getattr(process, method_name)
        method()
    server.wait_for_termination()

if __name__ == "__main__":

    logging.basicConfig(filename=f"logs/{PROCESS_ID}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", level=logging.INFO)
    method_name = None
    if len(sys.argv) >= 2:
        method_name = sys.argv[1]
    
    serve("flow")