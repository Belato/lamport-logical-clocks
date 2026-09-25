import logging

class Logger(processes_pb2_grpc.LoggerServicer):
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("codebase/logs/process.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    process = Process(PROCESS_ID)
    processes_pb2_grpc.add_ProcessesServicer_to_server(process, server)
    server.add_insecure_port('0.0.0.0:50054')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":

    logging.basicConfig(filename=f"logs/{PROCESS_ID}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", level=logging.INFO)
    
    serve()
