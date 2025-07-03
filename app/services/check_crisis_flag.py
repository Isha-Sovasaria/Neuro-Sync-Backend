from datetime import timedelta
from app.db import get_connection
def check_crisis_flags(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, timestamp
        FROM chats
        WHERE user_id = %s
          AND crisis_level = 'suicidal ideation'
          AND DATE(timestamp) = CURRENT_DATE
        ORDER BY timestamp;
    """, (user_id,))
    today_crises = cur.fetchall()

    first_crisis_today = len(today_crises) == 1

    crisis_count_today = len(today_crises)
    spaced_out_crises = False
    if crisis_count_today >= 3:
        cur.execute("""
            SELECT id, crisis_level
            FROM chats
            WHERE user_id = %s
              AND DATE(timestamp) = CURRENT_DATE
            ORDER BY timestamp;
        """, (user_id,))
        all_today_chats = cur.fetchall()

        crisis_indices = [i for i, row in enumerate(all_today_chats) if row[1] == 'yes']
        spaced_out_crises = True
        for i in range(1, len(crisis_indices)):
            if crisis_indices[i] - crisis_indices[i-1] < 3:
                spaced_out_crises = False
                break

    cur.execute("""
        SELECT DATE(timestamp)
        FROM chats
        WHERE user_id = %s AND crisis_level = 'suicidal ideation'
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp) DESC
        LIMIT 3;
    """, (user_id,))
    dates = [row[0] for row in cur.fetchall()]
    has_consecutive_days = (
        len(dates) == 3 and
        dates[0] - dates[1] == timedelta(days=1) and
        dates[1] - dates[2] == timedelta(days=1)
    )

    cur.close()
    conn.close()

    return first_crisis_today, spaced_out_crises, has_consecutive_days