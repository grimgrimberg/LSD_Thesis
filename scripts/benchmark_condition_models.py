# /// script
# dependencies = [
#   "numpy>=2.2.4",
#   "pydantic>=2.11.3",
#   "scikit-learn>=1.6.1",
#   "scipy>=1.15.2",
#   "torch>=2.7.0",
# ]
# ///

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lsd_thesis.condition_models import evaluate_sklearn_condition_models, load_window_dataset  # noqa: E402
from lsd_thesis.core import MODULE_NAMES  # noqa: E402


class TemporalCNN(nn.Module):
    def __init__(self, input_channels: int, hidden_channels: int = 24) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv1d(input_channels, hidden_channels, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(hidden_channels, hidden_channels * 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(hidden_channels * 2, 32),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(32, 2),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.network(inputs.transpose(1, 2))


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _classification_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:
    metrics = {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
    }
    if len(np.unique(y_true)) < 2:
        metrics["roc_auc"] = float("nan")
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true, probabilities))
    return metrics


def _aggregate_folds(folds: list[dict[str, float | int | str]]) -> dict[str, float]:
    aggregate: dict[str, float] = {}
    for metric_name in ("accuracy", "balanced_accuracy", "roc_auc"):
        values = np.asarray([float(fold[metric_name]) for fold in folds], dtype=float)
        aggregate[f"{metric_name}_mean"] = float(np.nanmean(values))
        aggregate[f"{metric_name}_std"] = float(np.nanstd(values))
    return aggregate


def evaluate_temporal_cnn(
    dataset: dict[str, np.ndarray],
    *,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
) -> dict[str, Any]:
    windows = np.asarray(dataset["windows"], dtype=np.float32)
    labels = np.asarray(dataset["condition"], dtype=np.int64)
    groups = np.asarray(dataset["subject"])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logo = LeaveOneGroupOut()

    folds: list[dict[str, float | int | str]] = []
    predictions: list[dict[str, float | int | str]] = []
    training_history: list[dict[str, Any]] = []

    for fold_index, (train_idx, test_idx) in enumerate(logo.split(windows, labels, groups), start=1):
        _set_seed(seed + fold_index)

        train_windows = torch.tensor(windows[train_idx], dtype=torch.float32)
        test_windows = torch.tensor(windows[test_idx], dtype=torch.float32)
        train_labels = torch.tensor(labels[train_idx], dtype=torch.long)

        channel_mean = train_windows.mean(dim=(0, 1), keepdim=True)
        channel_std = train_windows.std(dim=(0, 1), keepdim=True).clamp_min(1e-6)
        train_windows = (train_windows - channel_mean) / channel_std
        test_windows = (test_windows - channel_mean) / channel_std

        loader = DataLoader(
            TensorDataset(train_windows, train_labels),
            batch_size=batch_size,
            shuffle=True,
        )

        model = TemporalCNN(input_channels=windows.shape[-1]).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
        loss_fn = nn.CrossEntropyLoss()

        fold_history: list[dict[str, float | int]] = []
        model.train()
        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            batches = 0
            for batch_windows, batch_labels in loader:
                batch_windows = batch_windows.to(device)
                batch_labels = batch_labels.to(device)
                optimizer.zero_grad()
                logits = model(batch_windows)
                loss = loss_fn(logits, batch_labels)
                loss.backward()
                optimizer.step()
                epoch_loss += float(loss.item())
                batches += 1
            fold_history.append(
                {
                    "fold": fold_index,
                    "epoch": epoch,
                    "loss": epoch_loss / max(batches, 1),
                }
            )
        training_history.extend(fold_history)

        model.eval()
        with torch.no_grad():
            logits = model(test_windows.to(device))
            probabilities = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
        fold_predictions = (probabilities >= 0.5).astype(np.int8)
        fold_metrics = _classification_metrics(labels[test_idx], probabilities, fold_predictions)
        left_out_subject = str(np.unique(groups[test_idx])[0])
        folds.append({"fold": fold_index, "left_out_subject": left_out_subject, **fold_metrics})

        for sample_idx, probability, prediction in zip(test_idx, probabilities, fold_predictions, strict=False):
            predictions.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "y_true": int(labels[sample_idx]),
                    "y_pred": int(prediction),
                    "probability_lsd": float(probability),
                }
            )

    return {
        "device": device.type,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "folds": folds,
        "aggregate": _aggregate_folds(folds),
        "predictions": predictions,
        "training_history": training_history,
    }


def _to_plain_python(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_plain_python(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_plain_python(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def _write_predictions_csv(path: Path, model_results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("model", "fold", "subject", "y_true", "y_pred", "probability_lsd")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for model_name, payload in model_results.items():
            for row in payload["predictions"]:
                writer.writerow({"model": model_name, **row})


def _write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    ranking = sorted(
        summary["models"].items(),
        key=lambda item: item[1]["aggregate"]["balanced_accuracy_mean"],
        reverse=True,
    )
    lines = [
        "# LSD Condition Benchmark",
        "",
        f"- Dataset: `{summary['dataset_path']}`",
        f"- Samples: {summary['dataset']['sample_count']}",
        f"- Subjects: {summary['dataset']['subject_count']}",
        f"- Window shape: `{summary['dataset']['window_length']} x {summary['dataset']['module_count']}`",
        f"- CV: `{summary['cv_strategy']}`",
        "",
        "## Model Ranking",
        "",
        "| Model | Accuracy | Balanced Accuracy | ROC AUC |",
        "| --- | --- | --- | --- |",
    ]
    for model_name, payload in ranking:
        aggregate = payload["aggregate"]
        lines.append(
            f"| {model_name} | {aggregate['accuracy_mean']:.3f} ± {aggregate['accuracy_std']:.3f} | "
            f"{aggregate['balanced_accuracy_mean']:.3f} ± {aggregate['balanced_accuracy_std']:.3f} | "
            f"{aggregate['roc_auc_mean']:.3f} ± {aggregate['roc_auc_std']:.3f} |"
        )

    logistic = summary["models"].get("logistic_regression")
    if logistic and logistic.get("top_features"):
        lines.extend(["", "## Top Linear Features", ""])
        for item in logistic["top_features"][:10]:
            lines.append(
                f"- `{item['feature']}`: abs={item['importance']:.4f}, signed={item['signed_weight']:.4f}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This benchmark predicts `LSD vs placebo` from windowed 8-module trajectories under subject-held-out CV.",
            "- Engineered-feature models test whether the current graph-informed summary features and FC geometry already separate conditions.",
            "- The temporal CNN tests whether a small learned temporal model improves on those hand-crafted summaries without leaking subject identity.",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LSD vs placebo condition models on exported Stage 2 windows.")
    parser.add_argument("--dataset", default=str(REPO_ROOT / "results" / "training" / "ds003059_windows.npz"))
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "training" / "condition_benchmark"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_window_dataset(dataset_path)
    sklearn_results = evaluate_sklearn_condition_models(dataset, module_names=MODULE_NAMES, random_state=args.seed)
    cnn_results = evaluate_temporal_cnn(
        dataset,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )

    summary = {
        "task": "lsd_vs_placebo_condition_classification",
        "dataset_path": str(dataset_path),
        "cv_strategy": "LeaveOneGroupOut(subject)",
        "dataset": sklearn_results["dataset"],
        "feature_names": sklearn_results["feature_names"],
        "models": {
            **sklearn_results["models"],
            "temporal_cnn": cnn_results,
        },
    }

    (output_dir / "comparison_summary.json").write_text(
        json.dumps(_to_plain_python(summary), indent=2),
        encoding="utf-8",
    )
    _write_predictions_csv(output_dir / "fold_predictions.csv", summary["models"])
    _write_markdown_report(output_dir / "benchmark_report.md", summary)

    best_model_name, best_model = max(
        summary["models"].items(),
        key=lambda item: item[1]["aggregate"]["balanced_accuracy_mean"],
    )
    print(
        json.dumps(
            {
                "best_model": best_model_name,
                "balanced_accuracy_mean": best_model["aggregate"]["balanced_accuracy_mean"],
                "roc_auc_mean": best_model["aggregate"]["roc_auc_mean"],
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
