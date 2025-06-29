from flask import Blueprint, request, jsonify
from app.services.chat_with_gemini import chat_with_gemini
from app.services.get_or_create_user import get_or_create_user, mark_user_login

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON."}), 400

        email = data.get("email")
        user_message = data.get("text", "").strip()
        conversation_id = data.get("conversation_id")
        emotion = data.get("emotion")
        confidence = data.get("confidence") 

        if not email or not user_message:
            return jsonify({"error": "Both 'email' and 'text' fields are required."}), 422

        user_id = get_or_create_user(email)

        mark_user_login(user_id)

        reply, updated_conversation_id, emotion, crisis_data,redirect= chat_with_gemini(
            user_input=user_message,
            email=email,
            conversation_id=conversation_id,
            emotion=emotion,
            confidence_scores=confidence
        )

        return jsonify({
            "reply": reply,
            "user_id": user_id,
            "conversation_id": updated_conversation_id,
            "emotion": emotion,
            "crisis_data":crisis_data,
            "redirect":redirect
        }), 200

    except TimeoutError:
        return jsonify({"error": "The request to the Gemini API timed out."}), 504

    except ConnectionError:
        return jsonify({"error": "Failed to connect to the Gemini API."}), 502

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "An unexpected error occurred.",
            "details": str(e)
        }), 500
