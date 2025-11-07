"""
export_onnx.py

Exporta a ONNX el MEJOR fold de cada modelo:
 - Bi-encoder A (SentenceTransformer)
 - Bi-encoder B (SentenceTransformer)
 - Cross-encoder (AutoModelForSequenceClassification)
 - MLP asociado a cada bi-encoder

Asume que train_all_models() ya copió los mejores en:
    output/best/
        bi_encoder_A/
        bi_encoder_B/
        cross_encoder/
"""

import os
import torch
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# === MLP definition (same as training) ===
import torch.nn as nn

class SmallMLP(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 512, hidden2: int = 128, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden2, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ------------------------------------------------------------
# ✅ Utility: export SentenceTransformer to ONNX
# ------------------------------------------------------------
def export_sentence_transformer(model_dir: str, output_dir: str):
    print(f"[ONNX] Exporting SentenceTransformer: {model_dir}")

    model = SentenceTransformer(model_dir).to(DEVICE)
    os.makedirs(output_dir, exist_ok=True)

    # Prepare dummy inputs
    text = ["example text for onnx export"]
    inputs = model.tokenize(text)
    input_ids = inputs["input_ids"].to(DEVICE)
    attention_mask = inputs["attention_mask"].to(DEVICE)

    # Run once to get shape
    with torch.no_grad():
        model_output = model({"input_ids": input_ids, "attention_mask": attention_mask})
        emb_dim = model_output.shape[-1]

    print(f"[ONNX] Embedding dim = {emb_dim}")

    dummy_input = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }

    onnx_path = os.path.join(output_dir, "model.onnx")

    torch.onnx.export(
        model,
        (dummy_input,),
        onnx_path,
        input_names=["input"],
        output_names=["embeddings"],
        opset_version=17,
        dynamic_axes={
            "input": {0: "batch", 1: "seq"},
            "embeddings": {0: "batch"},
        }
    )

    print(f"[ONNX] Saved ONNX bi-encoder → {onnx_path}")
    return emb_dim


# ------------------------------------------------------------
# ✅ Utility: export MLP classifier to ONNX
# ------------------------------------------------------------
def export_mlp(mlp_path: str, input_dim: int, output_dir: str):
    print(f"[ONNX] Exporting MLP: {mlp_path}")

    mlp = SmallMLP(input_dim=input_dim)
    mlp.load_state_dict(torch.load(mlp_path, map_location="cpu"))
    mlp = mlp.to(DEVICE)
    mlp.eval()

    os.makedirs(output_dir, exist_ok=True)
    dummy = torch.randn(1, input_dim).to(DEVICE)

    onnx_path = os.path.join(output_dir, "mlp.onnx")

    torch.onnx.export(
        mlp,
        dummy,
        onnx_path,
        input_names=["features"],
        output_names=["prob"],
        opset_version=17,
        dynamic_axes={"features": {0: "batch"}, "prob": {0: "batch"}},
    )

    print(f"[ONNX] Saved ONNX MLP → {onnx_path}")


# ------------------------------------------------------------
# ✅ Utility: export Cross-encoder to ONNX
# ------------------------------------------------------------
def export_cross_encoder(model_dir: str, output_dir: str):
    print(f"[ONNX] Exporting CrossEncoder: {model_dir}")

    os.makedirs(output_dir, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(DEVICE)
    model.eval()

    dummy_text = "This is example text A [SEP] and example text B"
    enc = tokenizer(dummy_text, truncation=True, padding="max_length",
                    max_length=256, return_tensors="pt")

    enc = {k: v.to(DEVICE) for k, v in enc.items()}

    onnx_path = os.path.join(output_dir, "model.onnx")

    torch.onnx.export(
        model,
        (enc["input_ids"], enc["attention_mask"]),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        opset_version=17,
        dynamic_axes={
            "input_ids": {0: "batch", 1: "seq"},
            "attention_mask": {0: "batch", 1: "seq"},
            "logits": {0: "batch"},
        }
    )

    print(f"[ONNX] Saved ONNX cross-encoder → {onnx_path}")


# ------------------------------------------------------------
# ✅ MAIN EXPORTER
# ------------------------------------------------------------
def export_all(best_dir="threads_analysis/models/output/best",
               output_onnx="threads_analysis/models/output/onnx"):

    print(f"[INFO] Exporting ONNX from best models in: {best_dir}")

    os.makedirs(output_onnx, exist_ok=True)

    # ------------------------------------------------------------
    # ✅ BI-ENCODER A
    # ------------------------------------------------------------
    bi_a_dir = os.path.join(best_dir, "bi_encoder_A")
    if os.path.exists(bi_a_dir):
        out_a = os.path.join(output_onnx, "bi_encoder_A")
        emb_dim_a = export_sentence_transformer(bi_a_dir, out_a)

        # Load MLP for this bi-encoder
        mlp_path = os.path.join(bi_a_dir, "mlp_on_sentence_transformers", "mlp_model.pth")
        if os.path.exists(mlp_path):
            export_mlp(mlp_path, input_dim=emb_dim_a*4 + 9, output_dir=out_a)
        else:
            print("[WARN] MLP for bi-encoder A not found.")

    # ------------------------------------------------------------
    # ✅ BI-ENCODER B
    # ------------------------------------------------------------
    bi_b_dir = os.path.join(best_dir, "bi_encoder_B")
    if os.path.exists(bi_b_dir):
        out_b = os.path.join(output_onnx, "bi_encoder_B")
        emb_dim_b = export_sentence_transformer(bi_b_dir, out_b)

        # Load MLP for this bi-encoder
        mlp_path = os.path.join(bi_b_dir, "mlp_on_sentence_transformers", "mlp_model.pth")
        if os.path.exists(mlp_path):
            export_mlp(mlp_path, input_dim=emb_dim_b*4 + 9, output_dir=out_b)
        else:
            print("[WARN] MLP for bi-encoder B not found.")

    # ------------------------------------------------------------
    # ✅ CROSS-ENCODER
    # ------------------------------------------------------------
    cross_dir = os.path.join(best_dir, "cross_encoder")
    if os.path.exists(cross_dir):
        out_c = os.path.join(output_onnx, "cross_encoder")
        export_cross_encoder(cross_dir, out_c)
    else:
        print("[WARN] Cross-encoder best fold not found.")

    print(f"[DONE] ✅ ONNX export completed. Saved in: {output_onnx}")


# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--best-dir", type=str,
                        default="threads_analysis/models/output/best")
    parser.add_argument("--out", type=str,
                        default="threads_analysis/models/output/onnx")
    args = parser.parse_args()

    export_all(best_dir=args.best_dir, output_onnx=args.out)
