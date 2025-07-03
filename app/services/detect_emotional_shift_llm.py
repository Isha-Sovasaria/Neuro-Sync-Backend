import requests
from flask import current_app

def detect_emotional_shift_llm(
    prev_emotion_1, prev_conf_1,
    prev_text,
    curr_emotion_1, curr_conf_1,
    curr_emotion_2=None, curr_conf_2=None,
    curr_text="",
    prev_emotion_2=None, prev_conf_2=None
):
    if not curr_emotion_1 or not curr_text:
        return False, "Insufficient data"

    prev_emotion_block = f"""
Previous emotion #1: "{prev_emotion_1}" (confidence: {prev_conf_1:.2f})
"""
    if prev_emotion_2 and prev_conf_2:
        prev_emotion_block += f"""Previous emotion #2: "{prev_emotion_2}" (confidence: {prev_conf_2:.2f})"""

    curr_emotion_block = f"""
Current emotion #1: "{curr_emotion_1}" (confidence: {curr_conf_1:.2f})
"""
    if curr_emotion_2 and curr_conf_2:
        curr_emotion_block += f"""Current emotion #2: "{curr_emotion_2}" (confidence: {curr_conf_2:.2f})"""

    prompt = f"""
You are an emotion-aware therapist AI analyzing whether a person is undergoing a meaningful **emotional shift**.

## CASE: Immediate Emotional Change
{prev_emotion_block.strip()}
Previous message: "{prev_text}"

{curr_emotion_block.strip()}
Current message: "{curr_text}"

### TASK:
1. Determine if there's a meaningful emotional shift between the previous and current message:
   - Change in **emotional category** (e.g., sadness → hope, or negative → neutral)
   - Change in **intensity** (e.g., slight anxiety → panic)

2. First, answer clearly on a new line:
shift: yes or shift: no

3. Then respond like a therapist analyzing this, in 1–2 sentences. Explain if there's a shift or not, and what kind (category change, intensity spike, etc.). Avoid repetition. Do **not** say "as an AI" or give user advice.

⚠️ Do not speak to the user. Just reflect analytically.
""".strip()

    api_key = current_app.config["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        full_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip().lower()

        is_shift = full_text.startswith("shift: yes")
        explanation = full_text.split("\n", 1)[1].strip() if "\n" in full_text else ""
        return is_shift, explanation

    except Exception as e:
        print("Gemini error in shift detection:", e)
        return False, str(e)
