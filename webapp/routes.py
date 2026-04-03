from flask import Blueprint, current_app, jsonify, render_template, request, url_for

from .services.chat_service import answer_question


bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template(
        "index.html",
        chatbot_title=current_app.config["CHATBOT_TITLE"],
    )


@bp.get("/widget")
def widget():
    return render_template(
        "widget.html",
        chatbot_title=current_app.config["CHATBOT_TITLE"],
    )


@bp.get("/embed.js")
def embed_js():
    script = render_template("embed.js")
    return current_app.response_class(
        script,
        mimetype="application/javascript",
    )


@bp.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("message") or "").strip()

    if not question:
        return jsonify({"error": "質問を入力してください。"}), 400

    result = answer_question(
        question=question,
        data_file=current_app.config["DATA_FILE"],
        api_key=current_app.config["GEMINI_API_KEY"],
        model_name=current_app.config["GEMINI_MODEL"],
    )
    return jsonify(result)


@bp.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "chat_api": url_for("main.chat", _external=False),
        }
    )

