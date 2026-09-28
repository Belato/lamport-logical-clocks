import logging
from concurrent import futures
import grpc
import os

logger = logging.getLogger("Logger")

import loggers_pb2_grpc
import processes_pb2_grpc

from google.protobuf.empty_pb2 import Empty

class Logger(loggers_pb2_grpc.LoggersServicer):
    def __init__(self):
        p1_channel = grpc.insecure_channel(f"p1:50051")
        p2_channel = grpc.insecure_channel(f"p2:50052")
        p3_channel = grpc.insecure_channel(f"p3:50053")

        self.p1 = processes_pb2_grpc.ProcessesStub(p1_channel)
        self.p2 = processes_pb2_grpc.ProcessesStub(p2_channel)
        self.p3 = processes_pb2_grpc.ProcessesStub(p3_channel)



    def __generate_log(self, message):
        for msg in message:
            logger.info(msg.log_message.strip())


    def GenerateGlobalLog(self, request, context):

        p1_logs = self.p1.GetProcessLogsList(request).process_logs
        p2_logs = self.p2.GetProcessLogsList(request).process_logs
        p3_logs = self.p3.GetProcessLogsList(request).process_logs

        curr_p1 = 0
        curr_p2 = 0
        curr_p3 = 0

        global_log = []

        while len(global_log) < len(p1_logs) + len(p2_logs) + len(p3_logs):


            t_p1 = p1_logs[curr_p1].timestemp if curr_p1 < len(p1_logs) else float('inf')
            t_p2 = p2_logs[curr_p2].timestemp if curr_p2 < len(p2_logs) else float('inf')
            t_p3 = p3_logs[curr_p3].timestemp if curr_p3 < len(p3_logs) else float('inf')

            if t_p1 <= t_p2 and t_p1 <= t_p3:
                global_log.append(p1_logs[curr_p1])
                curr_p1 +=1
            elif t_p2 <= t_p1 and t_p2 <= t_p3:
                global_log.append(p2_logs[curr_p2])
                curr_p2 +=1
            else:
                global_log.append(p3_logs[curr_p3])
                curr_p3 +=1

        self.__generate_log(global_log)

        return Empty()

        
        
    

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Logger()
    loggers_pb2_grpc.add_LoggersServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50054')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    
    logging.basicConfig(
        filename=f"logs/output.log",
        filemode='w',
        format='%(message)s',
        level=logging.INFO
    )
    
    serve()
