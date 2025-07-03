import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import login, hf_hub_download
from app.config import Config

label_map = None

def load_label_map(model_path):
    global label_map
    if label_map is not None:
        return label_map

    login(token=Config.HF_TOKEN)

    try:
        label_file_path = hf_hub_download(
            repo_id=model_path,
            filename="label_names.txt",
            repo_type="model",
            token=Config.HF_TOKEN
        )
        with open(label_file_path, "r") as f:
            lines = f.readlines()
    except Exception:
        lines = []

    id2label = {}
    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split("\t")
        if len(parts) != 2:
            continue
        try:
            index = int(parts[0])
            label = parts[1]
            id2label[index] = label
        except ValueError:
            continue

    label_map = id2label
    return id2label

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
    model_path = "Isha2006/emotion-detector-via-text"

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()

    id2label = load_label_map(model_path)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.sigmoid(logits)[0]

    top_indices = torch.topk(probs, top_k).indices.tolist()
    emotions = [id2label.get(i, f"unknown_{i}") for i in top_indices]
    scores = [round(probs[i].item(), 4) for i in top_indices]

    return emotions, scores