# AI Chat Assistant - Flask Web Application

## Description
A fully featured Flask-based web application with agentic and multimodal 
capabilities.

The application features a chat interface that supports text and image inputs,
persistent memory, conversation history, and a suite of AI tools.

## Features
- **Text chat** with AI assistant (qwen3.5:2b-q4_K_M via Ollama)
- **Image understanding** — upload images and ask questions about them
- **Persistent memory** — say "remember [something]" to save facts
- **Conversation history** — all chats saved to JSON with timestamps
- **AI Tools:**
  - Calculator — evaluates math expressions
  - Web search — DuckDuckGo search
  - Wikipedia lookup — fetches article summaries
  - Python executor — runs Python code snippets

## Requirements
- Docker container with Python 3.10+
- Ollama installed and running
- qwen3.5:2b-q4_K_M model pulled

## Installation

### 1. Pull the model
```bash
ollama pull qwen3.5:2b-q4_K_M
```

### 2. Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Run the application
```bash
python3 app.py
```

### 4. Open in browser
http://localhost:8888

## Project Structure

flask_ai_app/
├── app.py                        # Main Flask application
├── agent.py                      # AI agent and tools
├── memory.py                     # JSON memory management
├── templates/
│   └── index.html                # Chat UI
├── static/
│   └── uploads/                  # Uploaded images
├── user_config/
│   ├── 25105700.json             # User memories and summary
│   └── 25105700_history.json     # Full conversation history
├── requirements.txt
└── README.md


## Usage Examples
- **Math:** "what is 25 multiplied by 48?"
- **Search:** "search for latest AI news"
- **Memory:** "remember I am studying AI at university"
- **Wikipedia:** "tell me about the Eiffel Tower"
- **Image:** Upload an image and ask "what do you see?"
