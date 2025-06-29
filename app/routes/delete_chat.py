from app.db import get_connection
from .chatbot import chatbot_bp
from flask import jsonify

@chatbot_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_conversation(chat_id):
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 🧪 Optional: Check if the conversation exists before deleting
        cur.execute("SELECT 1 FROM conversations WHERE conversation_id = %s;", (chat_id,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": "Conversation not found"}), 404

        # 🗑️ Delete conversation — cascades to chats
        cur.execute("DELETE FROM conversations WHERE conversation_id = %s;", (chat_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"message": "Conversation and associated chats deleted"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to delete conversation", "details": str(e)}), 500
