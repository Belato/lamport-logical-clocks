FROM python:3.14-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./rpc/processes_pb2_grpc.py ./processes_pb2_grpc.py
COPY ./rpc/processes_pb2.py ./processes_pb2.py

RUN pip install -r requirements.txt

CMD ["python", "./main.py"]