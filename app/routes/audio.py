from flask import request, jsonify, Blueprint
from werkzeug.utils import secure_filename
import os
import torch
import numpy as np
from pydub import AudioSegment
from vosk import Model as VoskModel, KaldiRecognizer
import wave
import json
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
from app.services.chat_with_gemini import chat_with_gemini
from app.services.get_or_create_user import get_or_create_user, mark_user_login
from .chatbot import chatbot_bp  # only if chatbot_bp is defined in chatbot.py

UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# === Load models once
emotion_model = Wav2Vec2ForSequenceClassification.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
emotion_processor = Wav2Vec2Processor.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
vosk_model = VoskModel("app/models/vosk-model")

label_map = {
    0: "neutral", 1: "calm", 2: "happy", 3: "sad", 4: "angry",
    5: "fearful", 6: "disgust", 7: "surprised"
}

def transcribe_with_vosk(wav_path):
    wf = wave.open(wav_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        raise ValueError("Audio must be WAV format mono PCM 16kHz.")
    
    recognizer = KaldiRecognizer(vosk_model, wf.getframerate())
    results = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if recognizer.AcceptWaveform(data):
            res = json.loads(recognizer.Result())
            results.append(res.get("text", ""))
    
    final_res = json.loads(recognizer.FinalResult())
    results.append(final_res.get("text", ""))
    return " ".join(results).strip()


@chatbot_bp.route("/audio-chat", methods=["POST"])
def audio_chat():
    raw_path = None
    wav_path = None

    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400

        email = request.form.get("email")
        raw_conversation_id = request.form.get("conversation_id")
        conversation_id = raw_conversation_id if raw_conversation_id and raw_conversation_id.lower() != "null" else None

        # DEBUG: Check conversation_id input
        print(f"Input conversation_id: {conversation_id}, type: {type(conversation_id)}")

        if not email:
            return jsonify({"error": "Email is required"}), 422

        file = request.files["audio"]
        if file.filename == "":
            return jsonify({"error": "Empty audio filename"}), 400

        # === Save and convert to WAV (mono, 16kHz, PCM signed 16-bit)
        filename = secure_filename(file.filename)
        raw_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(raw_path)

        wav_path = raw_path.rsplit(".", 1)[0] + ".wav"
        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav", parameters=["-acodec", "pcm_s16le"])

        # === Emotion detection
        samples = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
        waveform = torch.tensor(samples)
        inputs = emotion_processor(waveform, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = emotion_model(**inputs).logits
        predicted_id = int(logits.argmax())
        predicted_emotion = label_map[predicted_id]
        confidence = float(torch.nn.functional.softmax(logits, dim=-1).max())

        # === Transcription with debugging
        try:
            transcription = transcribe_with_vosk(wav_path)
            print(f"Vosk transcription successful: {transcription}")
        except Exception as e:
            print(f"Vosk transcription failed: {e}")
            raise

        # === Get or create user and mark login
        user_id = get_or_create_user(email)
        mark_user_login(user_id)

        # === Gemini chatbot call with debugging
        reply, updated_conversation_id, emotions, crisis_data, redirect = chat_with_gemini(
            user_input=transcription,
            email=email,
            conversation_id=conversation_id,
            emotion=[predicted_emotion],
            confidence_scores=[round(confidence, 3)]
        )

        # DEBUG: Check conversation_id output
        print(f"Output conversation_id: {updated_conversation_id}, type: {type(updated_conversation_id)}")

        return jsonify({
            "reply": reply,
            "conversation_id": str(updated_conversation_id),  # ✅ fix UUID issue here
            "transcription": transcription,
            "emotion": emotions,
            "crisis": crisis_data,
            "redirect": redirect
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Failed to process audio.",
            "details": str(e)
        }), 500

    finally:
        for path in [raw_path, wav_path]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except:
                pass