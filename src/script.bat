@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "PYTHON=python"
if exist "..\.venv\Scripts\python.exe" set "PYTHON=..\.venv\Scripts\python.exe"

echo Subindo containers (build somente se as imagens ainda nao existirem)...
docker compose up -d

echo Aguardando p1, p2, p3 e logger ficarem saudaveis...
call :wait_healthy p1
call :wait_healthy p2
call :wait_healthy p3
call :wait_healthy logger

echo Executando cenario de teste (start.py)...
"%PYTHON%" start.py

echo Cenario concluido. Log global salvo em result\output.log

goto :cleanup

:wait_healthy
set "SERVICE=%~1"
for /f "delims=" %%I in ('docker compose ps -q %SERVICE%') do set "CID=%%I"
:wait_healthy_loop
set "STATUS="
for /f "delims=" %%H in ('docker inspect -f "{{.State.Health.Status}}" %CID%') do set "STATUS=%%H"
if not "%STATUS%"=="healthy" (
    ping -n 2 127.0.0.1 >nul
    goto :wait_healthy_loop
)
echo   - %SERVICE% esta saudavel
exit /b

:cleanup
echo Encerrando containers...
docker compose down
