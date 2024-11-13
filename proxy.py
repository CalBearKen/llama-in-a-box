import socket
import threading
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OllamaProxy:
    def __init__(self, listen_port=11435, target_port=11434):
        self.listen_port = listen_port
        self.target_port = target_port
        self.server_socket = None
        self.running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.listen_port))
        self.server_socket.listen(5)
        self.running = True
        
        logger.info(f"Proxy listening on port {self.listen_port}")
        
        while self.running:
            try:
                client_sock, address = self.server_socket.accept()
                logger.debug(f"New connection from {address}")
                client_handler = threading.Thread(
                    target=self.handle_client,
                    args=(client_sock,)
                )
                client_handler.daemon = True
                client_handler.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket):
        try:
            # Connect to Ollama
            ollama_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ollama_socket.connect(('localhost', self.target_port))
            
            # Set up bidirectional forwarding
            t1 = threading.Thread(target=self.forward, args=(client_socket, ollama_socket))
            t2 = threading.Thread(target=self.forward, args=(ollama_socket, client_socket))
            
            t1.daemon = True
            t2.daemon = True
            
            t1.start()
            t2.start()
            
            t1.join()
            t2.join()
            
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def forward(self, source, destination):
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.send(data)
        except Exception as e:
            logger.error(f"Error forwarding data: {e}")
        finally:
            source.close()
            destination.close()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    proxy = OllamaProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        proxy.stop()
