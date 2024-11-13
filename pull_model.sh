#!/bin/bash

ollama serve
# Wait for a few seconds to ensure the service is up
sleep 5

# Pull the LLaMA model
ollama pull llama3.1
