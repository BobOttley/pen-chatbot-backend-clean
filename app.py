from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
import time

# Load API key from .env file
load_dotenv()

# Create a new OpenAI client instance
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        # Start a new thread
        thread = client.beta.threads.create()

        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Run the assistant on the thread
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for the run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return jsonify({'reply': 'Sorry, something went wrong.'})
            time.sleep(1)

        # Get the assistant's reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value
        return jsonify({'reply': reply})

    except Exception as e:
        print("🔥 Error:", e)
        return jsonify({'reply': f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

