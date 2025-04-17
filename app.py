from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
import time

# Load API key from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
CORS(app)

# Your Assistant ID
ASSISTANT_ID = "asst_BtudxTEP0qPuPmoDqnlmjSY9"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    if not user_input:
        return jsonify({'reply': 'Please enter a message.'})

    try:
        thread = openai.beta.threads.create()

        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({'reply': 'Sorry, something went wrong.'})
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value
        return jsonify({'reply': reply})

    except Exception as e:
        print("🔥 Error:", e)
        return jsonify({'reply': f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
