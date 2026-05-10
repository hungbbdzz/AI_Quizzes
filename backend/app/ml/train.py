from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from transformers import AutoTokenizer

from app.ml.dataset import load_csv_dataset, DifficultyDataset, collate_batch
from app.ml.model import DifficultyClassifier


LABEL_MAP = {0: "easy", 1: "medium", 2: "hard"}


def split_samples(samples, train_ratio: float = 0.9):
    random.shuffle(samples)
    split_idx = int(len(samples) * train_ratio)
    return samples[:split_idx], samples[split_idx:]


def train(args):
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    samples = load_csv_dataset(args.data)
    train_samples, val_samples = split_samples(samples)

    tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")

    train_ds = DifficultyDataset(train_samples)
    val_ds = DifficultyDataset(val_samples)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, args.max_length),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=lambda batch: collate_batch(batch, tokenizer, args.max_length),
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DifficultyClassifier(lstm_hidden=args.lstm_hidden).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    label_counts = Counter(sample.label for sample in train_samples)
    total = sum(label_counts.values())
    weights = [
        total / (label_counts.get(label, 1) * len(LABEL_MAP))
        for label in range(len(LABEL_MAP))
    ]
    class_weights = torch.tensor(weights, dtype=torch.float, device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)

    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0

        for encodings, labels in train_loader:
            encodings = {k: v.to(device) for k, v in encodings.items()}
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(encodings["input_ids"], encodings["attention_mask"])
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(len(train_loader), 1)
        val_acc = evaluate(model, val_loader, device)
        print(f"Epoch {epoch + 1}/{args.epochs} - loss: {avg_loss:.4f} - val_acc: {val_acc:.4f}")

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    model_path = Path(args.output_dir) / "model.pt"
    torch.save(model.state_dict(), model_path)

    label_map_path = Path(args.output_dir) / "label_map.json"
    with open(label_map_path, "w", encoding="utf-8") as handle:
        json.dump(LABEL_MAP, handle, ensure_ascii=False, indent=2)

    print(f"Saved model to {model_path}")


def evaluate(model, loader, device: str) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for encodings, labels in loader:
            encodings = {k: v.to(device) for k, v in encodings.items()}
            labels = labels.to(device)
            logits = model(encodings["input_ids"], encodings["attention_mask"])
            preds = torch.argmax(logits, dim=1)
            correct += int((preds == labels).sum().item())
            total += labels.size(0)
    return correct / total if total > 0 else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PhoBERT + BiLSTM difficulty classifier")
    parser.add_argument("--data", required=True, help="Path to CSV with columns cau_hoi, do_kho")
    parser.add_argument("--output-dir", default="backend/app/ml/artifacts")
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=128)
    parser.add_argument("--lstm-hidden", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)

    train(parser.parse_args())
