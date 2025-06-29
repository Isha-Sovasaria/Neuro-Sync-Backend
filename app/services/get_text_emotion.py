from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from huggingface_hub import login
from app.config import Config

login(token=Config.HF_TOKEN)

# === Load model and tokenizer from Hugging Face Hub ===
model_path = "Isha2006/emotion-detector-via-text"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

# === Load label names from text file on Hugging Face Hub ===
import requests

label_url = f"https://huggingface.co/{model_path}/resolve/main/label_names.txt"
response = requests.get(label_url)
lines = response.text.strip().split("\n")

id2label = {}
for line in lines:
    if not line.strip():
        continue  # skip empty lines
    parts = line.strip().split("\t")
    if len(parts) != 2:
        print(f"⚠️ Skipping malformed line: {line!r}")
        continue
    index, label = parts
    id2label[int(index)] = label

def get_text_emotion(text, top_k=2):
    """
    Get top-k emotions from your fine-tuned multi-label emotion model.

    Args:
        text (str): Input string
        top_k (int): Number of top emotions to return

    Returns:
        emotions (list of str): Top-k emotion labels
        scores (list of float): Corresponding confidence scores
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.sigmoid(logits)[0]

    top_indices = torch.topk(probs, top_k).indices.tolist()
    emotions = [id2label[i] for i in top_indices]
    scores = [round(probs[i].item(), 4) for i in top_indices]

    return emotions, scores
