import uuid
import psycopg2
from app.db import get_connection

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # Enable pgvector for embeddings
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # === USERS Table ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            last_login TIMESTAMPTZ
        );
    """)
    cur.execute("""CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ DEFAULT NOW(),

    -- Fields to track emotional shifts
    last_emotion_shift TEXT,
    last_emotion_shift_time TIMESTAMPTZ
);""")
   

    # === CHATS Table ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE CASCADE,
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            emotion TEXT[],
            emotion_confidence FLOAT[],
            crisis_level TEXT,
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            embedding VECTOR(1024)
        );
    """)

    cur.execute("""
CREATE TABLE IF NOT EXISTS daily_emotion_summaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    summary_date DATE NOT NULL,
    emotion_averages JSONB,
    total_entries INTEGER DEFAULT 0,
    dominant_emotion TEXT,
    emotional_intensity FLOAT,
    UNIQUE (user_id, summary_date)
);
""")
    # === STREAKS Table ===
    cur.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date_logged DATE NOT NULL,
            UNIQUE(user_id, date_logged)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()