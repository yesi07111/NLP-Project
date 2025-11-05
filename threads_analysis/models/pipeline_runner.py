import argparse
import subprocess
import os
import sys
from pathlib import Path


def run(cmd: list):
    print(f"\n[RUN] {' '.join(cmd)}\n", flush=True)
    result = subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(f"Command failed: {' '.join(cmd)}")


def auto_input_dim(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """
    Computes embedding dimension automatically.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    emb_dim = model.get_sentence_embedding_dimension()
    input_dim = 4 * emb_dim + 2
    print(f"[INFO] Auto-detected emb_dim={emb_dim}, input_dim={input_dim}")
    return input_dim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-chats", default="threads_analysis_results/train_chats")
    parser.add_argument("--output-dir", default="threads_analysis/models/output")
    parser.add_argument("--model-name", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--folds", type=int, default=5)
    args = parser.parse_args()

    train_chats = Path(args.train_chats)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pairs_path = str(output_dir / "pairs_with_hard_neg.jsonl")

    # 1. Build dataset with hard negatives
    run([
        sys.executable, '-m', 'threads_analysis.models.dataset_builder',
        '--input-dir', str(train_chats),
        '--output', pairs_path
    ])

    # 2. Train model with K-fold
    run([
        sys.executable, '-m', 'threads_analysis.models.siamese_bi_encoder',
        '--pairs', pairs_path,
        '--output-dir', str(output_dir),
        '--epochs', str(args.epochs),
        '--batch-size', str(args.batch_size),
        '--folds', str(args.folds)
    ])

    # Detect input_dim automatically
    input_dim = auto_input_dim(args.model_name)

    # 3. Export best fold to ONNX (example: fold 1)
    best_fold_path = str(output_dir / 'siamese_mlp_fold1.pth')
    onnx_out = str(output_dir / 'siamese_mlp.onnx')

    run([
        sys.executable, '-m', 'threads_analysis.models.onnx_export',
        '--model-pth', best_fold_path,
        '--input-dim', str(input_dim),
        '--out', onnx_out
    ])

    # 4. Evaluate
    run([
        sys.executable, '-m', 'threads_analysis.models.evaluation',
        '--pairs', pairs_path,
        '--model-pth', best_fold_path,
        '--input-dim', str(input_dim)
    ])

    print("\n✅ Pipeline completado con éxito.")


if __name__ == "__main__":
    main()