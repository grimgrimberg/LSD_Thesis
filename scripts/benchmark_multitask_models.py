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
from sklearn.metrics import accuracy_score, balanced_accuracy_score, mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
from sklearn.model_selection import LeaveOneGroupOut
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from lsd_thesis.condition_models import (  # noqa: E402
    build_window_eigenvalue_targets,
    evaluate_sklearn_multitask_models,
    load_window_dataset,
)


class MultitaskTemporalCNN(nn.Module):
    def __init__(self, input_channels: int, hidden_channels: int = 24, target_dim: int = 8) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, hidden_channels, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv1d(hidden_channels, hidden_channels * 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
        )
        self.shared = nn.Sequential(
            nn.Linear(hidden_channels * 2, 48),
            nn.ReLU(),
            nn.Dropout(p=0.2),
        )
        self.classifier_head = nn.Linear(48, 2)
        self.regression_head = nn.Linear(48, target_dim)

    def forward(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        latent = self.encoder(inputs.transpose(1, 2))
        shared = self.shared(latent)
        return self.classifier_head(shared), self.regression_head(shared)


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


def _regression_metrics(
    y_true: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, float]:
    if y_true.shape[0] < 2:
        eigen_r2 = float("nan")
    else:
        eigen_r2 = float(r2_score(y_true, predictions, multioutput="uniform_average"))
    return {
        "eigen_mae": float(mean_absolute_error(y_true, predictions)),
        "eigen_rmse": float(np.sqrt(mean_squared_error(y_true, predictions))),
        "eigen_r2": eigen_r2,
    }


def _aggregate_folds(folds: list[dict[str, float | int | str]]) -> dict[str, float]:
    metric_names = tuple(
        key
        for key in folds[0]
        if key not in {"fold", "left_out_subject"}
    )
    aggregate: dict[str, float] = {}
    for metric_name in metric_names:
        values = np.asarray([float(fold[metric_name]) for fold in folds], dtype=float)
        aggregate[f"{metric_name}_mean"] = float(np.nanmean(values))
        aggregate[f"{metric_name}_std"] = float(np.nanstd(values))
    return aggregate


def evaluate_multitask_temporal_cnn(
    dataset: dict[str, np.ndarray],
    *,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    classification_weight: float,
    regression_weight: float,
) -> dict[str, Any]:
    windows = np.asarray(dataset["windows"], dtype=np.float32)
    labels = np.asarray(dataset["condition"], dtype=np.int64)
    groups = np.asarray(dataset["subject"])
    eigen_targets, target_names = build_window_eigenvalue_targets(windows)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logo = LeaveOneGroupOut()
    folds: list[dict[str, float | int | str]] = []
    classification_predictions: list[dict[str, float | int | str]] = []
    eigen_predictions: list[dict[str, Any]] = []
    training_history: list[dict[str, Any]] = []

    for fold_index, (train_idx, test_idx) in enumerate(logo.split(windows, labels, groups), start=1):
        _set_seed(seed + fold_index)

        train_windows = torch.tensor(windows[train_idx], dtype=torch.float32)
        test_windows = torch.tensor(windows[test_idx], dtype=torch.float32)
        train_labels = torch.tensor(labels[train_idx], dtype=torch.long)
        train_targets = torch.tensor(eigen_targets[train_idx], dtype=torch.float32)

        channel_mean = train_windows.mean(dim=(0, 1), keepdim=True)
        channel_std = train_windows.std(dim=(0, 1), keepdim=True).clamp_min(1e-6)
        train_windows = (train_windows - channel_mean) / channel_std
        test_windows = (test_windows - channel_mean) / channel_std

        target_mean = train_targets.mean(dim=0, keepdim=True)
        target_std = train_targets.std(dim=0, keepdim=True).clamp_min(1e-6)
        normalized_targets = (train_targets - target_mean) / target_std

        loader = DataLoader(
            TensorDataset(train_windows, train_labels, normalized_targets),
            batch_size=batch_size,
            shuffle=True,
        )

        model = MultitaskTemporalCNN(
            input_channels=windows.shape[-1],
            target_dim=eigen_targets.shape[-1],
        ).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
        classification_loss_fn = nn.CrossEntropyLoss()
        regression_loss_fn = nn.MSELoss()

        model.train()
        for epoch in range(1, epochs + 1):
            epoch_total = 0.0
            epoch_classification = 0.0
            epoch_regression = 0.0
            batches = 0
            for batch_windows, batch_labels, batch_targets in loader:
                batch_windows = batch_windows.to(device)
                batch_labels = batch_labels.to(device)
                batch_targets = batch_targets.to(device)
                optimizer.zero_grad()
                class_logits, eigen_pred = model(batch_windows)
                classification_loss = classification_loss_fn(class_logits, batch_labels)
                regression_loss = regression_loss_fn(eigen_pred, batch_targets)
                total_loss = classification_weight * classification_loss + regression_weight * regression_loss
                total_loss.backward()
                optimizer.step()
                epoch_total += float(total_loss.item())
                epoch_classification += float(classification_loss.item())
                epoch_regression += float(regression_loss.item())
                batches += 1
            training_history.append(
                {
                    "fold": fold_index,
                    "epoch": epoch,
                    "total_loss": epoch_total / max(batches, 1),
                    "classification_loss": epoch_classification / max(batches, 1),
                    "regression_loss": epoch_regression / max(batches, 1),
                }
            )

        model.eval()
        with torch.no_grad():
            class_logits, normalized_predictions = model(test_windows.to(device))
            probabilities = torch.softmax(class_logits, dim=1)[:, 1].cpu().numpy()
            predicted_eigenvalues = (
                normalized_predictions.cpu() * target_std + target_mean
            ).numpy()

        class_predictions = (probabilities >= 0.5).astype(np.int8)
        left_out_subject = str(np.unique(groups[test_idx])[0])
        folds.append(
            {
                "fold": fold_index,
                "left_out_subject": left_out_subject,
                **_classification_metrics(labels[test_idx], probabilities, class_predictions),
                **_regression_metrics(eigen_targets[test_idx], predicted_eigenvalues),
            }
        )

        for sample_idx, probability, prediction in zip(test_idx, probabilities, class_predictions, strict=False):
            classification_predictions.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "y_true": int(labels[sample_idx]),
                    "y_pred": int(prediction),
                    "probability_lsd": float(probability),
                }
            )

        for sample_idx, truth, pred in zip(test_idx, eigen_targets[test_idx], predicted_eigenvalues, strict=False):
            eigen_predictions.append(
                {
                    "fold": fold_index,
                    "subject": str(groups[sample_idx]),
                    "true_eigenvalues": [float(value) for value in truth],
                    "predicted_eigenvalues": [float(value) for value in pred],
                }
            )

    return {
        "device": device.type,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "classification_weight": classification_weight,
        "regression_weight": regression_weight,
        "target_names": target_names,
        "folds": folds,
        "aggregate": _aggregate_folds(folds),
        "classification_predictions": classification_predictions,
        "eigen_predictions": eigen_predictions,
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


def _write_classification_predictions_csv(path: Path, model_results: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ("model", "fold", "subject", "y_true", "y_pred", "probability_lsd")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for model_name, payload in model_results.items():
            for row in payload.get("classification_predictions", payload.get("predictions", [])):
                writer.writerow(
                    {
                        "model": model_name,
                        "fold": row["fold"],
                        "subject": row["subject"],
                        "y_true": row["y_true"],
                        "y_pred": row["y_pred"],
                        "probability_lsd": row["probability_lsd"],
                    }
                )


def _write_eigen_predictions_csv(path: Path, model_results: dict[str, Any], target_names: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["model", "fold", "subject"]
    fieldnames.extend(f"true_{name}" for name in target_names)
    fieldnames.extend(f"pred_{name}" for name in target_names)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for model_name, payload in model_results.items():
            prediction_rows = payload.get("eigen_predictions", [])
            if not prediction_rows:
                prediction_rows = []
                for row in payload.get("predictions", []):
                    prediction_rows.append(
                        {
                            "fold": row["fold"],
                            "subject": row["subject"],
                            "true_eigenvalues": [row["eigen_true"][name] for name in target_names],
                            "predicted_eigenvalues": [row["eigen_pred"][name] for name in target_names],
                        }
                    )
            for row in prediction_rows:
                serialized = {"model": model_name, "fold": row["fold"], "subject": row["subject"]}
                serialized.update({f"true_{name}": row["true_eigenvalues"][index] for index, name in enumerate(target_names)})
                serialized.update({f"pred_{name}": row["predicted_eigenvalues"][index] for index, name in enumerate(target_names)})
                writer.writerow(serialized)


def _write_markdown_report(path: Path, summary: dict[str, Any]) -> None:
    ranking = sorted(
        summary["models"].items(),
        key=lambda item: (
            item[1]["aggregate"]["eigen_r2_mean"],
            item[1]["aggregate"]["balanced_accuracy_mean"],
        ),
        reverse=True,
    )
    lines = [
        "# LSD Multitask Spectral Benchmark",
        "",
        f"- Dataset: `{summary['dataset_path']}`",
        f"- Samples: {summary['dataset']['sample_count']}",
        f"- Subjects: {summary['dataset']['subject_count']}",
        f"- Window shape: `{summary['dataset']['window_length']} x {summary['dataset']['module_count']}`",
        f"- CV: `{summary['cv_strategy']}`",
        "- Targets: `LSD vs placebo` classification plus per-window FC eigenvalue regression.",
        "- Engineered baselines use graph-informed summary features plus FC upper-triangle edges, but exclude the eigenvalue targets themselves.",
        "- The temporal CNN sees only raw windows and learns a shared representation for both heads.",
        "",
        "## Model Comparison",
        "",
        "| Model | Balanced Accuracy | ROC AUC | Eigen MAE | Eigen RMSE | Eigen R2 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for model_name, payload in ranking:
        aggregate = payload["aggregate"]
        lines.append(
            f"| {model_name} | "
            f"{aggregate['balanced_accuracy_mean']:.3f} ± {aggregate['balanced_accuracy_std']:.3f} | "
            f"{aggregate['roc_auc_mean']:.3f} ± {aggregate['roc_auc_std']:.3f} | "
            f"{aggregate['eigen_mae_mean']:.3f} ± {aggregate['eigen_mae_std']:.3f} | "
            f"{aggregate['eigen_rmse_mean']:.3f} ± {aggregate['eigen_rmse_std']:.3f} | "
            f"{aggregate['eigen_r2_mean']:.3f} ± {aggregate['eigen_r2_std']:.3f} |"
        )

    ridge = summary["models"].get("ridge_multitask")
    if ridge and ridge.get("top_classification_features"):
        lines.extend(["", "## Top Ridge Classification Features", ""])
        for item in ridge["top_classification_features"][:10]:
            lines.append(
                f"- `{item['feature']}`: abs={item['importance']:.4f}, signed={item['signed_weight']:.4f}"
            )

    if ridge and ridge.get("top_regression_features"):
        lines.extend(["", "## Top Ridge Regression Features", ""])
        for item in ridge["top_regression_features"][:10]:
            lines.append(
                f"- `{item['feature']}`: abs={item['importance']:.4f}, signed={item['signed_weight']:.4f}"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The spectral targets are a compact graph-level summary of each 8-module FC window, not a claim of receptor or subjective realism.",
            (
                "- If the temporal CNN improves condition and spectrum metrics together, it is "
                "learning a useful shared macro-dynamics representation rather than only a label boundary."
            ),
            (
                "- If the engineered baselines dominate spectral regression, that means explicit FC "
                "geometry is still the strongest hand-built projection of the current windows."
            ),
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark multitask models on LSD vs placebo classification and per-window FC eigenvalue targets."
    )
    parser.add_argument("--dataset", default=str(REPO_ROOT / "results" / "training" / "ds003059_windows.npz"))
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "results" / "training" / "multitask_benchmark"))
    parser.add_argument("--epochs", type=int, default=16)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--classification-weight", type=float, default=1.0)
    parser.add_argument("--regression-weight", type=float, default=1.0)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_window_dataset(dataset_path)
    eigen_targets, target_names = build_window_eigenvalue_targets(np.asarray(dataset["windows"], dtype=float))
    np.savez_compressed(
        output_dir / "window_fc_eigenvalue_targets.npz",
        eigenvalues=eigen_targets,
        target_names=np.asarray(target_names, dtype="U16"),
        subject=np.asarray(dataset["subject"]),
        condition=np.asarray(dataset["condition"]),
        session=np.asarray(dataset.get("session", [])),
        run=np.asarray(dataset.get("run", [])),
    )

    sklearn_results = evaluate_sklearn_multitask_models(dataset, random_state=args.seed)
    cnn_results = evaluate_multitask_temporal_cnn(
        dataset,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        seed=args.seed,
        classification_weight=args.classification_weight,
        regression_weight=args.regression_weight,
    )

    summary = {
        "task": "lsd_condition_and_fc_eigenvalue_multitask",
        "dataset_path": str(dataset_path),
        "cv_strategy": "LeaveOneGroupOut(subject)",
        "dataset": sklearn_results["dataset"],
        "feature_names": sklearn_results["feature_names"],
        "target_names": sklearn_results["target_names"],
        "models": {
            **sklearn_results["models"],
            "multitask_temporal_cnn": cnn_results,
        },
    }

    (output_dir / "comparison_summary.json").write_text(
        json.dumps(_to_plain_python(summary), indent=2),
        encoding="utf-8",
    )
    _write_classification_predictions_csv(output_dir / "classification_predictions.csv", summary["models"])
    _write_eigen_predictions_csv(output_dir / "eigen_predictions.csv", summary["models"], summary["target_names"])
    _write_markdown_report(output_dir / "benchmark_report.md", summary)

    best_classification = max(
        summary["models"].items(),
        key=lambda item: item[1]["aggregate"]["balanced_accuracy_mean"],
    )
    best_regression = max(
        summary["models"].items(),
        key=lambda item: item[1]["aggregate"]["eigen_r2_mean"],
    )
    print(
        json.dumps(
            {
                "best_classification_model": best_classification[0],
                "best_classification_balanced_accuracy": best_classification[1]["aggregate"]["balanced_accuracy_mean"],
                "best_regression_model": best_regression[0],
                "best_regression_r2": best_regression[1]["aggregate"]["eigen_r2_mean"],
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
