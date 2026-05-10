from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import List, Tuple

import torch
from torch.utils.data import Dataset


@dataclass
class Sample:
    text: str
    label: int


def load_csv_dataset(path: str) -> List[Sample]:
    samples: List[Sample] = []
    with open(path, "r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            text = (row.get("cau_hoi") or "").strip()
            label_raw = row.get("do_kho")
            if not text or label_raw is None:
                continue
            try:
                label = int(label_raw)
            except ValueError:
                continue
            samples.append(Sample(text=text, label=label))
    return samples


class DifficultyDataset(Dataset):
    def __init__(self, samples: List[Sample]):
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[str, int]:
        sample = self.samples[idx]
        return sample.text, sample.label


def collate_batch(batch, tokenizer, max_length: int = 128):
    texts, labels = zip(*batch)
    encodings = tokenizer(
        list(texts),
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    return encodings, torch.tensor(labels, dtype=torch.long)
