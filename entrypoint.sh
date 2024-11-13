#!/bin/bash
set -e

echo "Starting setup..."

# Show network info
echo "Network configuration:"
ip addr show
echo "DNS configuration:"
cat /etc/resolv.conf
echo "Hosts file:"
cat /etc/hosts

# Start Ollama
echo "Starting Ollama server..."
ollama serve > /var/log/ollama.log 2>&1 &
OLLAMA_PID=$!

# Function to check if Ollama is running
check_ollama() {
    if ! ps -p $OLLAMA_PID > /dev/null; then
        echo "Ollama process died! Check logs:"
        cat /var/log/ollama.log
        return 1
    fi
    
    # Try multiple hostnames
    for host in "localhost" "127.0.0.1" "0.0.0.0" "ollama-api"; do
        if curl -s -f "http://${host}:11434/api/tags" > /dev/null 2>&1; then
            echo "Successfully connected to Ollama at ${host}"
            return 0
        fi
    done
    return 1
}

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
max_attempts=30
attempt=0

# Initial delay to let Ollama initialize
echo "Initial delay to let Ollama initialize..."
sleep 20  # Increased initial delay

while [ $attempt -lt $max_attempts ]; do
    echo "Checking Ollama (attempt $((attempt + 1))/$max_attempts)..."
    
    if check_ollama; then
        echo "✓ Ollama is responding to API requests"
        break
    fi
    
    # Show Ollama logs for debugging
    echo "Current Ollama logs:"
    tail -n 5 /var/log/ollama.log
    
    echo "Waiting for Ollama... (attempt $((attempt + 1))/$max_attempts)"
    sleep 10  # Increased delay between attempts
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "Error: Ollama failed to start after $max_attempts attempts"
    echo "Full Ollama logs:"
    cat /var/log/ollama.log
    exit 1
fi

echo "✓ Ollama is running"

# Pull the model before starting Flask
echo "Pulling llama3.2 model..."
ollama pull llama3.2

# Verify model is available
echo "Verifying model..."
if ! ollama list | grep -q "llama3.2"; then
    echo "Error: Model llama3.2 not found after pulling"
    exit 1
fi

# Final verification of Ollama
echo "Final Ollama verification..."
if ! curl -s -f http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama is not responding after model pull"
    exit 1
fi

# Additional delay before starting Flask
echo "Waiting for Ollama to fully initialize..."
sleep 15

# Start Flask API
echo "Starting Flask API..."
cd /app
exec python3 -u API.py
