from collections import Counter
import json
from datetime import date
from app.db import get_connection

def update_daily_emotion_summary(user_id, summary_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT emotion[1]
        FROM chats
        WHERE user_id = %s AND DATE(timestamp) = %s;
    """, (user_id, summary_date))
    rows = cur.fetchall()
    raw_emotions = [row[0] for row in rows if row[0] is not None]

    emotion_category_map = {
        "anger": "anger", "frustration": "anger", "irritation": "anger", "resentment": "anger",
        "anxiety": "anxiety", "fear": "anxiety", "nervousness": "anxiety", "panic": "anxiety",
        "overwhelmed": "anxiety", "insecurity": "anxiety", "stress": "anxiety", "confusion": "anxiety",
        "sadness": "sadness", "despair": "sadness", "disappointment": "sadness", "hopelessness": "sadness",
        "grief": "sadness", "helplessness": "sadness", "hurt": "sadness", "loneliness": "sadness",
        "regret": "sadness", "worthlessness": "sadness",
        "shame": "shame", "guilt": "shame", "embarrassment": "shame",
        "calm": "calm", "relief": "calm", "neutral": "calm", "satisfaction": "calm",
        "happiness": "positive", "joy": "positive", "love": "positive", "contentment": "positive",
        "hope": "positive", "pride": "positive", "gratitude": "positive",
        "numb": "disengaged", "fatigue": "disengaged", "exhaustion": "disengaged", "nostalgia": "disengaged",
        "pain": "disengaged", "disgust": "disengaged", "discomfort": "disengaged"
    }

    intensity_weights = {
        "positive": -1.0,
        "calm": -0.5,
        "disengaged": 1.0,
        "shame": 1.2,
        "sadness": 1.5,
        "anxiety": 2.0,
        "anger": 2.5,
        "other": 0.5
    }

    categorized = [emotion_category_map.get(e, "other") for e in raw_emotions]

    total = len(categorized)
    if total == 0:
        cur.close()
        conn.close()
        return

    freq = Counter(categorized)
    averages = {k: round(v / total, 3) for k, v in freq.items()}

    dominant_emotion = max(freq.items(), key=lambda x: x[1])[0]

    emotional_intensity = round(
        sum(freq[cat] * intensity_weights.get(cat, 0) for cat in freq) / total,
        3
    )

    cur.execute("""
        INSERT INTO daily_emotion_summaries (
            user_id, summary_date, emotion_averages, total_entries,
            dominant_emotion, emotional_intensity
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, summary_date)
        DO UPDATE SET
            emotion_averages = EXCLUDED.emotion_averages,
            total_entries = EXCLUDED.total_entries,
            dominant_emotion = EXCLUDED.dominant_emotion,
            emotional_intensity = EXCLUDED.emotional_intensity;
    """, (user_id, summary_date, json.dumps(averages), total, dominant_emotion, emotional_intensity))

    conn.commit()
    cur.close()
    conn.close()