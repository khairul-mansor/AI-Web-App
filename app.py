import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import memory
import agent

app = Flask(__name__)

# Config
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if uploaded file is an allowed image type."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ROUTE 1: Serve chat page
@app.route("/")
def index():
    return render_template("index.html")

# ROUTE 2: Handle chat messages
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Check if user wants to save a memory
    memory_text = agent.check_for_memory(user_message)
    if memory_text:
        memory.add_memory(memory_text)

    # Load memories and summary for context
    memories = memory.get_memories()
    config = memory.load_config()
    summary = config.get("conversation_summary", [])

    # Get image if it was uploaded
    image_data = None
    image_path = data.get("image_path")
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_data = f.read()

    # Run the agent
    reply = agent.run_agent(
        user_message=user_message,
        image_data=image_data,
        memories=memories,
        conversation_summary=summary
    )

    # Save to history
    memory.add_to_history(user_message, reply)

    # Update conversation summary every 5 messages
    with open(f"user_config/25105700_history.json") as f:
        import json
        hist = json.load(f)
    if len(hist) % 5 == 0 and len(hist) > 0:
        memory.update_summary(f"User asked: {user_message[:100]}")

    return jsonify({"reply": reply})

# ROUTE 3: Handle image uploads
@app.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return jsonify({"image_path": filepath})

    return jsonify({"error": "Invalid file type"}), 400

# STARTUP
if __name__ == "__main__":
    memory.initialize_files()
    print("Starting model warmup...")
    agent.warmup_model()
    app.run(host="0.0.0.0", port=8888, debug=False)
