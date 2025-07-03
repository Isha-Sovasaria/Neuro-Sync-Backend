from app.db import get_connection
from app.services.detect_emotional_shift_llm import detect_emotional_shift_llm
from datetime import datetime

def update_emotion_shift_if_detected(
    conversation_id,
    curr_emotion_1, curr_conf_1,
    curr_emotion_2=None, curr_conf_2=None,
    curr_text=""
):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                emotion[1], emotion_confidence[1], 
                emotion[2], emotion_confidence[2], 
                question
            FROM chats
            WHERE conversation_id = %s
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (conversation_id,))
        
        row = cur.fetchone()
        if not row:
            print("Not enough history to detect emotional shift.")
            cur.close()
            conn.close()
            return False, "Not enough previous messages"

        prev_emotion_1, prev_conf_1, prev_emotion_2, prev_conf_2, prev_text = row

        is_shift, explanation = detect_emotional_shift_llm(
            prev_emotion_1=prev_emotion_1,
            prev_conf_1=prev_conf_1 or 0.0,
            prev_text=prev_text,
            curr_emotion_1=curr_emotion_1,
            curr_conf_1=curr_conf_1 or 0.0,
            curr_emotion_2=curr_emotion_2,
            curr_conf_2=curr_conf_2,
            curr_text=curr_text,
            prev_emotion_2=prev_emotion_2,
            prev_conf_2=prev_conf_2
        )

        if is_shift:
            cur.execute("""
                UPDATE conversations
                SET last_emotion_shift = %s,
                    last_emotion_shift_time = %s
                WHERE conversation_id = %s;
            """, (explanation, datetime.now(), conversation_id))
            conn.commit()

        cur.close()
        conn.close()

        return is_shift, explanation if is_shift else "No shift detected: " + explanation

    except Exception as e:
        return False, str(e)