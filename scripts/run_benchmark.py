"""Repeatable multi-dataset, multi-model benchmark for the Collab CLI pipeline."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_iris, load_wine
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
RANDOM_STATE = 42

def datasets_for_suite(suite: str):
    loaders = {
        "iris": load_iris,
        "wine": load_wine,
        "breast_cancer": load_breast_cancer,
    }
    names = ["iris"] if suite == "smoke" else list(loaders)
    return [(name, loaders[name](as_frame=True)) for name in names]

def models_for_suite(suite: str):
    models = {
        "LogisticRegression": Pipeline([
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]),
        "RandomForest": RandomForestClassifier(
            n_estimators=120, min_samples_leaf=2, random_state=RANDOM_STATE, n_jobs=1
        ),
        "SVC_RBF": Pipeline([
            ("scale", StandardScaler()),
            ("model", SVC(C=2.0, kernel="rbf", probability=True, random_state=RANDOM_STATE)),
        ]),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=100, max_leaf_nodes=15, random_state=RANDOM_STATE
        ),
    }
    return models

def safe_roc_auc(model, X_test, y_test, n_classes):
    try:
        if n_classes == 2:
            probabilities = model.predict_proba(X_test)[:, 1]
            return float(roc_auc_score(y_test, probabilities))
        probabilities = model.predict_proba(X_test)
        return float(roc_auc_score(y_test, probabilities, multi_class="ovr", average="weighted"))
    except (ValueError, AttributeError):
        return None

def run_benchmarks(suite: str | None = None):
    suite = (suite or os.getenv("BENCHMARK_SUITE", "extended")).lower()
    if suite not in {"smoke", "extended"}:
        raise ValueError("BENCHMARK_SUITE must be 'smoke' or 'extended'")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, detailed = [], {}
    cv_folds = 3 if suite == "smoke" else 5

    for dataset_name, bunch in datasets_for_suite(suite):
        X, y = bunch.data, bunch.target
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
        )
        dataset_result = {
            "n_samples": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "n_classes": int(pd.Series(y).nunique()),
            "class_names": [str(c) for c in bunch.target_names],
            "models": {},
        }
        for model_name, estimator in models_for_suite(suite).items():
            started = time.perf_counter()
            estimator.fit(X_train, y_train)
            fit_seconds = time.perf_counter() - started
            started = time.perf_counter()
            prediction = estimator.predict(X_test)
            predict_seconds = time.perf_counter() - started
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
            cv_scores = cross_val_score(estimator, X, y, cv=cv, scoring="accuracy", n_jobs=1)
            n_classes = int(pd.Series(y).nunique())
            metrics = {
                "dataset": dataset_name,
                "model": model_name,
                "accuracy": float(accuracy_score(y_test, prediction)),
                "balanced_accuracy": float(balanced_accuracy_score(y_test, prediction)),
                "precision_weighted": float(precision_score(y_test, prediction, average="weighted", zero_division=0)),
                "recall_weighted": float(recall_score(y_test, prediction, average="weighted", zero_division=0)),
                "f1_weighted": float(f1_score(y_test, prediction, average="weighted", zero_division=0)),
                "roc_auc_ovr_weighted": safe_roc_auc(estimator, X_test, y_test, n_classes),
                "cv_accuracy_mean": float(np.mean(cv_scores)),
                "cv_accuracy_std": float(np.std(cv_scores, ddof=1)) if len(cv_scores) > 1 else 0.0,
                "fit_seconds": round(fit_seconds, 6),
                "predict_seconds": round(predict_seconds, 6),
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
                "cv_folds": cv_folds,
            }
            rows.append(metrics)
            dataset_result["models"][model_name] = {
                "metrics": metrics,
                "confusion_matrix": confusion_matrix(y_test, prediction).tolist(),
                "classification_report": classification_report(
                    y_test, prediction, target_names=[str(c) for c in bunch.target_names],
                    output_dict=True, zero_division=0
                ),
            }
        detailed[dataset_name] = dataset_result

    results = pd.DataFrame(rows).sort_values(
        ["dataset", "f1_weighted", "cv_accuracy_mean"], ascending=[True, False, False]
    ).reset_index(drop=True)
    results.to_csv(OUT / "benchmark_metrics.csv", index=False)
    with open(OUT / "benchmark_details.json", "w", encoding="utf-8") as f:
        json.dump(detailed, f, indent=2)
    summary = {
        "status": "success",
        "suite": suite,
        "dataset_count": len(detailed),
        "model_count": len(models_for_suite(suite)),
        "experiment_count": len(rows),
        "cv_folds": cv_folds,
        "random_state": RANDOM_STATE,
        "datasets": {
            name: {
                "n_samples": value["n_samples"],
                "n_features": value["n_features"],
                "n_classes": value["n_classes"],
                "best_model_by_f1": max(
                    value["models"].items(), key=lambda item: item[1]["metrics"]["f1_weighted"]
                )[0],
                "best_f1_weighted": max(
                    model["metrics"]["f1_weighted"] for model in value["models"].values()
                ),
            } for name, value in detailed.items()
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(OUT / "benchmark_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    plot_metrics(results)
    print(json.dumps(summary, indent=2))
    return summary

def plot_metrics(results: pd.DataFrame):
    for metric, title, filename in [
        ("f1_weighted", "Weighted F1 by dataset and model", "f1_comparison.png"),
        ("cv_accuracy_mean", "Cross-validation accuracy by dataset and model", "cv_accuracy_comparison.png"),
    ]:
        pivot = results.pivot(index="dataset", columns="model", values=metric)
        ax = pivot.plot(kind="bar", figsize=(11, 6), ylim=(0, 1.05), rot=0)
        ax.set_title(title)
        ax.set_ylabel(metric.replace("_", " ").title())
        ax.set_xlabel("Dataset")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(title="Model", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig(OUT / filename, dpi=140)
        plt.close()

if __name__ == "__main__":
    run_benchmarks()
