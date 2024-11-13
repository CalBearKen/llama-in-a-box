import http.server
import socketserver
import json
import urllib.request
import time

PORT = 5002

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            try:
                # Try to connect to Ollama
                req = urllib.request.Request(
                    'http://localhost:11434/api/tags',
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = response.read()
                    
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
                
            except Exception as e:
                # Send error response
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": str(e)
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Serving health check at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Wait for Ollama to start
    time.sleep(5)
    run_server()
