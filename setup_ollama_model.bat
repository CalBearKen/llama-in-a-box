@echo off

REM Define the container name or ID
set CONTAINER_NAME=ollama_api

REM Run 'ollama list' inside the container
docker exec %CONTAINER_NAME% ollama list

REM Pull a model inside the container
docker exec %CONTAINER_NAME% ollama pull llama3.2

REM Run the model with a prompt inside the container
docker exec %CONTAINER_NAME% ollama run llama3.2