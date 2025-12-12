from flask import Flask, render_template, request, jsonify
from llm_client import generate_reply

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(force=True)
        mode = data.get("mode", "support")
        messages = data.get("messages", [])
        prev_id = data.get("previous_response_id")  # 可選：前端有傳再用

        reply_text, response_id = generate_reply(
            mode=mode,
            messages=messages,
            previous_response_id=prev_id,
        )

        return jsonify({
            "reply": reply_text,
            "response_id": response_id,  # 可選：前端要存就拿這個
        })


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
