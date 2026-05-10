"""Difficulty prediction service using a local PhoBERT + BiLSTM model."""

from __future__ import annotations

import asyncio
from typing import List, Dict

from app.config import settings
from app.ml.predict import DifficultyPredictor


_DEFAULT_LABEL = "medium"
_predictor: DifficultyPredictor | None = None


def _get_predictor() -> DifficultyPredictor:
    global _predictor
    if _predictor is None:
        _predictor = DifficultyPredictor(
            model_path=settings.DIFFICULTY_MODEL_PATH,
            label_map_path=settings.DIFFICULTY_LABEL_MAP_PATH,
        )
    return _predictor


def _fallback(texts: List[str]) -> List[Dict[str, float | str]]:
    return [
        {
            "label": _DEFAULT_LABEL,
            "score": 0.0,
            "version": settings.DIFFICULTY_VERSION,
        }
        for _ in texts
    ]


async def predict_difficulty(texts: List[str]) -> List[Dict[str, float | str]]:
    if not texts:
        return []

    try:
        predictor = _get_predictor()
        predictions = await asyncio.to_thread(predictor.predict, texts)
        return [
            {
                "label": pred.label,
                "score": pred.score,
                "version": settings.DIFFICULTY_VERSION,
            }
            for pred in predictions
        ]
    except Exception as exc:
        print(f"[DIFFICULTY SERVICE] Fallback to default label: {exc}")
        return _fallback(texts)
