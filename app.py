# app.py

import os
import json
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# 1. Load environment and OpenAI client
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY)

# 2. Initialise Flask and enable CORS
app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

# 3. System prompt for Cheltenham College
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

# 4. Base system prompt for More House (context added dynamically)
SYSTEM_PROMPT_MOREHOUSE = """\
You are PEN for More House School in Knightsbridge — a warm, professional
digital assistant dedicated to answering questions about More House only.

Only respond to questions directly related to More House School. Politely
decline any unrelated topics.

Use the provided context to inform your answers when helpful.

Always reply in clean, friendly paragraphs.
Never output raw HTML or mention that you are an AI or reference internal files.
"""

# 5. Load scraped paragraphs for More House
with open("morehouse_paragraphs.json", encoding="utf-8") as f:
    MOREHOUSE_PARAS = json.load(f)

@app.route("/chat-cheltenham", methods=["POST"])
def chat_cheltenham():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."}), 400

    try:
        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_CHELTS},
                {"role": "user",   "content": user_input}
            ]
        )
        return jsonify({"reply": resp.choices[0].message.content})
    except Exception as e:
        print("[ERROR] OpenAI API call failed (Cheltenham):", e)
        return jsonify({"reply": "Sorry, I couldn’t complete your request."}), 500

@app.route("/chat-morehouse", methods=["POST"])
def chat_morehouse():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."}), 400

    # Prioritise paragraphs with open day events that contain real dates/times
    query = user_input.lower()
    event_keywords = ["open morning", "open evening", "open day"]
    has_date_or_time = ["2025", "2026", "am", "pm", ":"]

    matches = [
        para for para in MOREHOUSE_PARAS
        if any(ek in para.lower() for ek in event_keywords)
        and any(ht in para.lower() for ht in has_date_or_time)
    ]

    # Combine all matching paragraphs and trim to 4000 characters max
    combined = "\n\n".join(matches)
    context = combined[:4000]

    try:
        resp = client.chat.completions.create(
            model="gpt-4-turbo",
            temperature=0.2,
            messages=[
                {"role": "system", "content": f"{SYSTEM_PROMPT_MOREHOUSE}\n\nContext:\n{context}"},
                {"role": "user",   "content": user_input}
            ]
        )
        return jsonify({"reply": resp.choices[0].message.content})
    except Exception as e:
        print("[ERROR] OpenAI API call failed (More House):", e)
        return jsonify({"reply": "Sorry, I couldn’t complete your request."}), 500

# 6. Run the app (development server) on port 5001
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

