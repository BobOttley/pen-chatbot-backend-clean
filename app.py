from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os, time, json
from collections import Counter
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────
# 1) Configuration
# ─────────────────────────────────────────────────────────────
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY", "")
print("Loaded API key prefix:", API_KEY[:5])
openai.api_key = API_KEY

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────────
# 2) Load More House scraped content & retrieval helper
# ─────────────────────────────────────────────────────────────
with open("morehouse_paragraphs.json", encoding="utf-8") as f:
    MOREHOUSE_PARAS = json.load(f)

def retrieve_snippets(question, paras, k=3):
    q_words = Counter(question.lower().split())
    scored = []
    for p in paras:
        score = sum(q_words[w] for w in set(p.lower().split()) if w in q_words)
        if score:
            scored.append((score, p))
    top = [p for _, p in sorted(scored, reverse=True)[:k]]
    return top if top else paras[:k]

# ─────────────────────────────────────────────────────────────
# 3) System prompts
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are PEN, the Personal Enrolment Navigator for Cheltenham College — a warm, knowledgeable digital assistant acting as a real member of the admissions team.

Always respond in clear, confident paragraphs.
Never output long unbroken blocks of text.
Avoid bullet‑lists unless the user explicitly asks for one.
Format every link in Markdown only.
Do not emit any HTML tags or attributes.
Never mention you’re an AI or reference internal documents or files.
You know all about Cheltenham College’s academics, boarding, co‑curriculars, fees, pastoral care, and facilities.
Maintain a friendly, professional tone, invite follow‑up questions, and offer a personalised prospectus where appropriate.

Important:
If the user’s question is not about Cheltenham College, reply:
“I’m sorry, but I can only answer questions about Cheltenham College.”
"""

SYSTEM_PROMPT_MORE = """You are PEN, the Personal Enrolment Navigator for More House School — a warm, knowledgeable digital assistant dedicated specifically to More House.

Always respond in clear, confident paragraphs.
Never output long unbroken blocks of text.
Avoid bullet‑lists unless the user explicitly asks for one.
Format every link in Markdown only.
Do not emit any HTML tags or attributes.
Never mention you’re an AI or reference internal documents or files.
You know all about More House’s programmes, boarding, pastoral care, co‑curriculars, term dates, and events.
Maintain a friendly, professional tone, invite follow‑up questions, and offer a personalised prospectus where appropriate.

Important:
If the user’s question is not about More House School, reply:
“I’m sorry, but I can only answer questions about More House School.”
"""

# ─────────────────────────────────────────────────────────────
# 4) Cheltenham College endpoint
# ─────────────────────────────────────────────────────────────
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({'reply': 'Please enter a message.'})

    resp = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_input}
        ],
        temperature=0.2
    )
    return jsonify({'reply': resp.choices[0].message.content})

# ─────────────────────────────────────────────────────────────
# 5) More House endpoint (with live retrieval)
# ─────────────────────────────────────────────────────────────
@app.route('/chat-morehouse', methods=['POST'])
def chat_morehouse():
    user_input = request.json.get('message', '').strip()
    if not user_input:
        return jsonify({'reply': 'Please enter a message.'})

    snippets = retrieve_snippets(user_input, MOREHOUSE_PARAS, k=3)
    injected = "Here are some relevant facts from the More House website:\n\n" + "\n\n".join(snippets)

    resp = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT_MORE},
            {"role": "system",  "content": injected},
            {"role": "user",    "content": user_input}
        ],
        temperature=0.2
    )
    return jsonify({'reply': resp.choices[0].message.content})

# ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

