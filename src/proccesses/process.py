import grpc

from processes_pb2 import ProcessMsg, ProcessLog, ProcessLogsList
from google.protobuf.empty_pb2 import Empty

import processes_pb2_grpc


class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id, logger):
        self.id = process_id
        self.timestemp = 0
        self.logger = logger


    def __generate_log(self, event_type, timestemp, message, process=None):

        if event_type == "SEND":
            self.logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: process '{process}' sent '{message}'")

        elif event_type == "RECEIVE":
            self.logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: process '{process}' received '{message}'")
        
        else:
            self.logger.info(f"Evento: {event_type} | Relógio Lógico: {timestemp} | Detalhes: {message}")

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
        pass

    def ExecuteTestCase(self, process_msg_rcv, context):
            pass

    def GetProcessLogsList(self, request, context):
            
        list_logs = []
        with open(f"logs/{self.id}.log", "r", encoding="utf-8") as log_file:
            for line in log_file:
                timestemp = line.split(" | ")[1].replace("Relógio Lógico: ", "")
                list_logs.append(ProcessLog(process=self.id, log_message=line, timestemp=int(timestemp)))

        return ProcessLogsList(process_logs=list_logs)