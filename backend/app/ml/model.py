from __future__ import annotations

import torch
from torch import nn
from transformers import AutoModel


class DifficultyClassifier(nn.Module):
    """PhoBERT encoder + BiLSTM classifier for difficulty prediction."""

    def __init__(self, base_model: str = "vinai/phobert-base", lstm_hidden: int = 256, num_labels: int = 3):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        self.lstm = nn.LSTM(
            input_size=self.encoder.config.hidden_size,
            hidden_size=lstm_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
        )
        self.dropout = nn.Dropout(0.2)
        self.classifier = nn.Linear(lstm_hidden * 2, num_labels)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state

        lengths = attention_mask.sum(dim=1).cpu()
        packed = nn.utils.rnn.pack_padded_sequence(
            sequence_output,
            lengths,
            batch_first=True,
            enforce_sorted=False,
        )
        _, (hidden, _) = self.lstm(packed)
        forward_hidden = hidden[-2]
        backward_hidden = hidden[-1]
        pooled = torch.cat([forward_hidden, backward_hidden], dim=1)
        pooled = self.dropout(pooled)
        return self.classifier(pooled)
