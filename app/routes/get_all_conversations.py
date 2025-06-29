from flask import request, jsonify
from .chatbot import chatbot_bp
from app.db import get_connection


@chatbot_bp.route("/chats", methods=["GET"])
def get_all_conversations():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Fetch user_id from email
        cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
        user_row = cur.fetchone()
        if not user_row:
            cur.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404

        user_id = user_row[0]

        # Fetch conversation IDs with latest chat timestamps (or NULL if no chats)
        cur.execute("""
            SELECT c.conversation_id, MAX(ch.timestamp) AS latest
            FROM conversations c
            LEFT JOIN chats ch ON c.conversation_id = ch.conversation_id
            WHERE c.user_id = %s
            GROUP BY c.conversation_id
            ORDER BY latest DESC NULLS LAST;
        """, (user_id,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Return list of conversation IDs
        return jsonify([{"id": row[0]} for row in rows]), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch conversations",
            "details": str(e)
        }), 500

@chatbot_bp.route("/chats/<chat_id>", methods=["GET"])
def get_chat_messages(chat_id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Confirm that conversation exists (optional but safer)
        cur.execute("SELECT 1 FROM conversations WHERE conversation_id = %s;", (chat_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Conversation not found"}), 404

        # Fetch all chat messages in order
        cur.execute("""
            SELECT question, response
            FROM chats
            WHERE conversation_id = %s
            ORDER BY timestamp ASC;
        """, (chat_id,))

        rows = cur.fetchall()
        cur.close()
        conn.close()

        messages = [{"user": q, "bot": r} for q, r in rows]
        return jsonify(messages), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch chat messages",
            "details": str(e)
        }), 500