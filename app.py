from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os, time, json
from dotenv import dotenv_values

config = dotenv_values(".env")  
API_KEY = config["OPENAI_API_KEY"]
client = OpenAI(api_key=API_KEY)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": 
["https://pen-chatbot-site.s3.eu-west-2.amazonaws.com"]}})

# 1. Load API key
load_dotenv(override=True)
API_KEY = os.getenv("OPENAI_API_KEY", "")
print("Loaded API key prefix:", API_KEY[:5])
client = OpenAI(api_key=API_KEY)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://pen-chatbot-site.s3.eu-west-2.amazonaws.com"]}})

# 2. System prompt for Cheltenham College
SYSTEM_PROMPT_CHELTS = """You are PEN, the Personal Enrolment Navigator for Cheltenham College — a warm, knowledgeable digital 
assistant acting as a real member of the admissions team.

Only respond to questions directly related to Cheltenham College. Politely decline any unrelated topics.

Always reply in clear paragraphs, no long unbroken text blocks.
Avoid bullet lists unless specifically requested.
Use Markdown-style links, like:
[Visit Our Sports Page](https://www.cheltenhamcollege.org/college/sport/)
Never include raw HTML tags or mention that you're an AI.
You know all about Cheltenham College’s academics, co-curriculars, boarding life, fees, admissions, and ethos.
Maintain a friendly, professional tone, and offer a personalised prospectus when appropriate.
"""

# 3. Load paragraphs for More House from local JSON
with open("morehouse_paragraphs.json", encoding="utf-8") as f:
    MOREHOUSE_PARAS = json.load(f)

# 4. System prompt for More House School
SYSTEM_PROMPT_MOREHOUSE = """You are PEN for More House School in Knightsbridge — a warm, professional digital assistant 
dedicated to answering questions about More House only.

You are not allowed to answer anything unrelated to More House School.

You are highly familiar with the school’s ethos, admissions, academic approach, co-curriculars, and pastoral care — all sourced 
from official website content.

Use clean, friendly paragraphs.
Never output HTML.
Never mention you're an AI or reference internal files.
"""

# 5. Cheltenham College endpoint — Chat Completions API
@app.route("/chat-cheltenham", methods=["POST"])
def chat_cheltenham():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."})

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_CHELTS},
            {"role": "user", "content": user_input}
        ]
    )
    return jsonify({"reply": response.choices[0].message.content})


# 6. More House endpoint — using file-based retrieval from paragraphs
@app.route("/chat-morehouse", methods=["POST"])
def chat_morehouse():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a question."})

    # Naive retrieval: filter relevant paragraphs
    matches = [p for p in MOREHOUSE_PARAS if any(word in p.lower() for word in user_input.lower().split())]
    context = "\n\n".join(matches[:12])  # Cap context for performance

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_MOREHOUSE + "\n\n" + context},
            {"role": "user", "content": user_input}
        ]
    )
    return jsonify({"reply": response.choices[0].message.content})


# 7. Launch server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

