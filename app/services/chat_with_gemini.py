import requests
from flask import current_app, request
from datetime import datetime
from app.db import get_connection
from app.services.get_embedding_vector import get_embedding_vector
from app.services.insert_chat import insert_chat
from app.services.fetch_relevant_chats import fetch_relevant_chats
from app.services.update_emotional_shift import update_emotion_shift_if_detected
from app.services.get_text_emotion import get_text_emotion
from app.services.detect_crisis_level import detect_crisis_level
from app.services.update_daily_emotions import update_daily_emotion_summary
from app.services.check_crisis_flag import check_crisis_flags
import ipinfo

def chat_with_gemini(user_input, email, conversation_id=None, emotion=None, confidence_scores=None):
    api_key = current_app.config["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    # === Step 1: Embedding and location setup
    embedding = get_embedding_vector(user_input)
    access_token = "801d518a4fcf32"  # Replace with your actual token
    ip_handler = ipinfo.getHandler(access_token)
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address.startswith("127.") or ip_address == "::1":
        ip_address = "8.8.8.8"  # fallback for localhost
    details = ip_handler.getDetails(ip_address)
    city = details.city
    country = details.country_name

    # === Step 2: Emotion detection if not passed
    if emotion is None or confidence_scores is None:
        emotion, confidence_scores = get_text_emotion(user_input)

    # === Step 3: Get user_id
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_id = cur.fetchone()[0]

    # === Step 4: Crisis detection
    crisis_data = detect_crisis_level(user_input)
    crisis_label = crisis_data["label"]
    crisis_confidence = crisis_data["confidence"]
    is_crisis = crisis_data["crisis"]
    first_crisis_today, spaced_out_crises, has_consecutive_days = check_crisis_flags(user_id)

    if is_crisis:
        pattern_note = ""
        if spaced_out_crises:
            pattern_note = "This is not the first time today — the user has expressed distress multiple times in a short span.Please acknowledge that fact that you have noticed this. "
        elif has_consecutive_days:
            pattern_note = "This pattern has been recurring over multiple consecutive days.Please mention this to the user and acknowledge that you have noticed this."

        helpline_lookup = {
            "United States": "📞 **Suicide & Crisis Lifeline**: Call or text 988 (24/7, confidential)",
            "India": "📞 **iCall**: +91 9152987821 (available 24/7)",
            "United Kingdom": "📞 **Samaritans UK**: Call 116 123 (24/7, free)",
            "Singapore": "📞 **Samaritans of Singapore (SOS)**: Call 1767",
            "Canada": "📞 **Talk Suicide Canada**: 1-833-456-4566 (24/7)",
            "Australia": "📞 **Lifeline Australia**: 13 11 14",
            "Germany": "📞 **Telefonseelsorge**: 0800 1110111 or 0800 1110222 (24/7)",
            "South Africa": "📞 **Lifeline South Africa**: 0861 322 322",
            "New Zealand": "📞 **Lifeline Aotearoa**: 0800 543 354",
            "Philippines": "📞 **Hopeline Philippines**: (02) 8804-4673 or 0917-558-4673"
        }

        helpline = helpline_lookup.get(country, "Please reach out to your local emergency support.")

        crisis_remark = (
            f"\n\n🚨 **Potential Crisis Detected**: _{crisis_label}_ (confidence: {crisis_confidence}). "
            f"Please respond with empathy and let the user know they are not alone.Keep your response concise. "
            f"Share this helpline with them for {country}: {helpline} "
            f"{pattern_note}"
        )
    else:
        crisis_remark = ""

    # === Step 5: Fetch chat memory
    relevant_chats, same_convo_chats = fetch_relevant_chats(email, embedding, conversation_id)
    same_convo_context = "\n\n".join(f"User: {q}\nAI: {r}" for q, r in same_convo_chats)
    relevant_context = "\n\n".join(f"User: {q}\nAI: {r}" for q, r in relevant_chats)

    # === Step 6: Emotional shift detection
    shift_detected, shift_summary = update_emotion_shift_if_detected(
        conversation_id=conversation_id,
        curr_emotion_1=emotion[0],
        curr_conf_1=confidence_scores[0],
        curr_emotion_2=emotion[1] if len(emotion) > 1 else None,
        curr_conf_2=confidence_scores[1] if len(confidence_scores) > 1 else None,
        curr_text=user_input
    )

    shift_remark = (
        f"\n\n🌀 **Emotional Shift Noted**:\n{shift_summary.strip()}"
        if shift_detected else ""
    )

    # === Step 7: Build prompt
    prompt = f"""
You are a compassionate mental health guide who helps users process their emotions and talk through their experiences with care and understanding.

🎯 Tone and Intentions:
- Use short, natural-sounding sentences — like in real conversations.
- Maintain continuity in the current conversation. Avoid repeating questions or advice unnecessarily.
- Ask gentle follow-up questions to help users explore their feelings.
- Offer helpful tips or coping techniques, but don’t overwhelm with too many questions at once.Do not continuously offer grounding/breathing tips in every message.
- Avoid dramatic expressions (e.g., “oh honey”, “oh dear”).
- Never break character or mention you're an AI or chatbot.
- After suggestions, ask open-ended follow-ups like:
  “Do you think that might help?” or  
  “How did that feel when you tried it?”

🧠 Memory Awareness:
- Use current conversation history to stay consistent and avoid repeating prior insights.

Current conversation history:
{same_convo_context or "No prior messages in this thread."}

Content Guidelines:
- If the user asks about work, academics, or technical topics, gently steer the conversation back to their emotional well-being or personal experiences.
  For example: "That sounds like a stressful situation — how has it been affecting you emotionally?"

💭 Past emotionally relevant experiences from other chats (Please make reference to any prior experience of the user and use relevant tips/techniques that helped them previously):
{relevant_context or "No related chat history available."}

Current emotional state detected:
Primary emotion(s): {emotion} (confidence: {confidence_scores})
{shift_remark}
Please keep the emotional state of the user in mind when asking questions or offering support. Also, acknowledge gently when the user makes a positive emotional shift and encourage them.

{crisis_remark}

✉️ The user now says:
"{user_input}"

Craft your response mindfully, maintaining continuity and care.
""".strip()

    # === Step 8: Call Gemini
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    # === Step 9: Save chat
    new_convo_id = insert_chat(
        email=email,
        question=user_input,
        response=reply,
        emotion=emotion,
        embedding=embedding,
        emotion_confidence=confidence_scores,
        conversation_id=conversation_id,
        crisis_level=crisis_label
    )

    # === DEBUG: Print location and prompt
    print(f"🌍 Location detected: {city}, {country}")
    print("📝 Final Prompt Sent to Gemini:\n", prompt)

    # === Step 10: Update daily emotion summary
    update_daily_emotion_summary(
        user_id=user_id,
        summary_date=datetime.now().date()
    )

    redirect = spaced_out_crises or has_consecutive_days

    cur.close()
    conn.close()

    return reply, str(new_convo_id), emotion, crisis_data, redirect if is_crisis else None
