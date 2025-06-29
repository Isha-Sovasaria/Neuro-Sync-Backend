import requests
from flask import current_app

def get_embedding_vector(user_input):
    api_key = current_app.config["COHERE_API_KEY"]

    url = "https://api.cohere.ai/v1/embed"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "embed-english-v3.0",
        "texts": [user_input],
        "input_type": "classification"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    embedding = response.json()["embeddings"][0]
    return embedding