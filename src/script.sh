#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

PYTHON="python"
if [ -f "../.venv/Scripts/python.exe" ]; then
    PYTHON="../.venv/Scripts/python.exe"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON="../.venv/bin/python"
fi

cleanup() {
    echo "Encerrando containers..."
    docker compose down
}
trap cleanup EXIT

echo "Subindo containers (build somente se as imagens ainda nao existirem)..."
docker compose up -d

echo "Aguardando p1, p2, p3 e logger ficarem saudaveis..."
for service in p1 p2 p3 logger; do
    container_id=$(docker compose ps -q "$service")
    until [ "$(docker inspect -f '{{.State.Health.Status}}' "$container_id")" == "healthy" ]; do
        sleep 1
    done
    echo "  - $service esta saudavel"
done

echo "Executando cenario de teste (start.py)..."
"$PYTHON" start.py

echo "Cenario concluido. Log global salvo em result/output.log"
