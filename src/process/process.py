from concurrent import futures
import sys
import grpc
from datetime import datetime
import logging
import os

PROCESS_ID = os.getenv("PROCESS_ID")
logger = logging.getLogger(PROCESS_ID)

import processes_pb2
import processes_pb2_grpc


class Process(processes_pb2_grpc.ProcessesServicer):
    def __init__(self, process_id):
        self.id = process_id
        self.timestemp = 0
        processes_channel = grpc.insecure_channel(
            f"{'localhost'}:50051"
        )
        self.client = processes_pb2_grpc.ProcessesStub(processes_channel)

    def __clockwork_increment(self):
        self.timestemp += 1
        logger.info(f"Process {self.id} timestamp incremented to {self.timestemp}.")

    def Send_message(self, message=None):

        self.__clockwork_increment()
        message_body = {
            'message': message,
            'timestemp': self.timestemp
        }
        logger.info(f"Process {self.id} sent message: {message['message']} with timestamp {message['timestemp']}.")
        self.client.Receive_message(message_body)

    def example(self, request, context):
        # Retorna uma resposta GetProcesssesResponse com uma lista de processos
        return processes_pb2.GetProcesssesResponse(processes=[
            processes_pb2.Process(
                id='1',
                name='Michael',
                email='michaeldouglas@example.com',
                password='password')
        ])



    def Receive_message(self, request, context):
        ##receive message
        self.timestemp = max(self.timestemp, request.timestemp) + 1
        logger.info(f"Process {self.id} received message: {request.message} with timestamp {request.timestemp}.")


    def Execute_event(self):
        self.__clockwork_increment()
        logger.info(f"Process {self.id} executed an internal event with timestamp {self.timestemp}.")


    def flow(self):
        # Simula o envio de uma mensagem
        self.Execute_event()

        self.Send_message({"message": "Hello from process", "timestemp": self.timestemp})

        # Simula a execução de um evento interno
        self.execute_event()

        # Simula o recebimento de uma mensagem
        self.receive_message({"message": "Hello from another process", "timestemp": self.timestemp})



def serve(method_name):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print(method_name)
    if method_name and hasattr(Process, method_name):
        print(method_name)
        method = getattr(process, method_name)
        method()
    server.wait_for_termination()

if __name__ == "__main__":

    logging.basicConfig(filename=f"logs/{PROCESS_ID}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", level=logging.INFO)
    print("Starting server in: %s" % ('localhost:50051'))

    method_name = None
    if len(sys.argv) >= 2:
        method_name = sys.argv[1]
    
    serve(method_name)








processes_channel = grpc.insecure_channel(
    f"{'localhost'}:50051"
)
processes_client = processes_pb2_grpc.ProcessesStub(processes_channel)
