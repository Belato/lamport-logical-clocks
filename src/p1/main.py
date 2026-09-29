from concurrent import futures
import sys
import grpc
from datetime import datetime
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

from processes_pb2 import ProcessMsg, ProcessLog, ProcessLogsList
from google.protobuf.empty_pb2 import Empty

import processes_pb2_grpc
import loggers_pb2_grpc



class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id):
        self.id = process_id
        self.timestemp = 0

        p2_channel = grpc.insecure_channel(f"p2:50052")
        logger_channel = grpc.insecure_channel(f"logger:50054")

        self.p2 = processes_pb2_grpc.ProcessesStub(p2_channel)
        self.logger = loggers_pb2_grpc.LoggersStub(logger_channel)

    def __generate_log(self, event_type, timestemp, message, process=None):

        if event_type == "SEND":
            logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: process '{process}' sent '{message}'")

        elif event_type == "RECEIVE":
            logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: process '{process}' received '{message}'")
        
        else:
            logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: {message}")

    def __clockwork_increment(self):
            self.timestemp += 1

    def _send_message(self, message, p_target):

        self.__clockwork_increment()
        
        self.__generate_log("SEND", self.timestemp, message, process=p_target)
        return ProcessMsg(
            sender=self.id,
            message=message,
            timestemp=self.timestemp
        )

    def _receive_message(self, message, timestemp, p_origin):
        self.timestemp = max(self.timestemp, timestemp) + 1
        self.__generate_log("RECEIVE", self.timestemp, message, process=p_origin)


    def _execute_event(self):
        self.__clockwork_increment()
        self.__generate_log("EXEC", self.timestemp, "Internal event")


    def ExecuteProcess(self, process_msg_rcv, context):
        self._receive_message(message=process_msg_rcv.message, timestemp=process_msg_rcv.timestemp, p_origin=process_msg_rcv.sender)

        self._execute_event()

        process_msg_snd =self._send_message(message="Another message from process 1", p_target=process_msg_rcv.sender)
        return process_msg_snd


    def GetProcessLogsList(self, request, context):
            
        list_logs = []
        with open(f"logs/{PROCESS_ID}.log", "r", encoding="utf-8") as log_file:
            for line in log_file:
                timestemp = line.split(" | ")[1].replace("Relógio Lógico: ", "")
                list_logs.append(ProcessLog(process=self.id, log_message=line, timestemp=int(timestemp)))

        return ProcessLogsList(process_logs=list_logs)
        


    def flow(self):
        self._execute_event()

        p2_msg_snd = self._send_message(message="Process 1 sending message to process 2", p_target="P2")
        p2_msg_rcv = self.p2.ExecuteProcess(p2_msg_snd)
        self._receive_message(message=p2_msg_rcv.message, timestemp=p2_msg_rcv.timestemp, p_origin=p2_msg_rcv.sender)
        
        self._execute_event()

        self.logger.GenerateGlobalLog(Empty())



def serve(method_name):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50051')
    server.start()

    if method_name and hasattr(Process, method_name):
        method = getattr(process, method_name)
        method()

    server.wait_for_termination()


if __name__ == "__main__":

    logging.basicConfig(
        filename=f"logs/{PROCESS_ID}.log",
        filemode='w',
        format='[Processo %(name)s] %(message)s',
        level=logging.INFO
    )

    method_name = None
    if len(sys.argv) >= 2:
        method_name = sys.argv[1]
    
    serve("flow")