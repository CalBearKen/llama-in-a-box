Setup instructions:

run setup.bat

How to use:
POST request to http://localhost:5001/api/generate
curl http://localhost:11434/api/generate \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{"model": "llama3.1", "prompt": "Hello, how are you?"}'


TODO: 
- create Linux versions of the batch scripts