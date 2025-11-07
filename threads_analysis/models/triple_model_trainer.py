"""
threads_analysis/models/triple_model_trainer.py

Entrena (fine-tune completo) tres modelos:
 - Bi-encoder A: paraphrase-multilingual-mpnet-base-v2
 - Bi-encoder B: sentence-transformers/all-MiniLM-L12-v2
 - Cross-encoder: cross-encoder/ms-marco-MiniLM-L-12-v2

Procedure:
 - Carga pairs JSONL (output de dataset_builder.py)
 - Construye folds (GroupKFold si hay >1 chat, otherwise Stratified/KFold)
 - Para cada model:
    * Fine-tune modelo (bi-encoders con MultipleNegativesRankingLoss; cross-encoder como classifier)
    * Después de fine-tune para bi-encoders: extraer embeddings y entrenar MLP classifier (opcional)
 - Guarda modelos por fold en: output_dir/fold_{fold}/{model_tag}/
 - Guarda métricas en metrics.json en cada fold dir
"""
from __future__ import annotations
import os
import json
import math
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path
from glob import glob

import numpy as np
from tqdm import tqdm

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import GroupKFold, StratifiedKFold, KFold
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

# sentence-transformers / transformers
from sentence_transformers import SentenceTransformer, InputExample, losses
# cross_encoder from sentence-transformers not strictly required here but kept for reference
from sentence_transformers.cross_encoder import CrossEncoder

# transformers: tokenizer + model for cross-encoder full fine-tune
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

# config: user-requested models
BI_ENCODER_A = "paraphrase-multilingual-mpnet-base-v2"
BI_ENCODER_B = "sentence-transformers/all-MiniLM-L12-v2"
CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-12-v2"

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

# Default training hyperparams (you can override via CLI)
DEFAULT_EPOCHS = 3
DEFAULT_BATCH = 32
DEFAULT_LR = 2e-5
DEFAULT_ACCUM = 2
DEFAULT_WARMUP_PCT = 0.06
DEFAULT_FOLDS = 5

# Simple MLP classifier used after fine-tuning bi-encoders (embeddings -> prob)
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

# Dataset to train the MLP from precomputed features/embeddings
class EmbeddingPairsDataset(Dataset):
    def __init__(self, rows: List[Dict[str, Any]]):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        feat = np.array(r['mlp_features'], dtype=np.float32)
        label = np.float32(r.get('label', 0))
        return torch.from_numpy(feat), torch.tensor(label, dtype=torch.float32)

# Utility to load jsonl pairs
def load_pairs_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows

# Build folds (group aware)
def build_splits(rows: List[Dict[str, Any]], n_splits: int):
    groups = np.array([r.get('chat_id', 0) for r in rows])
    y = np.array([int(r.get('label', 0)) for r in rows])
    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)
    if n_groups >= 2:
        if n_groups < n_splits:
            n_splits = n_groups
        splitter = GroupKFold(n_splits=n_splits)
        splits = list(splitter.split(np.arange(len(rows)), y, groups))
    else:
        # fallback stratified if possible
        if len(np.unique(y)) > 1 and len(y) >= n_splits:
            splitter = StratifiedKFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=RANDOM_SEED)
            splits = list(splitter.split(np.arange(len(rows)), y))
        else:
            splitter = KFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=RANDOM_SEED)
            splits = list(splitter.split(np.arange(len(rows))))
    return splits

# Helper to compute mlp feature vector from embeddings + extras
def build_mlp_features_from_embeddings(emb_a: np.ndarray, emb_b: np.ndarray, extras: Dict[str, Any]) -> np.ndarray:
    a = emb_a.astype(np.float32)
    b = emb_b.astype(np.float32)
    comb = np.concatenate([a, b, np.abs(a - b), a * b], axis=0).astype(np.float32)
    # extras: dict with keys len_a,len_b,tfidf_jaccard,seq_ratio,emoji_diff,both_have_url,both_all_caps,time_delta_min,same_author
    extra_list = [
        float(extras.get('len_a', 0)),
        float(extras.get('len_b', 0)),
        float(extras.get('tfidf_jaccard', 0.0)),
        float(extras.get('seq_ratio', 0.0)),
        float(extras.get('emoji_diff', 0)),
        float(extras.get('both_have_url', 0)),
        float(extras.get('both_all_caps', 0)),
        float(extras.get('time_delta_min', 1e6)),
        float(extras.get('same_author', 0))
    ]
    extra_arr = np.array(extra_list, dtype=np.float32)
    feat = np.concatenate([comb, extra_arr], axis=0)
    return feat

# Train MLP given embeddings cache and rows
def train_mlp_for_fold(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], emb_model: SentenceTransformer,
                       output_dir: str, fold_dir: str, batch_size: int, epochs: int, lr: float, accum_steps: int):
    # prepare mlp features
    print("[MLP] Building features tensors for train/val using embeddings...")
    for r in rows_train:
        emb_a = emb_model.encode(r['a']['text'] or "", convert_to_numpy=True)
        emb_b = emb_model.encode(r['b']['text'] or "", convert_to_numpy=True)
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(emb_a, emb_b, extras)
    for r in rows_val:
        emb_a = emb_model.encode(r['a']['text'] or "", convert_to_numpy=True)
        emb_b = emb_model.encode(r['b']['text'] or "", convert_to_numpy=True)
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(emb_a, emb_b, extras)

    input_dim = rows_train[0]['mlp_features'].shape[0]
    mlp = SmallMLP(input_dim).to(DEVICE)
    opt = torch.optim.AdamW(mlp.parameters(), lr=lr)
    loss_fn = nn.BCELoss()
    train_ds = EmbeddingPairsDataset(rows_train)
    val_ds = EmbeddingPairsDataset(rows_val)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    best_f1 = -1.0
    best_state = None
    for epoch in range(1, epochs + 1):
        mlp.train()
        total_loss = 0.0
        for Xb, yb in train_loader:
            Xb = Xb.to(DEVICE)
            yb = yb.to(DEVICE)
            opt.zero_grad()
            preds = mlp(Xb)
            loss = loss_fn(preds, yb)
            loss.backward()
            opt.step()
            total_loss += loss.item() * Xb.size(0)
        avg_loss = total_loss / len(train_ds)
        # validate
        mlp.eval()
        ys, yps = [], []
        with torch.no_grad():
            for Xv, yv in val_loader:
                Xv = Xv.to(DEVICE)
                pv = mlp(Xv).detach().cpu().numpy().tolist()
                ys.extend(yv.numpy().tolist())
                yps.extend(pv)
        preds_bin = [1 if p >= 0.5 else 0 for p in yps]
        p, r, f, _ = precision_recall_fscore_support(ys, preds_bin, average='binary', zero_division=0)
        print(f"[MLP] Epoch {epoch}: loss={avg_loss:.4f} val_P={p:.4f} val_R={r:.4f} val_F1={f:.4f}")
        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k, v in mlp.state_dict().items()}
    # save best mlp
    if best_state is not None:
        mlp_dir = os.path.join(fold_dir, "mlp_on_" + emb_model.__class__.__module__.split(".")[0])
        os.makedirs(mlp_dir, exist_ok=True)
        model_path = os.path.join(mlp_dir, "mlp_model.pth")
        torch.save(best_state, model_path)
        print(f"[MLP] Saved best mlp to {model_path} (F1={best_f1:.4f})")
    return best_f1

# Fine-tune a bi-encoder using sentence-transformers (MultipleNegativesRankingLoss on positives)
def finetune_bi_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]],
                        output_dir: str, fold: int, epochs: int = 3, batch_size: int = 32, lr: float = 2e-5,
                        warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[BI] Fine-tuning bi-encoder {model_name} (tag={model_tag}) fold={fold}")

    # Create a fresh SentenceTransformer instance
    model = SentenceTransformer(model_name)
    # create train examples: use positives only (MultipleNegativesRankingLoss uses in-batch negatives)
    train_examples = []
    for r in rows_train:
        if r.get('label', 0) == 1:
            a = r['a']['text'] or ""
            b = r['b']['text'] or ""
            train_examples.append(InputExample(texts=[a, b]))
    val_examples = []
    for r in rows_val:
        if r.get('label', 0) == 1:
            val_examples.append(InputExample(texts=[r['a']['text'] or "", r['b']['text'] or ""]))

    if len(train_examples) == 0:
        print("[BI] No positive examples in train for this fold; skipping bi-encoder fine-tune")
        return None, model

    train_dataloader = torch.utils.data.DataLoader(train_examples, shuffle=True, batch_size=batch_size, collate_fn=model.smart_batching_collate)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    # evaluator: use BinaryClassificationEvaluator from sentence-transformers on val set (we'll convert val to pairs)
    from sentence_transformers.evaluation import BinaryClassificationEvaluator
    val_a = [r['a']['text'] for r in rows_val]
    val_b = [r['b']['text'] for r in rows_val]
    val_labels = [int(r.get('label', 0)) for r in rows_val]
    evaluator = BinaryClassificationEvaluator(val_a, val_b, val_labels, show_progress_bar=False)

    warmup_steps = math.ceil(len(train_dataloader) * epochs * warmup_pct)
    model.fit(train_objectives=[(train_dataloader, train_loss)],
              evaluator=evaluator,
              epochs=epochs,
              evaluation_steps=max(1, len(train_dataloader)),
              output_path=os.path.join(output_dir, f"fold_{fold}", model_tag),
              warmup_steps=warmup_steps,
              optimizer_params={'lr': lr},
              use_amp=torch.cuda.is_available())

    print(f"[BI] Saved bi-encoder at {os.path.join(output_dir, f'fold_{fold}', model_tag)}")
    return os.path.join(output_dir, f"fold_{fold}", model_tag), model

# Fine-tune cross-encoder using a PyTorch loop (binary classification)
def finetune_cross_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], 
                           output_dir: str, fold: int, epochs: int = 3, batch_size: int = 16, lr: float = 2e-5,
                           warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[CE] Fine-tuning cross-encoder {model_name} fold={fold}")

    # Use transformers AutoModelForSequenceClassification for full fine-tune (num_labels=1 with BCEWithLogits)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1).to(DEVICE)

    # prepare datasets
    class SeqDataset(Dataset):
        def __init__(self, rows):
            self.rows = rows
        def __len__(self): return len(self.rows)
        def __getitem__(self, idx):
            r = self.rows[idx]
            text = (r['a']['text'] or "") + " [SEP] " + (r['b']['text'] or "")
            label = float(r.get('label', 0))
            enc = tokenizer(text, truncation=True, padding='max_length', max_length=256, return_tensors='pt')
            item = {k: v.squeeze(0) for k,v in enc.items()}
            item['labels'] = torch.tensor(label, dtype=torch.float32)
            return item

    train_ds = SeqDataset(rows_train)
    val_ds = SeqDataset(rows_val)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # optimizer + scheduler
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {'params': [p for n,p in model.named_parameters() if not any(nd in n for nd in no_decay)], 'weight_decay': 0.01},
        {'params': [p for n,p in model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
    ]
    # use torch.optim.AdamW to avoid transformers.AdamW import issues
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=lr)
    total_steps = len(train_loader) // max(1, accum_steps) * epochs
    warmup_steps = max(1, int(total_steps * warmup_pct))
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    scaler = torch.cuda.amp.GradScaler(enabled=torch.cuda.is_available())

    loss_fn = nn.BCEWithLogitsLoss()

    best_f1 = -1.0
    best_state = None

    for epoch in range(1, epochs+1):
        model.train()
        total_loss = 0.0
        optimizer.zero_grad()
        for step, batch in enumerate(train_loader, 1):
            inputs = {k: v.to(DEVICE) for k,v in batch.items() if k != 'labels'}
            labels = batch['labels'].to(DEVICE)
            with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                outputs = model(**inputs)
                logits = outputs.logits.view(-1)
                loss = loss_fn(logits, labels)
                loss = loss / accum_steps
            scaler.scale(loss).backward()
            if step % accum_steps == 0:
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            total_loss += loss.item() * accum_steps

        avg_loss = total_loss / len(train_loader)

        # validation
        model.eval()
        ys, yps = [], []
        with torch.no_grad():
            for batch in val_loader:
                inputs = {k: v.to(DEVICE) for k,v in batch.items() if k != 'labels'}
                labels = batch['labels'].to(DEVICE)
                with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
                    outputs = model(**inputs)
                    logits = outputs.logits.view(-1)
                    probs = torch.sigmoid(logits).detach().cpu().numpy()
                ys.extend(labels.cpu().numpy().tolist())
                yps.extend(probs.tolist())
        preds_bin = [1 if p >= 0.5 else 0 for p in yps]
        p, r, f, _ = precision_recall_fscore_support(ys, preds_bin, average='binary', zero_division=0)
        auc = roc_auc_score(ys, yps) if len(np.unique(ys)) > 1 else 0.0
        print(f"[CE] Epoch {epoch}: loss={avg_loss:.4f} val_AUC={auc:.4f} P={p:.4f} R={r:.4f} F1={f:.4f}")
        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k,v in model.state_dict().items()}

    # save best
    fold_dir = os.path.join(output_dir, f"fold_{fold}")
    model_dir = os.path.join(fold_dir, model_name.split("/")[-1])
    os.makedirs(model_dir, exist_ok=True)
    if best_state is not None:
        torch.save(best_state, os.path.join(model_dir, "model.pth"))
        tokenizer.save_pretrained(model_dir)
        print(f"[CE] Saved best cross-encoder model to {model_dir} (F1={best_f1:.4f})")
    return model_dir, best_f1

# Main trainer orchestrating k-fold training for all three models
def train_all_models(pairs_path: str, output_dir: str = "threads_analysis/models/output", n_splits: int = DEFAULT_FOLDS,
                     epochs: int = DEFAULT_EPOCHS, batch_size: int = DEFAULT_BATCH, lr: float = DEFAULT_LR,
                     accum_steps: int = DEFAULT_ACCUM):
    os.makedirs(output_dir, exist_ok=True)
    rows = load_pairs_jsonl(pairs_path)
    print(f"[INFO] Loaded {len(rows)} pairs from {pairs_path}")

    splits = build_splits(rows, n_splits)
    print(f"[INFO] Built {len(splits)} splits (folds)")

    summary = {"bi_a": [], "bi_b": [], "cross": []}

    # For each fold: train three models
    fold_idx = 0
    for train_idx, val_idx in splits:
        fold_idx += 1
        print(f"\n===== Starting fold {fold_idx}/{len(splits)} =====")
        rows_train = [rows[i] for i in train_idx]
        rows_val = [rows[i] for i in val_idx]

        # 1) Bi-encoder A
        try:
            bi_a_dir, _ = finetune_bi_encoder(BI_ENCODER_A, rows_train, rows_val, output_dir,
                                              fold=fold_idx, epochs=epochs, batch_size=batch_size, lr=lr,
                                              warmup_pct=DEFAULT_WARMUP_PCT, accum_steps=accum_steps)
            # load fine-tuned for embeddings
            bi_a_model = SentenceTransformer(bi_a_dir) if bi_a_dir is not None else SentenceTransformer(BI_ENCODER_A)
            # train MLP classifier on top of its embeddings
            mlp_f1_a = train_mlp_for_fold(rows_train, rows_val, bi_a_model, output_dir, os.path.join(output_dir, f"fold_{fold_idx}"), batch_size=batch_size, epochs=epochs, lr=1e-3, accum_steps=1)
            summary["bi_a"].append({"fold": fold_idx, "mlp_f1": mlp_f1_a, "model_dir": bi_a_dir})
        except Exception as e:
            print(f"[ERROR] bi-encoder A fold {fold_idx} failed: {e}")

        # 2) Bi-encoder B
        try:
            bi_b_dir, _ = finetune_bi_encoder(BI_ENCODER_B, rows_train, rows_val, output_dir,
                                              fold=fold_idx, epochs=epochs, batch_size=batch_size, lr=lr,
                                              warmup_pct=DEFAULT_WARMUP_PCT, accum_steps=accum_steps)
            bi_b_model = SentenceTransformer(bi_b_dir) if bi_b_dir is not None else SentenceTransformer(BI_ENCODER_B)
            mlp_f1_b = train_mlp_for_fold(rows_train, rows_val, bi_b_model, output_dir, os.path.join(output_dir, f"fold_{fold_idx}"), batch_size=batch_size, epochs=epochs, lr=1e-3, accum_steps=1)
            summary["bi_b"].append({"fold": fold_idx, "mlp_f1": mlp_f1_b, "model_dir": bi_b_dir})
        except Exception as e:
            print(f"[ERROR] bi-encoder B fold {fold_idx} failed: {e}")

        # 3) Cross-encoder
        try:
            ce_dir, ce_f1 = finetune_cross_encoder(CROSS_ENCODER, rows_train, rows_val, output_dir,
                                                   fold=fold_idx, epochs=epochs, batch_size=max(8, batch_size//2),
                                                   lr=lr, warmup_pct=DEFAULT_WARMUP_PCT, accum_steps=accum_steps)
            summary["cross"].append({"fold": fold_idx, "cross_f1": ce_f1, "model_dir": ce_dir})
        except Exception as e:
            print(f"[ERROR] cross-encoder fold {fold_idx} failed: {e}")

    # save summary
    with open(os.path.join(output_dir, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("[INFO] Training complete. Summary saved to training_summary.json")

    best_output = os.path.join(output_dir, "best")
    os.makedirs(best_output, exist_ok=True)

    def export_best(summary_key, subdir_name, is_bi_encoder=True):
        entries = summary.get(summary_key, [])
        if not entries:
            print(f"[WARN] No entries for {summary_key}")
            return

        # Get best entry by highest F1
        if is_bi_encoder:
            best = max(entries, key=lambda x: x.get("mlp_f1", -1))
            model_dir = best.get("model_dir")
            mlp_f1 = best.get("mlp_f1")
            print(f"[BEST] {summary_key}: fold={best['fold']} F1={mlp_f1:.4f}")
        else:
            best = max(entries, key=lambda x: x.get("cross_f1", -1))
            model_dir = best.get("model_dir")
            f1 = best.get("cross_f1")
            print(f"[BEST] {summary_key}: fold={best['fold']} F1={f1:.4f}")

        if model_dir is None:
            print(f"[WARN] Model dir not found for {summary_key}")
            return

        dest = os.path.join(best_output, subdir_name)
        os.makedirs(dest, exist_ok=True)

        # Copy whole directory
        import shutil
        shutil.copytree(model_dir, dest, dirs_exist_ok=True)
        print(f"[BEST] Copied best {summary_key} model to {dest}")

    # Export best bi-encoder A
    export_best("bi_a", "bi_encoder_A", is_bi_encoder=True)

    # Export best bi-encoder B
    export_best("bi_b", "bi_encoder_B", is_bi_encoder=True)

    # Export best cross-encoder
    export_best("cross", "cross_encoder", is_bi_encoder=False)

    return summary

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=str, required=True, help='Path to pairs jsonl (output dataset)')
    parser.add_argument('--output-dir', type=str, default='threads_analysis/models/output')
    parser.add_argument('--folds', type=int, default=5)
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=2e-5)
    parser.add_argument('--accum', type=int, default=2)
    args = parser.parse_args()

    train_all_models(args.pairs, output_dir=args.output_dir, n_splits=args.folds,
                     epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, accum_steps=args.accum)
