FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./grpc/loggers_pb2_grpc.py ./loggers_pb2_grpc.py
COPY ./grpc/loggers_pb2.py ./loggers_pb2.py

RUN pip install -r requirements.txt

CMD ["python", "./main.py"]