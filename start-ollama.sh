#!/bin/bash

echo "Starting Ollama server..."

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Function to check if Ollama is responding
check_ollama() {
    curl -s "http://127.0.0.1:11434/api/tags" > /dev/null
}

# Wait for Ollama to start
echo "Waiting for Ollama to become responsive..."
COUNTER=0
MAX_TRIES=60

until check_ollama || [ $COUNTER -eq $MAX_TRIES ]; do
    echo "Waiting for Ollama... (Attempt $COUNTER of $MAX_TRIES)"
    COUNTER=$((COUNTER + 1))
    sleep 1
done

if [ $COUNTER -eq $MAX_TRIES ]; then
    echo "Failed to start Ollama after $MAX_TRIES seconds"
    exit 1
fi

echo "Ollama is running!"

# Pull the model
echo "Pulling llama2 model..."
ollama pull llama2

echo "Setup complete!"

# Keep the script running
wait $OLLAMA_PID
