FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./rpc/processes_pb2_grpc.py ./processes_pb2_grpc.py
COPY ./rpc/processes_pb2.py ./processes_pb2.py
COPY ./rpc/loggers_pb2_grpc.py ./loggers_pb2_grpc.py
COPY ./rpc/loggers_pb2.py ./loggers_pb2.py

RUN pip install -r requirements.txt

CMD ["python", "./main.py"]