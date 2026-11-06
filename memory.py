import json
import os
from datetime import datetime

STUDENT_ID = "00"
STUDENT_NAME = "X Y"
USER_CONFIG_DIR = "user_config"
CONFIG_FILE = os.path.join(USER_CONFIG_DIR, f"{STUDENT_ID}.json")
HISTORY_FILE = os.path.join(USER_CONFIG_DIR, f"{STUDENT_ID}_history.json")

def initialize_files():
    """Create JSON files if they don't exist"""
    os.makedirs(USER_CONFIG_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "user_id": STUDENT_ID,
            "name": STUDENT_NAME,
            "memories": [],
            "conversation_summary": []
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created {CONFIG_FILE}")

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f, indent=2)
        print(f"Created {HISTORY_FILE}")

def load_config():
    """Load user config file"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save user config file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def add_memory(memory_text):
    """Add a new memory to config file"""
    config = load_config()
    config["memories"].append({
        "text": memory_text,
        "timestamp": datetime.now().isoformat()
    })
    save_config(config)

def add_to_history(prompt, reply, agent="qwen3.5:2b-q4_K_M"):
    """Append full conversation entry to history file"""
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)

    history.append({
        "datetime": datetime.now().isoformat(),
        "user_id": STUDENT_ID,
        "prompt": prompt,
        "agent": agent,
        "reply": reply
    })

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_memories():
    """Get all memories"""
    config = load_config()
    return config.get("memories", [])

def update_summary(summary_text):
    """Update conversation summary in config"""
    config = load_config()
    config["conversation_summary"].append({
        "summary": summary_text,
        "timestamp": datetime.now().isoformat()
    })
    save_config(config)