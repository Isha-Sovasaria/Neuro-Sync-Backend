from flask import Blueprint, request, jsonify
from app.db import get_connection
from app.services.get_or_create_user import get_or_create_user
import uuid
from .chatbot import chatbot_bp
from datetime import datetime

@chatbot_bp.route("/new", methods=["POST"])
def start_new_conversation():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email")
    conversation_id = data.get("conversation_id")

    if not email or not conversation_id:
        return jsonify({"error": "'email' and 'conversation_id' are required"}), 422

    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        return jsonify({"error": "Invalid UUID format for conversation_id"}), 400

    try:
        user_id = get_or_create_user(email)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM conversations WHERE conversation_id = %s", (str(conversation_uuid),))
        if cur.fetchone():
            return jsonify({"error": "Duplicate conversation_id"}), 409

        cur.execute("""
            INSERT INTO conversations (conversation_id, user_id, start_time)
            VALUES (%s, %s, %s)
        """, (str(conversation_uuid), user_id, datetime.now()))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "message": "New conversation started",
            "conversation_id": str(conversation_uuid),
        }), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to create conversation",
            "details": str(e)
        }), 500
