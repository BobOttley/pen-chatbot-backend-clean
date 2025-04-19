from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load your OpenAI key
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY)

# 2. Flask + CORS
app = Flask(__name__)
CORS(app)

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
Never include raw HTML tags or mention that you're an AI.
You know all about Cheltenham College’s academics, co‑curriculars, 
boarding life, fees, admissions, and ethos.
Maintain a friendly, professional tone, and offer a personalised 
prospectus when appropriate.
"""

# 4. Load More House paragraphs from JSON
with open("morehouse_paragraphs.json", encoding="utf-8") as f:
    MOREHOUSE_PARAS = json.load(f)

# 5. System prompt for More House School
SYSTEM_PROMPT_MOREHOUSE = """\
You are PEN for More House School in Knightsbridge — a warm, professional 
digital assistant dedicated to answering questions about More House only.

Only respond to questions directly related to More House School. Politely 
decline any unrelated topics.

You are highly familiar with the school’s ethos, admissions, academic 
approach, co‑curriculars, sport, and pastoral care — all sourced from 
official website content.

Use clean, friendly paragraphs.
Never output HTML.
Never mention you're an AI or reference internal files.
"""

# 6. Cheltenham endpoint
@app.route("/chat-cheltenham", methods=["POST"])
def chat_cheltenham():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."})

    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_CHELTS},
            {"role": "user",   "content": user_input}
        ]
    )
    return jsonify({"reply": resp.choices[0].message.content})

# 7. More House endpoint — file‑based retrieval
@app.route("/chat-morehouse", methods=["POST"])
def chat_morehouse():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."})

    # naive bag‑of‑words match
    matches = [
        p for p in MOREHOUSE_PARAS
        if any(tok in p.lower() for tok in user_input.lower().split())
    ]
    context = "\n\n".join(matches[:12])  # cap context for performance

    # build system + context
    full_system = SYSTEM_PROMPT_MOREHOUSE + "\n\n" + context
    messages = [
        {"role": "system", "content": full_system},
        {"role": "user",   "content": user_input}
    ]

    # call OpenAI
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        temperature=0.2
    )

    return jsonify({"reply": resp.choices[0].message.content})

# 8. Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

