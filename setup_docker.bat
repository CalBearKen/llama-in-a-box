docker build -t ollama_api .

docker run -d --name ollama_api -p 11434:11434 -p 5001:5001 ollama_api