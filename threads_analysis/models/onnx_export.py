"""
threads_analysis/models/onnx_export.py

Exporta la MLP entrenada (PyTorch) a ONNX y valida con onnxruntime.

Uso:
python -m threads_analysis.models.onnx_export --fold 1 --input-dim 1538
"""
from __future__ import annotations
import os
import argparse
import numpy as np
import torch
import onnx
import onnxruntime as ort

from threads_analysis.models.siamese_bi_encoder import SimpleMLP


def export_to_onnx(model_pth: str, input_dim: int, out_path: str, opset: int = 12):
    if not os.path.exists(model_pth):
        raise FileNotFoundError(f"[ERROR] No existe el modelo: {model_pth}")

    print(f"[INFO] Cargando modelo: {model_pth}")
    model = SimpleMLP(input_dim)
    model.load_state_dict(torch.load(model_pth, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, input_dim, dtype=torch.float32)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    print(f"[INFO] Exportando a ONNX -> {out_path}")
    torch.onnx.export(
        model,
        dummy_input,
        out_path,
        input_names=["input"],
        output_names=["output"],
        opset_version=opset
    )

    print(f"[OK] Modelo exportado a: {out_path}")

    # quick check
    sess = ort.InferenceSession(out_path)
    out = sess.run(None, {"input": dummy_input.numpy()})
    print("[INFO] ONNX output shape:", np.array(out).shape)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--fold", type=int, required=True,
                        help="Número de fold a exportar (1..N)")
    parser.add_argument("--input-dim", type=int, required=True)
    parser.add_argument("--models-dir", type=str,
                        default="threads_analysis/models/output",
                        help="Directorio donde están los folds")
    parser.add_argument("--out", type=str,
                        default="threads_analysis/models/output/siamese_mlp.onnx")

    args = parser.parse_args()

    # RUTA CORRECTA DEL MODELO
    model_pth = os.path.join(args.models_dir, f"fold_{args.fold}", "model.pth")

    export_to_onnx(model_pth, args.input_dim, args.out)
