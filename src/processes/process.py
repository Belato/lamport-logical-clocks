from concurrent import futures
import grpc

class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id, lamport):
        self.id = process_id
        self.lamport = lamport


    def ExecuteProcess(self, process_msg_rcv, context):
        pass

    def GetProcessLogsList(self, request, context):
        
        list_logs = []
        with open(f"logs/{PROCESS_ID}.log", "r", encoding="utf-8") as log_file:
            for line in log_file:
                timestemp = line.split(" | ")[1].replace("Relógio Lógico: ", "")
                list_logs.append(ProcessLog(process=self.id, log_message=line, timestemp=int(timestemp)))

        return ProcessLogsList(process_logs=list_logs)
