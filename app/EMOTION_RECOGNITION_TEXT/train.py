from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset, concatenate_datasets
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score
import torch
import numpy as np
import os
import pandas as pd

csv1 = load_dataset("csv", data_files="file1.csv")["train"]
csv2 = load_dataset("csv", data_files="file2.csv")["train"]
csv3 = load_dataset("csv", data_files="file3.csv")["train"]
custom = load_dataset("json", data_files="custom_emotions.jsonl")["train"]

dataset = concatenate_datasets([csv1, csv2, csv3, custom])

dataset = dataset.filter(lambda x: isinstance(x["labels"], list) and x["labels"])

all_labels = set(label for labels in dataset["labels"] for label in labels)
mlb = MultiLabelBinarizer(classes=sorted(list(all_labels)))
mlb.fit(dataset["labels"])

model_name = "distilroberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def preprocess(example):
    tokenized = tokenizer(example["text"], padding="max_length", truncation=True, max_length=128)
    tokenized["labels"] = mlb.transform([example["labels"]])[0].astype(float).tolist()
    return tokenized

dataset_split = dataset.train_test_split(test_size=0.1, seed=42)
tokenized_dataset = dataset_split.map(preprocess)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    num_labels=len(mlb.classes_),
    problem_type="multi_label_classification"
)

training_args = TrainingArguments(
    output_dir="./finetuned-emotion-model",
    per_device_train_batch_size=8,
    num_train_epochs=5,
    learning_rate=2e-5,
    weight_decay=0.01,
    save_strategy="epoch",
    logging_dir="./logs"
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    probs = torch.sigmoid(torch.tensor(logits)).numpy()
    predictions = (probs >= 0.3).astype(int)
    return {
        "f1": f1_score(labels, predictions, average="micro"),
        "precision": precision_score(labels, predictions, average="micro"),
        "recall": recall_score(labels, predictions, average="micro"),
        "accuracy": accuracy_score(labels, predictions)
    }

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    compute_metrics=compute_metrics
)

trainer.train()

output_dir = "./finetuned-emotion-model"
model.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)

with open(os.path.join(output_dir, "label_names.txt"), "w") as f:
    for i, label in enumerate(mlb.classes_):
        f.write(f"{i}\t{label}\n")

print("Model training complete. Saved to ./finetuned-emotion-model")
