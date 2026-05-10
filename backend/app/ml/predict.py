from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Dict

import torch
from transformers import AutoTokenizer

from app.ml.model import DifficultyClassifier


DEFAULT_LABEL_MAP = {"0": "easy", "1": "medium", "2": "hard"}


@dataclass
class Prediction:
    label: str
    score: float


class DifficultyPredictor:
    def __init__(self, model_path: str, label_map_path: str | None = None, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
        self.model = DifficultyClassifier()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        if label_map_path:
            with open(label_map_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            self.label_map = {str(k): v for k, v in raw.items()}
        else:
            self.label_map = DEFAULT_LABEL_MAP

    def predict(self, texts: List[str]) -> List[Prediction]:
        if not texts:
            return []

        encodings = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        encodings = {k: v.to(self.device) for k, v in encodings.items()}

        with torch.no_grad():
            logits = self.model(encodings["input_ids"], encodings["attention_mask"])
            probs = torch.softmax(logits, dim=1)

        predictions: List[Prediction] = []
        for row in probs.cpu().tolist():
            best_idx = int(max(range(len(row)), key=row.__getitem__))
            label = self.label_map.get(str(best_idx), "medium")
            score = float(row[best_idx])
            predictions.append(Prediction(label=label, score=score))

        return predictions
