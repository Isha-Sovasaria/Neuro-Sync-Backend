from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

NEGATION_PHRASES = [
    "i am safe", 
    "no thoughts of harming", 
    "i’m okay", 
    "i am okay", 
    "i’m fine", 
    "i have support"
]

SAFE_EMOTIONS = set([
    "calm", "gratitude", "hope", "relief", "contentment",
    "happiness", "satisfaction", "joy", "love", "pride"
])

tokenizer = AutoTokenizer.from_pretrained("sentinet/suicidality")
model = AutoModelForSequenceClassification.from_pretrained("sentinet/suicidality")

def detect_crisis_level(text, top_emotion=None):


    if any(phrase in text.lower() for phrase in NEGATION_PHRASES):
        return {"crisis": False, "label": "no risk", "confidence": 1.0}

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)

    probs = F.softmax(outputs.logits, dim=1).squeeze()
    confidence_0 = probs[0].item()
    confidence_1 = probs[1].item()

    margin = confidence_1 - confidence_0

    if confidence_1 > 0.85 and margin > 0.2:
        label = "suicidal ideation"
        confidence = round(confidence_1, 3)
    else:
        label = "no risk"
        confidence = round(confidence_0, 3)

    # Override if emotion is safe
    if label == "suicidal ideation" and top_emotion and top_emotion.lower() in SAFE_EMOTIONS:
        label = "no risk"
        confidence = 0.7

    return {
        "crisis": label == "suicidal ideation",
        "label": label,
        "confidence": confidence
    }
