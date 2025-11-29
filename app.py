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

        # 呼叫你封裝好的 LLM
        reply = generate_reply(mode=mode, messages=messages)

        return jsonify({"reply": reply})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
