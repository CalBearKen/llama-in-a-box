# Use an official Ubuntu as the base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Step 1: Update package list
RUN echo "Step 1: Updating package list..." && \
    apt-get update

# Step 2: Install system dependencies
RUN echo "Step 2: Installing system dependencies..." && \
    apt-get install -y \
    curl \
    python3 \
    python3-pip \
    iproute2 \
    net-tools \
    iputils-ping \
    && echo "Cleaning up apt cache..." \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Install Python packages
RUN echo "Step 3: Installing Python packages..." && \
    pip3 install --no-cache-dir --verbose flask requests flask-cors

# Step 4: Install Ollama
RUN echo "Step 4: Installing Ollama..." && \
    curl -fsSL https://ollama.com/install.sh | sh

# Step 5: Set up application
WORKDIR /app
RUN echo "Step 5: Setting up application directory at /app"

# Step 6: Copy application files
COPY API.py index.html entrypoint.sh ./
COPY static/ ./static/
RUN echo "Step 6: Copied application files" && \
    echo "Making entrypoint.sh executable..." && \
    chmod +x /app/entrypoint.sh

# Step 7: Expose ports
EXPOSE 5001 11434
RUN echo "Step 7: Exposed ports 5001 and 11434"

# Final step: Set entrypoint
RUN echo "Final step: Setting entrypoint to /app/entrypoint.sh"
ENTRYPOINT ["/app/entrypoint.sh"]
