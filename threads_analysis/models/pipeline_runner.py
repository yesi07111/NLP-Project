"""
pipeline_runner.py
Ejecuta TODO el pipeline de principio a fin:

1. Construcción de dataset + hard negatives
2. Entrenamiento de los tres modelos (K-fold):
   - bi-encoder A (MiniLM)
   - bi-encoder B (MPNet)
   - cross-encoder (MiniLM-cross)
3. Selección del mejor fold por F1
4. Exportación ONNX para cada modelo
5. Evaluación final:
   - heurísticas
   - bi-encoder A
   - bi-encoder B
   - cross-encoder
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from time import sleep

# -------- Colored logs ----------
class Colors:
    OK = "\033[92m"
    INFO = "\033[94m"
    WARN = "\033[93m"
    ERR = "\033[91m"
    END = "\033[0m"

def log_info(msg):
    print(f"{Colors.INFO}[INFO]{Colors.END} {msg}", flush=True)

def log_ok(msg):
    print(f"{Colors.OK}[OK]{Colors.END} {msg}", flush=True)

def log_warn(msg):
    print(f"{Colors.WARN}[WARN]{Colors.END} {msg}", flush=True)

def log_err(msg):
    print(f"{Colors.ERR}[ERR]{Colors.END} {msg}", flush=True)


# -------- Runner helper ----------
def run(cmd: list):
    log_info(f"Ejecutando comando: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if result.returncode != 0:
        log_err(f"Fallo ejecutando: {' '.join(cmd)}")
        raise SystemExit(result.returncode)


# -------- Auto detect input_dim --------
def auto_input_dim(model_name):
    """
    Obtiene input_dim basado en el bi-encoder elegido.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    emb_dim = model.get_sentence_embedding_dimension()

    # 4 concatenaciones + 2 features adicionales
    input_dim = 4 * emb_dim + 2

    log_info(f"Detectado emb_dim={emb_dim}, input_dim={input_dim}")
    return input_dim


# -------- Global progress bar -------
def progress_bar(step, total):
    bar_len = 40
    filled = int(bar_len * step / total)
    bar = "█" * filled + "-" * (bar_len - filled)
    print(f"\r{Colors.INFO}Progreso global:{Colors.END} [{bar}] {step}/{total}", end="", flush=True)
    if step == total:
        print("\n")


# ===============================================================
# ============================ MAIN ==============================
# ===============================================================
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--train-chats", default="threads_analysis_results/train_chats")
    parser.add_argument("--output-dir", default="threads_analysis/models/output")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    TOTAL_STEPS = 5
    current_step = 0

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pairs_path = str(output_dir / "pairs_with_hard_neg.jsonl")

    # ============================================================
    # STEP 1) Build dataset (solo si no existe dataset preconstruido)
    # ============================================================
    current_step += 1
    progress_bar(current_step, TOTAL_STEPS)

    meta_path = Path(pairs_path + ".meta")
    dataset_exists = Path(pairs_path).exists() and meta_path.exists()

    if dataset_exists:
        try:
            import json
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            valid = True
            if meta.get("version") != 2:
                valid = False
            if meta.get("embedding_model") != "sentence-transformers/all-mpnet-base-v2":
                valid = False
            if not isinstance(meta.get("chat_files"), list) or len(meta["chat_files"]) == 0:
                valid = False
            if "params" not in meta:
                valid = False

            if valid:
                log_ok("Dataset detectado y válido. Se usará el dataset existente.")
            else:
                log_warn("Dataset existente pero meta inválido. Se reconstruirá.")
                dataset_exists = False

        except Exception as e:
            log_warn(f"No se pudo leer el meta. Se reconstruirá. Error: {e}")
            dataset_exists = False

    if not dataset_exists:
        log_info("Construyendo dataset desde cero...")
        run([
            sys.executable, "-m", "threads_analysis.models.dataset_builder",
            "--input-dir", args.train_chats,
            "--output", pairs_path
        ])
        log_ok("Dataset construido.")
    else:
        log_info("Saltando construcción de dataset (ya existe).")


    # ============================================================
    # STEP 2) Train models
    # ============================================================
    current_step += 1
    progress_bar(current_step, TOTAL_STEPS)

    log_info("Entrenando los modelos (model_trainer.py)...")

    run([
        sys.executable, "-m", "threads_analysis.models.model_trainer",
        "--pairs", pairs_path,
        "--output-dir", str(output_dir),
        # "--epochs", str(args.epochs),
        # "--batch-size", str(args.batch_size),
        # "--folds", str(args.folds)
    ])

    log_ok("Modelos entrenados exitosamente.")

    # ============================================================
    # STEP 3) Export best fold to ONNX
    # ============================================================
    current_step += 1
    progress_bar(current_step, TOTAL_STEPS)

    log_info("Buscando el mejor fold de cada modelo...")

    # -------- Load f1 summary ----------
    summary_path = output_dir / "training_summary.json"
    if not summary_path.exists():
        log_err("No existe training_summary.json. Algo falló en el entrenamiento.")
        raise SystemExit(1)

    import json
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    best_fold_mini = summary["bi_encoder_A"]["best_fold"]
    best_fold_mpnet = summary["bi_encoder_B"]["best_fold"]
    best_fold_cross = summary["cross_encoder"]["best_fold"]

    log_ok(f"Mejor fold MiniLM-bi-encoder: {best_fold_mini}")
    log_ok(f"Mejor fold MPNet-bi-encoder: {best_fold_mpnet}")
    log_ok(f"Mejor fold Cross-Encoder: {best_fold_cross}")

    # --- Exportación ONNX de cada modelo ---
    log_info("Exportando modelos a ONNX...")

    # A) Bi-encoder A
    run([
        sys.executable, "-m", "threads_analysis.models.onnx_export",
        "--model-type", "biA",
        "--fold", str(best_fold_mini),
        "--output-dir", str(output_dir)
    ])

    # B) Bi-encoder B
    run([
        sys.executable, "-m", "threads_analysis.models.onnx_export",
        "--model-type", "biB",
        "--fold", str(best_fold_mpnet),
        "--output-dir", str(output_dir)
    ])

    # C) Cross-encoder
    run([
        sys.executable, "-m", "threads_analysis.models.onnx_export",
        "--model-type", "cross",
        "--fold", str(best_fold_cross),
        "--output-dir", str(output_dir)
    ])

    log_ok("ONNX exportado para los 3 modelos.")

    # ============================================================
    # STEP 4) Evaluate models vs heuristics
    # ============================================================
    current_step += 1
    progress_bar(current_step, TOTAL_STEPS)

    log_info("Evaluando heurísticas y los 3 modelos...")

    run([
        sys.executable, "-m", "threads_analysis.models.evaluation",
        "--pairs", pairs_path,
        "--models-dir", str(output_dir)
    ])

    log_ok("Evaluación completada.")

    # ============================================================
    # DONE
    # ============================================================
    current_step += 1
    progress_bar(current_step, TOTAL_STEPS)

    print(f"\n{Colors.OK}✅ Pipeline completado con éxito.{Colors.END}")


if __name__ == "__main__":
    main()
