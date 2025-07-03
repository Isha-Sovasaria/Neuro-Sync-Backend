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
    crisis_level='none'
):
    conn = get_connection()
    cur = conn.cursor()

    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO users (email)
        VALUES (%s)
        ON CONFLICT (email) DO NOTHING;
    """, (email,))

    cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
    user_id = cur.fetchone()[0]

    emotion = emotion or []
    emotion_confidence = emotion_confidence or []

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