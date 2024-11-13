# Check if Docker is installed
function Test-DockerInstalled {
    try {
        docker --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to show progress
function Write-Step {
    param($Message)
    Write-Host "`n🚀 $Message" -ForegroundColor Cyan
}

# Main setup script
Write-Step "Starting Ollama API setup..."

# Check Docker installation
if (-not (Test-DockerInstalled)) {
    Write-Host "❌ Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Step "Checking Docker service..."
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop and remove existing containers
Write-Step "Cleaning up existing containers..."
docker ps -a | Select-String "ollama-api" | ForEach-Object { 
    $containerId = $_.ToString().Split()[0]
    Write-Host "Stopping container: $containerId"
    docker stop $containerId 2>$null
    Write-Host "Removing container: $containerId"
    docker rm $containerId 2>$null
}

# Remove existing image
Write-Step "Removing existing image..."
docker rmi ollama-api -f 2>$null

# Build new image
Write-Step "Building Docker image..."
docker build -t ollama-api .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    exit 1
}

# Start container
Write-Step "Starting container..."
docker run -d -p 5001:5001 -p 11434:11434 --name ollama-api ollama-api
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait for services to start
Write-Step "Waiting for services to start..."
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    }
    catch {
        Write-Host "Waiting for API to become available... (Attempt $($attempt + 1)/$maxAttempts)"
        Start-Sleep -Seconds 2
    }
    $attempt++
}

if ($ready) {
    Write-Host "`n✅ Setup completed successfully!" -ForegroundColor Green
    Write-Host "`nAPI is now running at: http://localhost:5001" -ForegroundColor Yellow
    Write-Host "To test the API, you can use the following PowerShell command:`n" -ForegroundColor Yellow
    Write-Host 'Invoke-RestMethod -Uri "http://localhost:5001/api/generate" -Method Post -ContentType "application/json" -Body ''{"model":"llama2","prompt":"Hello, how are you?"}''' -ForegroundColor Gray
    Write-Host "`nTo stop the service, run:" -ForegroundColor Yellow
    Write-Host "docker stop ollama-api" -ForegroundColor Gray
} else {
    Write-Host "❌ Setup completed but services may not be fully ready. Please check docker logs:" -ForegroundColor Red
    Write-Host "docker logs ollama-api" -ForegroundColor Gray
}

# Add error handling for logs
Write-Step "Recent logs:"
try {
    docker logs --tail 10 ollama-api
} catch {
    Write-Host "Could not fetch logs" -ForegroundColor Red
}
