from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import torch
import whisper
import numpy as np
from pydub import AudioSegment
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Processor
from app.services.chat_with_gemini import chat_with_gemini
from .chatbot import chatbot_bp

UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load models once
processor = Wav2Vec2Processor.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
model = Wav2Vec2ForSequenceClassification.from_pretrained("audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim")
whisper_model = whisper.load_model("base")

label_map = {
    0: "neutral", 1: "calm", 2: "happy", 3: "sad", 4: "angry",
    5: "fearful", 6: "disgust", 7: "surprised"
}

@chatbot_bp.route("/audio-chat", methods=["POST"])
def audio_chat():
    raw_path = None
    wav_path = None

    try:
        # === Validate form data ===
        if "audio" not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400

        email = request.form.get("email")
        raw_conversation_id = request.form.get("conversation_id")  # from frontend as string or null

        # === Match `/ask` logic ===
        conversation_id = raw_conversation_id if raw_conversation_id and raw_conversation_id.lower() != "null" else None

        if not email:
            return jsonify({"error": "Email is required"}), 422

        file = request.files["audio"]
        if file.filename == "":
            return jsonify({"error": "Empty audio filename"}), 400

        # === Save and convert to .wav ===
        filename = secure_filename(file.filename)
        raw_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(raw_path)

        wav_path = raw_path.rsplit(".", 1)[0] + ".wav"
        audio = AudioSegment.from_file(raw_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_path, format="wav")

        # === Convert audio to waveform for model ===
        samples = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
        waveform = torch.tensor(samples)

        # === Emotion detection ===
        inputs = processor(waveform, sampling_rate=16000, return_tensors="pt", padding=True)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_id = int(logits.argmax())
        predicted_emotion = label_map[predicted_id]
        confidence = float(torch.nn.functional.softmax(logits, dim=-1).max())

        # === Transcription ===
        transcription = whisper_model.transcribe(wav_path)["text"].strip()

        # === Chatbot call ===
        reply, conv_id, emotions, crisis_data, redirect = chat_with_gemini(
            user_input=transcription,
            email=email,
            conversation_id=conversation_id,  # passed as string or None — exactly like `/ask`
            emotion=[predicted_emotion],
            confidence_scores=[round(confidence, 3)]
        )

        return jsonify({
            "reply": reply,
            "conversation_id": conv_id,
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
