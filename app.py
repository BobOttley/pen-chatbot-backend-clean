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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)

