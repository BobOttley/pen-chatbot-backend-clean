import os
import json
from flask import Flask, jsonify
from openai import OpenAI
import logging
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('app.log')]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load OpenAI key
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logger.critical("OPENAI_API_KEY environment variable not set")
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=API_KEY)

# Load data
try:
    with open("morehouse_paragraphs.json", encoding="utf-8") as f:
        MOREHOUSE_PARAS = json.load(f)
    logger.info("Successfully loaded morehouse_paragraphs.json")
except Exception as e:
    logger.critical("Failed to load morehouse_paragraphs.json: %s", e)
    raise

@app.route("/")
def health():
    return jsonify({"status": "ok"})
@app.route("/chat-morehouse", methods=["POST"])
def chat_morehouse():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Missing message in request body"}), 400

        user_message = data["message"]
        context = "\n".join(MOREHOUSE_PARAS)
        prompt = f"Answer the following question based on the More House School information provided:\n\n{context}\n\nQuestion: {user_message}\n\nAnswer:"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )

        answer = response.choices[0].message.content.strip()
        return jsonify({"response": answer})

    except Exception as e:
        logger.error("Error in /chat-morehouse: %s", e)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # 👈 this matches Render's setting
    app.run(host="0.0.0.0", port=port)

