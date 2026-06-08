# /// script
# dependencies = [
#   "numpy>=2.2.4",
#   "torch>=2.7.0",
# ]
# ///

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


class SequenceAutoencoder(nn.Module):
    def __init__(self, input_dim: int = 8, hidden_dim: int = 32, latent_dim: int = 16) -> None:
        super().__init__()
        self.encoder = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.to_latent = nn.Linear(hidden_dim, latent_dim)
        self.from_latent = nn.Linear(latent_dim, hidden_dim)
        self.decoder = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, input_dim)
        self.condition_head = nn.Linear(latent_dim, 2)

    def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        _, hidden = self.encoder(inputs)
        latent = self.to_latent(hidden[-1])
        repeated = self.from_latent(latent).unsqueeze(0)
        decoder_input = torch.zeros_like(inputs)
        decoded, _ = self.decoder(decoder_input, repeated)
        reconstruction = self.output(decoded)
        condition_logits = self.condition_head(latent)
        return reconstruction, condition_logits


def main() -> None:
    dataset_path = Path(os.environ.get("DATASET_PATH", "results/training/ds003059_windows.npz"))
    output_dir = Path(os.environ.get("OUTPUT_DIR", "results/cloud_training"))
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = np.load(dataset_path)
    inputs = torch.tensor(payload["windows"], dtype=torch.float32)
    condition = torch.tensor(payload["condition"], dtype=torch.long)

    dataset = TensorDataset(inputs, condition)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    model = SequenceAutoencoder(input_dim=inputs.shape[-1])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    reconstruction_loss = nn.MSELoss()
    classification_loss = nn.CrossEntropyLoss()

    history: list[dict[str, float | int]] = []
    for epoch in range(1, 11):
        total_recon = 0.0
        total_cls = 0.0
        batches = 0
        for batch_inputs, batch_condition in loader:
            optimizer.zero_grad()
            reconstructed, logits = model(batch_inputs)
            loss_recon = reconstruction_loss(reconstructed, batch_inputs)
            loss_cls = classification_loss(logits, batch_condition)
            loss = loss_recon + 0.2 * loss_cls
            loss.backward()
            optimizer.step()
            total_recon += float(loss_recon.item())
            total_cls += float(loss_cls.item())
            batches += 1

        history.append(
            {
                "epoch": epoch,
                "reconstruction_loss": total_recon / max(batches, 1),
                "condition_loss": total_cls / max(batches, 1),
            }
        )

    torch.save(model.state_dict(), output_dir / "sequence_autoencoder.pt")
    (output_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    print(json.dumps(history[-1], indent=2))


if __name__ == "__main__":
    main()
