from app.db import get_connection
from datetime import datetime

def fetch_relevant_chats(email, embedding, conversation_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_id = cur.fetchone()[0]

    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

    cur.execute("""
        SELECT question, response
        FROM chats
        WHERE user_id = %s AND conversation_id <> %s
        ORDER BY embedding <#> %s::vector <0.5
        LIMIT 10;
    """, (user_id, conversation_id, embedding_str))
    similar_chats = cur.fetchall()

    cur.execute("""
        SELECT question, response
        FROM chats
        WHERE user_id = %s AND conversation_id = %s
        ORDER BY timestamp ASC;
    """, (user_id, conversation_id))
    conversation_chats = cur.fetchall()

    cur.close()
    conn.close()

    return similar_chats, conversation_chats