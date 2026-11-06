import ollama
import ast
import operator
import subprocess
import tempfile
import os
import json
import wikipediaapi
import base64
from ddgs import DDGS
from PIL import Image
import io

MODEL = "qwen3.5:2b-q4_K_M"


# TOOLS


def calculator(expression: str) -> str:
    """Safely evaluate a math expression."""
    _SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv, ast.USub: operator.neg,
    }
    def _safe_eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
        else:
            raise ValueError(f"Unsupported expression: {ast.dump(node)}")
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        return f"{expression.strip()} = {result}"
    except Exception as e:
        return f"Calculator error: {str(e)}"


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return f"No results found for: {query}"
        parts = []
        for i, r in enumerate(results, 1):
            parts.append(f"[{i}] {r['title']}\n    {r['body']}\n    Source: {r['href']}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"Search error: {str(e)}"


def wikipedia_lookup(topic: str) -> str:
    """Fetch a Wikipedia article summary."""
    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="FlaskAIApp/1.0 (educational)", language="en"
        )
        page = wiki.page(topic)
        if not page.exists():
            return f"Wikipedia article not found for: {topic}"
        return f"Wikipedia — {page.title}:\n{page.summary[:1500]}"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


def python_exec(code: str) -> str:
    """Execute a Python code snippet safely."""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(code)
            fname = f.name
        result = subprocess.run(
            ["python3", fname],
            capture_output=True, text=True, timeout=10
        )
        os.unlink(fname)
        output = result.stdout or result.stderr
        return output.strip() if output.strip() else "Code ran with no output."
    except subprocess.TimeoutExpired:
        return "Code execution timed out after 10 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"

def resize_image(image_data: bytes, max_size: int = 512) -> bytes:
    """Resize image to reduce processing time."""
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail((max_size, max_size))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()



# TOOL SCHEMAS


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a mathematical expression. Use this for any arithmetic or math calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression e.g. '(45 * 12) + 98'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information. Use this for recent events, news, or facts you don't know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_lookup",
            "description": "Look up a topic on Wikipedia. Use this for general knowledge and encyclopedic information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The Wikipedia topic to search for"
                    }
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "python_exec",
            "description": "Execute a Python code snippet. Use this for complex calculations or data processing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Valid Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    },
]

# Map tool names to actual functions
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "web_search": web_search,
    "wikipedia_lookup": wikipedia_lookup,
    "python_exec": python_exec,
}



# MEMORY DETECTION


def check_for_memory(user_message: str) -> str | None:
    """Check if user wants to save a memory."""
    msg = user_message.strip().lower()
    if msg.startswith("remember "):
        return user_message[9:].strip()
    return None


# MAIN AGENT FUNCTION

def run_agent(user_message: str, image_data: bytes = None,
              memories: list = None, conversation_summary: list = None) -> str:
    """
    Main agent function. Handles text + optional image.
    Uses native tool calling with a loop.
    """

    # Build system prompt including memories
    memory_text = ""
    if memories:
        memory_items = "\n".join([f"- {m['text']}" for m in memories])
        memory_text = f"\n\nUser memories:\n{memory_items}"

    summary_text = ""
    if conversation_summary:
        recent = conversation_summary[-3:]  # only last 3 summaries
        summary_text = "\n\nRecent conversation context:\n" + \
            "\n".join([s['summary'] for s in recent])

    system_prompt = f"""You are a helpful AI assistant with access to tools.
Use tools when needed to give accurate answers.
When the user says 'remember [something]', confirm you've saved it.
Always be concise and helpful.{memory_text}{summary_text}"""

    # Build initial message
    message = {"role": "user", "content": user_message}

    # Add image if provided
    if image_data:
        resized = resize_image(image_data)
        message["images"] = [resized]

    messages = [
        {"role": "system", "content": system_prompt},
        message
    ]

    # Agent loop - keeps going until model gives final answer
    max_iterations = 5
    for iteration in range(max_iterations):

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS if not image_data else None,  # tools disabled with images
            think=False,
            options={"num_ctx": 2048}
        )

        response_message = response["message"]

        # Check if model wants to call a tool
        if response_message.get("tool_calls"):
            # Add model's response to message history
            messages.append(response_message)

            # Execute each tool the model requested
            for tool_call in response_message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                if tool_name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[tool_name](**tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"

                # Add tool result back to messages
                messages.append({
                    "role": "tool",
                    "content": str(result)
                })

        else:
            # No tool call — this is the final answer
            return response_message["content"]

    return "I reached the maximum number of steps. Please try a simpler question."

def warmup_model():
    """Pre-load model into RAM on startup."""
    print("Warming up model...")
    ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "hi"}],
        think=False,
        options={"num_ctx": 2048}
    )
    print("Model ready!")


