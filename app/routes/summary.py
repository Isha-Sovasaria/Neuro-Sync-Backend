from flask import Blueprint, request, jsonify
from app.db import get_connection
from datetime import timedelta, date
summary_bp = Blueprint("summary", __name__)

@summary_bp.route("/emotion-summary/daily", methods=["GET"])
def get_daily_summary():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_row = cur.fetchone()
    if not user_row:
        return jsonify({"error": "User not found"}), 404

    user_id = user_row[0]

    cur.execute("""
        SELECT summary_date, emotion_averages, dominant_emotion
        FROM daily_emotion_summaries
        WHERE user_id = %s AND summary_date = CURRENT_DATE;
    """, (user_id,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"message": "No emotion summary found for today."}), 404

    summary_date, emotion_averages, dominant_emotion = row

    emotion_list = [{"emotion": k, "value": round(v, 4)} for k, v in emotion_averages.items()]

    return jsonify({
        "date": summary_date.isoformat(),
        "dominant_emotion": dominant_emotion,
        "data": emotion_list
    })


@summary_bp.route("/emotion-summary/weekly-intensity-labels", methods=["GET"])
def get_weekly_emotion_intensity():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_row = cur.fetchone()
    if not user_row:
        return jsonify({"error": "User not found"}), 404

    user_id = user_row[0]
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    cur.execute("""
        SELECT summary_date, dominant_emotion, emotional_intensity
        FROM daily_emotion_summaries
        WHERE user_id = %s AND summary_date BETWEEN %s AND %s
        ORDER BY summary_date;
    """, (user_id, monday, today))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    data = [
        {
            "date": row[0].isoformat(),
            "dominant_emotion": row[1],
            "intensity": float(row[2]) if row[2] is not None else 0.0
        }
        for row in rows
    ]
    return jsonify(data)