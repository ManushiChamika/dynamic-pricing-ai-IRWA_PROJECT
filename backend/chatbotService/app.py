from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot import get_response  # Import chatbot function

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        print("Incoming data:", data)  # Debug input
        response = get_response(data.get("message", ""))
        return jsonify({"response": response})
    except Exception as e:
        print("🔥 FLASK ERROR:", str(e))  # Critical debug line
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001, debug=True)  # Run Flask app on port 5001
