# Test Script Migration

1. Start the local LLM (Ollama)
- Install Ollama
- Pull a model:
  - ollama pull mistral
- ollama serve
- Ensure Ollama is running: http://localhost:11434

2. Python setup
pip install -r requirements.txt

3. Run backend
uvicorn app:app --reload
Backend: http://127.0.0.1:8000

uvicorn app:app --reload --host 127.0.0.1 --port 8000

4. Run UI
streamlit run UI.py

Output
Generated scripts saved in ./output
