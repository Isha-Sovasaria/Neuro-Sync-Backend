from datetime import datetime, date
from app.db import get_connection

def get_or_create_user(email):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (email)
        VALUES (%s)
        ON CONFLICT (email) DO NOTHING;
    """, (email,))
    conn.commit()

    cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
    user_id = cur.fetchone()[0]

    cur.close()
    conn.close()
    return user_id


def mark_user_login(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET last_login = %s
        WHERE id = %s;
    """, (datetime.now(), user_id))

    cur.execute("""
        INSERT INTO streaks (user_id, date_logged)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """, (user_id, date.today()))

    conn.commit()
    cur.close()
    conn.close()