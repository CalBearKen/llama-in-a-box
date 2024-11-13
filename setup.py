import subprocess
import sys
import time
import os
from tqdm import tqdm
import requests
import docker

def print_colored(text, color='white'):
    """Print colored text"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'blue': '\033[94m',
        'yellow': '\033[93m',
        'white': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['white']}")

def check_requirements():
    """Check if all requirements are met"""
    requirements = [
        ('Docker', 'Checking Docker installation...'),
        ('Python', 'Checking Python installation...'),
        ('Disk Space', 'Checking available disk space...')
    ]
    
    with tqdm(total=len(requirements), desc="Checking requirements") as pbar:
        # Check Docker
        try:
            client = docker.from_env()
            client.ping()
            pbar.update(1)
        except Exception as e:
            print_colored(f"\nDocker is not running or not installed: {e}", 'red')
            return False
            
        # Check Python version
        try:
            if sys.version_info >= (3, 8):
                pbar.update(1)
            else:
                print_colored("\nPython 3.8 or higher is required", 'red')
                return False
        except Exception as e:
            print_colored(f"\nCould not check Python version: {e}", 'red')
            return False
            
        # Check disk space (need at least 10GB free)
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p("."), None, None, ctypes.pointer(free_bytes))
                free_gb = free_bytes.value / 1024 / 1024 / 1024
            else:  # Unix/Linux/macOS
                st = os.statvfs('.')
                free_gb = (st.f_bavail * st.f_frsize) / (1024 * 1024 * 1024)
                
            if free_gb < 10:
                print_colored(f"\nInsufficient disk space. Need at least 10GB free, but only have {free_gb:.1f}GB", 'red')
                return False
            pbar.update(1)
        except Exception as e:
            print_colored(f"\nCould not check disk space: {e}", 'yellow')
            pbar.update(1)
    
    print_colored("✓ All requirements met", 'green')
    return True

def wait_for_services(container, max_attempts=60):
    """Wait for all services to be ready"""
    print_colored("\nWaiting for services to start...", 'blue')
    
    def check_container_logs():
        """Check container logs for errors"""
        logs = container.logs().decode('utf-8')
        if "Error:" in logs or "error:" in logs:
            print_colored("\nFound errors in container logs:", 'red')
            print_colored(logs, 'red')
            return False
        return True

    with tqdm(total=max_attempts, desc="Starting services") as pbar:
        for attempt in range(max_attempts):
            try:
                # Check if container is still running
                container.reload()
                if container.status != 'running':
                    print_colored("\nContainer stopped unexpectedly!", 'red')
                    print_colored("\nContainer logs:", 'red')
                    print_colored(container.logs().decode('utf-8'), 'red')
                    return False

                # Check API health
                response = requests.get('http://localhost:5001/health', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy' and data.get('ollama_status') == 'up':
                        print_colored("\n✓ Services are ready!", 'green')
                        return True
                    else:
                        print_colored(f"\nUnhealthy response: {data}", 'yellow')

                # Check Ollama directly
                ollama_response = requests.get('http://localhost:11434/api/tags', timeout=10)
                if ollama_response.status_code == 200:
                    print_colored("\n✓ Ollama is responding!", 'green')

            except requests.exceptions.ConnectionError:
                if attempt % 5 == 0:  # Log every 5th attempt
                    print_colored("\nWaiting for services to become available...", 'yellow')
                    check_container_logs()
            except Exception as e:
                if attempt % 5 == 0:  # Log every 5th attempt
                    print_colored(f"\nError checking services: {str(e)}", 'yellow')
                    check_container_logs()

            pbar.update(1)
            time.sleep(2)

    # If we get here, services didn't start in time
    print_colored("\nContainer logs:", 'red')
    print_colored(container.logs().decode('utf-8'), 'red')
    return False

def build_and_run():
    """Build and run the Docker container"""
    try:
        client = docker.from_env()
        
        # Stop and remove existing container if it exists
        try:
            container = client.containers.get('ollama-api')
            print_colored("Stopping existing container...", 'blue')
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
            
        print_colored("\nBuilding Docker image...", 'blue')
        image, build_logs = client.images.build(
            path=".",
            tag="ollama-api",
            rm=True
        )
        
        print_colored("\nStarting container...", 'blue')
        container = client.containers.run(
            "ollama-api",
            name="ollama-api",
            ports={
                '11434/tcp': 11434,
                '5001/tcp': 5001
            },
            detach=True
        )
        
        # Wait for services with improved monitoring
        return wait_for_services(container)
        
    except Exception as e:
        print_colored(f"\nError: {str(e)}", 'red')
        return False

def main():
    """Main function"""
    print_colored("Starting setup...", 'blue')
    
    if not check_requirements():
        print_colored("\nSetup failed: requirements not met!", 'red')
        sys.exit(1)
        
    if not build_and_run():
        print_colored("\nSetup failed!", 'red')
        sys.exit(1)
    
    print_colored("\nSetup completed successfully!", 'green')
    print_colored("The services should now be accessible at:", 'blue')
    print_colored("- API endpoint: http://localhost:5001", 'white')
    print_colored("- Ollama service: http://localhost:11434", 'white')

if __name__ == "__main__":
    main()