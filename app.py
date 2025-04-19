import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from openai import OpenAI, OpenAIError
from werkzeug.middleware.proxy_fix import ProxyFix

# 1. Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 2. Load environment variables and validate
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://your-frontend-domain.com").split(",")
if not API_KEY:
    logger.critical("OPENAI_API_KEY is not set in .env file")
    raise EnvironmentError("OPENAI_API_KEY is required")

# 3. Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

# 4. Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
CORS(app, resources={r"/chat-*": {"origins": CORS_ORIGINS}})  # Update CORS_ORIGINS in .env

# 5. Initialize rate limiter (IP-based)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["60 per minute"],
    storage_uri=os.getenv("REDIS_URL", "memory://")  # Use Redis in production, memory in dev
)

# 6. Constants and configuration
MAX_INPUT_LENGTH = 500

# System prompts
SYSTEM_PROMPT_CHELTS = """\
You are PEN, the Personal Enrolment Navigator for Cheltenham College — a
warm, knowledgeable digital assistant acting as a real member of the
admissions team.

Always respond in clear, confident paragraphs.
Never output long unbroken blocks of text.
Avoid bullet‑lists unless the user explicitly asks for one.
Format every link in Markdown only, for example:
[Visit Our Sports Page](https://www.cheltenhamcollege.org/college/sport/)
Never include raw HTML tags or mention that you’re an AI.
You know all about Cheltenham College’s academics, co‑curriculars,
boarding life, fees, admissions, and ethos.
Maintain a friendly, professional tone, and offer a personalised
prospectus when appropriate.
"""

SYSTEM_PROMPT_MOREHOUSE = """\
You are PEN for More House School in Knightsbridge — a warm, professional
digital assistant dedicated to answering questions about More House only.

Only respond to questions directly related to More House School. Politely
decline any unrelated topics.

Use the provided context to inform your answers when helpful.

Always reply in clean, friendly paragraphs.
Never output raw HTML or mention that you are an AI or reference internal files.
"""

# 7. Load More House paragraphs (cached at startup)
try:
    with open("morehouse_paragraphs.json", encoding="utf-8") as f:
        MOREHOUSE_PARAS = json.load(f)
    logger.info("Successfully loaded morehouse_paragraphs.json")
except Exception as e:
    logger.critical("Failed to load morehouse_paragraphs.json: %s", e)
    raise

# 8. Utility function for OpenAI API calls
@limiter.limit("60 per minute")
def call_openai_api(system_prompt, user_input):
    try:
        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        return resp.choices[0].message.content
    except OpenAIError as e:
        logger.error("OpenAI API error: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error in OpenAI API call: %s", e)
        raise

# 9. Health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "morehouse_paras_loaded": len(MOREHOUSE_PARAS) > 0,
        "api_key_configured": bool(API_KEY)
    }
    return jsonify(status)

# 10. Cheltenham College chat endpoint
@app.route("/chat-cheltenham", methods=["POST"])
def chat_cheltenham():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"reply": "Please enter a question."}), 400
        if len(user_input) > MAX_INPUT_LENGTH:
            return jsonify({"reply": f"Input exceeds {MAX_INPUT_LENGTH} characters."}), 400

        logger.info("Processing Cheltenham query: %s", user_input)
        reply = call_openai_api(SYSTEM_PROMPT_CHELTS, user_input)
        return jsonify({"reply": reply})
    except ValueError:
        logger.warning("Invalid JSON in request")
        return jsonify({"reply": "Invalid request format."}), 400
    except OpenAIError:
        logger.error("OpenAI error in chat-cheltenham")
        return jsonify({"reply": "Sorry, I'm having trouble processing that right now."}), 500
    except Exception as e:
        logger.error("Error in chat-cheltenham: %s", e)
        return jsonify({"reply": "Sorry, something went wrong."}), 500

# 11. More House chat endpoint
@app.route("/chat-morehouse", methods=["POST"])
def chat_morehouse():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"reply": "Please enter a question."}), 400
        if len(user_input) > MAX_INPUT_LENGTH:
            return jsonify({"reply": f"Input exceeds {MAX_INPUT_LENGTH} characters."}), 400

        logger.info("Processing More House query: %s", user_input)
        
        # Filter paragraphs for open day events with dates/times
        event_keywords = ["open morning", "open evening", "open day"]
        has_date_or_time = ["2025", "2026", "am", "pm", ":"]
        matches = [
            para for para in MOREHOUSE_PARAS
            if any(ek in para.lower() for ek in event_keywords)
            and any(ht in para.lower() for ht in has_date_or_time)
        ]
        
        # Combine matches, trim to 4000 characters
        combined = "\n\n".join(matches)
        context = combined[:4000]
        logger.info("Context size: %s characters", len(context))
        
        system_prompt = f"{SYSTEM_PROMPT_MOREHOUSE}\n\nContext:\n{context}"
        reply = call_openai_api(system_prompt, user_input)
        return jsonify({"reply": reply})
    except ValueError:
        logger.warning("Invalid JSON in request")
        return jsonify({"reply": "Invalid request format."}), 400
    except OpenAIError:
        logger.error("OpenAI error in chat-morehouse")
        return jsonify({"reply": "Sorry, I'm having trouble processing that right now."}), 500
    except Exception as e:
        logger.error("Error in chat-morehouse: %s", e)
        return jsonify({"reply": "Sorry, something went wrong."}), 500

# 12. Run the app
# For production, use: gunicorn app:app --workers=2 --bind=0.0.0.0:10000
if __name__ == "__main__":
    logger.info("Starting Flask application on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)