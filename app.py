import os
import json
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv

# Load .env from the current directory
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv() # Fallback for local dev or environment variables

app = Flask(__name__)

# Load Tours Data with absolute path
tours_path = os.path.join(basedir, "data", "tours.json")
try:
    with open(tours_path, "r", encoding="utf-8") as f:
        tours_data = json.load(f)
except FileNotFoundError:
    print(f"ERROR: tours.json not found at {tours_path}")
    tours_data = {}

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("CRITICAL ERROR: GROQ_API_KEY not found in environment variables.")

# Lazy load or check client
client = None
if api_key:
    client = Groq(api_key=api_key)
else:
    print("WARNING: Groq client not initialized due to missing API key.")

conversation_history = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    try:
        if not client:
            return jsonify({"reply": "System Error: AI service is not configured (missing API key). Please check Vercel environment variables."})

        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        recent_history = conversation_history[-6:]

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are Smith Assistant, the official AI assistant for Travel Smith Goa.

STRICT RESPONSE FORMAT RULES:

When suggesting MULTIPLE tours:

🔹 Tour Name  
🕒 Duration: ...  
📅 Season: ...  
🌟 Highlights: short phrase  

---

When describing ONE tour:

✨ Tour Name  
🕒 Duration: ...  
📅 Season: ...  

🌟 Highlights:
• point  
• point  

IMPORTANT RULES:
- Remember previous conversation context.
- NEVER write long paragraphs.
- Keep answers premium and easy to scan.
- Always prefer Travel Smith tours.

Tour Data:
{tours_data}
"""
                },
                *recent_history
            ],
            temperature=0.4,
        )

        bot_reply = completion.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": bot_reply
        })

        return jsonify({"reply": bot_reply})

    except Exception as e:
        print("GROQ ERROR:", e)
        return jsonify({"reply": "Sorry, something went wrong."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
