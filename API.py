from flask import Flask, request, jsonify, Response, stream_with_context, send_file, send_from_directory
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)

def create_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    return session

@app.route('/')
def serve_frontend():
    return send_file('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_text():
    try:
        # Extract data from the incoming request
        data = request.get_json(force=True)
        logger.info(f"Received request: {data}")

        # Ensure the input contains both 'model' and 'prompt'
        if not data or 'model' not in data or 'prompt' not in data:
            return jsonify({"error": "Please provide both 'model' and 'prompt' in the request body."}), 400

        model = data['model']
        prompt = data['prompt']

        # Try different URLs in case one fails
        urls = [
            "http://localhost:11434/api/generate",
            "http://127.0.0.1:11434/api/generate",
            "http://0.0.0.0:11434/api/generate"
        ]

        # Prepare the request payload for Ollama
        ollama_payload = {
            "model": model,
            "prompt": prompt
        }

        headers = {'Content-Type': 'application/json'}
        session = create_session()

        # Try each URL until one works
        last_error = None
        for ollama_url in urls:
            try:
                logger.info(f"Trying Ollama URL: {ollama_url}")
                response = session.post(
                    ollama_url, 
                    json=ollama_payload, 
                    headers=headers, 
                    stream=True,
                    timeout=30
                )

                if response.status_code == 200:
                    logger.info(f"Successfully connected to {ollama_url}")
                    
                    def generate():
                        try:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    yield chunk
                        except Exception as e:
                            logger.error(f"Error during streaming: {str(e)}")
                            yield str(e).encode()
                        finally:
                            response.close()

                    return Response(
                        stream_with_context(generate()),
                        content_type=response.headers.get('Content-Type')
                    )
                else:
                    last_error = f"Status code {response.status_code} from {ollama_url}"
                    logger.warning(last_error)
                    response.close()

            except Exception as e:
                last_error = f"Error connecting to {ollama_url}: {str(e)}"
                logger.warning(last_error)
                continue

        # If we get here, none of the URLs worked
        error_msg = f"Failed to connect to Ollama. Last error: {last_error}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

    except Exception as e:
        error_msg = f"Exception in generate_text: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/health')
def health_check():
    try:
        session = create_session()
        response = session.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            return jsonify({
                "status": "healthy",
                "ollama_status": "up"
            })
        else:
            return jsonify({
                "status": "unhealthy",
                "error": f"Ollama returned status code {response.status_code}"
            }), 503
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    # Wait for Ollama to be ready
    logger.info("Waiting for Ollama to be ready...")
    session = create_session()
    max_retries = 30
    for i in range(max_retries):
        try:
            response = session.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                logger.info("Successfully connected to Ollama")
                break
        except:
            if i == max_retries - 1:
                logger.error("Could not connect to Ollama after maximum retries")
                sys.exit(1)
            logger.info(f"Waiting for Ollama... (attempt {i+1}/{max_retries})")
            time.sleep(2)

    app.run(host='0.0.0.0', port=5001)
