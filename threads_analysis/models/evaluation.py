"""
threads_analysis/models/evaluation.py

Evalúa:
- Heurísticas del grafo
- Bi-encoder A
- Bi-encoder B
- Cross-encoder

Usando el dataset generado en dataset_builder.py
Toma automáticamente el mejor fold desde training_summary.json.

Uso:
python -m threads_analysis.models.evaluation \
    --pairs threads_analysis/models/output/pairs_with_hard_neg.jsonl \
    --models-dir threads_analysis/models/output
"""

from __future__ import annotations
import os
import json
from typing import List, Dict, Any
import numpy as np
from tqdm import tqdm
import torch
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

from threads_analysis.knowledge_graph import ConversationGraphBuilder
from threads_analysis.models.triple_model_trainer import (
    EmbeddingCache,
    load_mlp_from_path,
    make_features,
    make_cross_features
)

# -------------- Colored logs ----------------------------------
class Colors:
    OK = "\033[92m"
    INFO = "\033[94m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    END = "\033[0m"

def log_info(msg): print(f"{Colors.INFO}[INFO]{Colors.END} {msg}")
def log_ok(msg): print(f"{Colors.OK}[OK]{Colors.END} {msg}")
def log_warn(msg): print(f"{Colors.WARN}[WARN]{Colors.END} {msg}")
def log_err(msg): print(f"{Colors.ERR}[ERR]{Colors.END} {msg}")


# ------------------------------------------------------------------------
# Load best model paths according to training_summary.json
# ------------------------------------------------------------------------
def load_best_models(models_dir: str):
    summary_path = os.path.join(models_dir, "training_summary.json")

    if not os.path.exists(summary_path):
        log_err("ERROR: No se encuentra training_summary.json")
        raise SystemExit(1)

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    best = {
        "biA": summary["bi_encoder_A"]["best_fold"],
        "biB": summary["bi_encoder_B"]["best_fold"],
        "cross": summary["cross_encoder"]["best_fold"],
    }

    # Construimos rutas
    model_paths = {
        "biA": os.path.join(models_dir, f"bi_encoder_A_fold{best['biA']}.pth"),
        "biB": os.path.join(models_dir, f"bi_encoder_B_fold{best['biB']}.pth"),
        "cross": os.path.join(models_dir, f"cross_encoder_fold{best['cross']}.pth"),
    }

    return model_paths, summary


# ------------------------------------------------------------------------
# Evaluation function
# ------------------------------------------------------------------------
def evaluate_model(model, featurizer, pairs: str, model_type: str):
    log_info(f"Evaluando modelo: {model_type}")

    emb_cache = EmbeddingCache()
    ys = []
    yps = []

    with open(pairs, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            a = obj["a"]
            b = obj["b"]
            label = int(obj["label"])

            ys.append(label)

            emb_a = emb_cache.get(a["text"])
            emb_b = emb_cache.get(b["text"])
            time_delta = float(obj.get("time_delta_min", 99999.0))
            same_author = int(obj.get("same_author", 0))

            if model_type == "cross":
                X = torch.from_numpy(
                    featurizer(a["text"], b["text"])
                ).unsqueeze(0)
            else:
                X = torch.from_numpy(
                    featurizer(emb_a, emb_b, time_delta, same_author)
                ).unsqueeze(0)

            with torch.no_grad():
                pred = float(model(X).cpu().numpy().squeeze())

            yps.append(pred)

    # Compute metrics
    preds_bin = [1 if p >= 0.5 else 0 for p in yps]

    p, r, f1, _ = precision_recall_fscore_support(
        ys, preds_bin, average="binary", zero_division=0
    )

    try:
        auc = roc_auc_score(ys, yps)
    except ValueError:
        auc = 0.0

    log_ok(f"{model_type}: AUC={auc:.4f}  P={p:.4f}  R={r:.4f}  F1={f1:.4f}")

    return {"auc": auc, "p": p, "r": r, "f1": f1}


# ------------------------------------------------------------------------
# Heuristics evaluation
# ------------------------------------------------------------------------
def evaluate_heuristics(pairs: str):
    log_info("Evaluando Heurísticas...")

    kg = ConversationGraphBuilder()
    ys = []
    yps = []

    with open(pairs, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            a = obj["a"]
            b = obj["b"]
            label = int(obj["label"])
            ys.append(label)

            try:
                pred = kg._calculate_reply_probability(a, b)
            except Exception:
                pred = 0.0
            yps.append(pred)

    preds_bin = [1 if p >= 0.5 else 0 for p in yps]

    p, r, f1, _ = precision_recall_fscore_support(
        ys, preds_bin, average="binary", zero_division=0
    )

    try:
        auc = roc_auc_score(ys, yps)
    except ValueError:
        auc = 0.0

    log_ok(f"Heuristicas: AUC={auc:.4f}  P={p:.4f}  R={r:.4f}  F1={f1:.4f}")

    return {"auc": auc, "p": p, "r": r, "f1": f1}


# ------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=str, required=True)
    parser.add_argument("--models-dir", type=str, required=True)
    args = parser.parse_args()

    models_dir = args.models_dir

    # Load best fold models
    model_paths, summary = load_best_models(models_dir)

    # Load PyTorch models
    log_info("Cargando modelos de mejor fold...")

    biA_model = load_mlp_from_path(model_paths["biA"], summary["bi_encoder_A"]["input_dim"])
    biB_model = load_mlp_from_path(model_paths["biB"], summary["bi_encoder_B"]["input_dim"])
    cross_model = load_mlp_from_path(model_paths["cross"], summary["cross_encoder"]["input_dim"])

    # Run evaluations
    results = {}

    results["heuristics"] = evaluate_heuristics(args.pairs)
    results["biA"] = evaluate_model(biA_model, make_features, args.pairs, "biA")
    results["biB"] = evaluate_model(biB_model, make_features, args.pairs, "biB")
    results["cross"] = evaluate_model(cross_model, make_cross_features, args.pairs, "cross")

    # ---- Summary ----
    print("\n==============================")
    print("📊 RESUMEN FINAL MODELOS")
    print("==============================")
    for k, v in results.items():
        print(f"{k}: AUC={v['auc']:.4f}  P={v['p']:.4f}  R={v['r']:.4f}  F1={v['f1']:.4f}")

    print("\n✅ Evaluación completa.")


if __name__ == "__main__":
    main()
