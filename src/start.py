import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, "rpc"))

import grpc
from processes_pb2_grpc import ProcessesStub
from google.protobuf.empty_pb2 import Empty

if __name__ == "__main__":

    p1_channel = grpc.insecure_channel("localhost:50051")

    p1 = ProcessesStub(p1_channel)
    p1.ExecuteTestCase(Empty())

    log_source = os.path.join(BASE_DIR, "logger", "logs", "output.log")
    result_dir = os.path.join(BASE_DIR, "result")

    os.makedirs(result_dir, exist_ok=True)
    shutil.copy(log_source, os.path.join(result_dir, "output.log"))
