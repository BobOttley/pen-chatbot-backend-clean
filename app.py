from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load your OpenAI key
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=API_KEY)

# 2. Flask + CORS
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
Never include raw HTML tags or mention that you're an AI.
You know all about Cheltenham College’s academics, co‑curriculars,
boarding life, fees, admissions, and ethos.
Maintain a friendly, professional tone, and offer a personalised
prospectus when appropriate.
"""

# 4. Load More House paragraphs from local JSON
with open("morehouse_paragraphs.json", encoding="utf-8") as f:
    MOREHOUSE_PARAS = json.load(f)

# Build a single block of reference text for More House
COMBINED_MOREHOUSE = "\n\n".join(MOREHOUSE_PARAS)

# 5. System prompt for More House School (embedding your scraped content)
SYSTEM_PROMPT_MOREHOUSE = f"""\
You are PEN for More House School in Knightsbridge — a warm, professional
digital assistant dedicated to answering questions about More House only.

Only respond to questions directly related to More House School. Politely
decline any unrelated topics.

Use the following reference information from the official website in your
responses when helpful:

{COMBINED_MOREHOUSE}

Always reply in clean, friendly paragraphs.
Never output raw HTML or mention that you are an AI or reference internal files.
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

    # Simple bag‑of‑words retrieval of relevant paragraphs
    matches = [
        p for p in MOREHOUSE_PARAS
        if any(tok in p.lower() for tok in user_input.lower().split())
    ]
    context = "\n\n".join(matches[:10])  # cap at 10 paragraphs

    full_system = SYSTEM_PROMPT_MOREHOUSE + "\n\nContext:\n" + context

    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        temperature=0.2,
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user",   "content": user_input}
        ]
    )
    return jsonify({"reply": resp.choices[0].message.content})

# 8. Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

