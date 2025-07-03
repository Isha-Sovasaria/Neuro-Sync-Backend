from huggingface_hub import HfApi
import os

model_id = "Isha2006/emotion-detector-via-text"
local_path = "/Users/isha/backend/app/EMOTION_RECOGNITION_TEXT/finetuned-emotion-model"
api = HfApi()

for root, dirs, files in os.walk(local_path):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for file in files:
        if file.startswith('.'):
            continue
        full_path = os.path.join(root, file)
        repo_path = os.path.relpath(full_path, local_path)

        print(f"Uploading: {repo_path}")
        api.upload_file(
            path_or_fileobj=full_path,
            path_in_repo=repo_path,
            repo_id=model_id,
            repo_type="model"
        )

print("All model files uploaded successfully.")
