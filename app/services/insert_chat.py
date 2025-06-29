from app.db import get_connection
import uuid

def insert_chat(
    email,
    question,
    response,
    emotion,
    embedding,
    emotion_confidence=None,
    conversation_id=None,
    crisis_level='none'  # ✅ Default to 'none' unless specified
):
    conn = get_connection()
    cur = conn.cursor()

    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    # Step 1: Ensure user exists
    cur.execute("""
        INSERT INTO users (email)
        VALUES (%s)
        ON CONFLICT (email) DO NOTHING;
    """, (email,))

    # Step 2: Get user_id
    cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
    user_id = cur.fetchone()[0]

    # Step 3: Default fallbacks for optional fields
    emotion = emotion or []
    emotion_confidence = emotion_confidence or []

    # Step 4: Insert chat
    cur.execute("""
        INSERT INTO chats (
            user_id, question, response, emotion,
            emotion_confidence, embedding, crisis_level, conversation_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, (
        user_id,
        question,
        response,
        emotion,
        emotion_confidence,
        embedding,
        crisis_level,
        conversation_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return conversation_id
