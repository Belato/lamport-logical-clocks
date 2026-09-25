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


class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id):
        self.id = process_id
        self.timestemp = 0

    def __clockwork_increment(self):
        self.timestemp += 1
        Evento: %(event_type)s | Relógio Lógico: %(timestamp)s  | Detalhes: <mensagem/info>
        # logger.info(f"Process {self.id} timestamp incremented to {self.timestemp}.")

    def __generate_log(self, event_type, timestemp, message):
        logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp}  | Detalhes: {message}")


    def _send_message(self, message=None):

        self.__clockwork_increment()
        self.__generate_log("SEND", self.timestemp, message)
        # logger.info(f"Process {self.id} sent message: {message} with timestamp {self.timestemp}.")
        return ProcessMsg(
            message=message,
            timestemp=self.timestemp
        )

    def _receive_message(self, process_msg):
        self.timestemp = max(self.timestemp, process_msg.timestemp) + 1
        self.__generate_log("RECEIVE", self.timestemp, process_msg.message)
        # logger.info(f"Process {self.id} received message: {process_msg.message} with timestamp {self.timestemp}.")


    def _execute_event(self):
        self.__clockwork_increment()
        self.__generate_log("EXEC", self.timestemp, "Internal event")


    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(process_msg_rcv)

        process_msg_snd =self._send_message(process_msg_rcv.message)
        return process_msg_snd

    def GetProcessLogsList(self, request, context):
        
        list_logs = []
        with open(f"logs/{PROCESS_ID}.log", "r", encoding="utf-8") as log_file:
            for line in log_file:
                list_logs.append(ProcessLog(message=line, timestemp=self.timestemp))

        return processes_pb2.GetProcessLogsListResponse(logs=list_logs)
        

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50052')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
#-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}
    logging.basicConfig(
        filename=f"logs/{PROCESS_ID}.log", 
        format='[%(name)s] %(message)s'
    )
    
    serve()