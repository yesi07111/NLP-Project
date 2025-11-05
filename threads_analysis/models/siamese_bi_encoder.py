"""
threads_analysis/models/siamese_bi_encoder.py

Entrenamiento del modelo Siamese / Bi-encoder (SBERT) + MLP con K-Fold (GroupKFold por chat).
- Ajusta n_splits si hay menos grupos.
- Si hay 1 grupo, usa KFold (estratificado si es posible).
- Guarda cada fold en output_dir/fold_{i}/model.pth y metrics.json (contiene f1, auc, precision, recall).
- Elige el mejor fold según F1.
"""
from __future__ import annotations
import os
import json
import math
import random
from typing import List, Dict, Any
from glob import glob

import numpy as np
from tqdm import tqdm

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import GroupKFold, KFold, StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

from sentence_transformers import SentenceTransformer

# ---------------- CONFIG ----------------
EMBEDDING_MODEL = os.getenv('SBERT_MODEL', 'all-MiniLM-L6-v2')
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ---------------- Utilities ----------------
class EmbeddingCache:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)
        self.cache: Dict[str, np.ndarray] = {}

    def get(self, text: str) -> np.ndarray:
        key = text if text is not None else ''
        if key in self.cache:
            return self.cache[key]
        emb = self.model.encode(key, convert_to_numpy=True)
        self.cache[key] = emb
        return emb

    def bulk_encode(self, texts: List[str], show_progress: bool = True) -> List[np.ndarray]:
        # encode many texts in batch (fills cache)
        uncached = [t for t in texts if t not in self.cache]
        if uncached:
            embeddings = self.model.encode(uncached, convert_to_numpy=True, show_progress_bar=show_progress)
            for t, e in zip(uncached, embeddings):
                self.cache[t] = e
        return [self.cache[t] for t in texts]


# ---------------- Dataset & Model ----------------
class ReplyPairsDataset(Dataset):
    def __init__(self, rows: List[Dict[str, Any]]):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        r = self.rows[idx]
        features = r['features']
        label = np.float32(r['label'])
        return torch.from_numpy(features), torch.tensor(label, dtype=torch.float32)


class SimpleMLP(nn.Module):
    def __init__(self, input_dim: int, hidden1: int = 512, hidden2: int = 128, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden2, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


# ---------------- Feature helper ----------------
def make_features(emb_a: np.ndarray, emb_b: np.ndarray, time_delta_min: float, same_author: int) -> np.ndarray:
    time_feat = np.array([math.log1p(time_delta_min)], dtype=np.float32)
    same_feat = np.array([float(same_author)], dtype=np.float32)

    a = emb_a.astype(np.float32)
    b = emb_b.astype(np.float32)
    feat = np.concatenate([a, b, np.abs(a - b), a * b, time_feat, same_feat]).astype(np.float32)
    return feat


# ---------------- Training with Group K-Fold ----------------
def train_kfold(pairs_path: str, emb_model_name: str = EMBEDDING_MODEL, output_dir: str = 'models/output', n_splits: int = 5,
                epochs: int = 4, batch_size: int = 64, lr: float = 1e-3):
    os.makedirs(output_dir, exist_ok=True)

    # load pairs (jsonl with fields: a.text, b.text, label, time_delta_min, same_author, chat_id)
    rows = []
    texts = set()
    groups = []
    labels = []
    with open(pairs_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            rows.append(obj)
            texts.add(obj['a']['text'])
            texts.add(obj['b']['text'])
            groups.append(obj.get('chat_id', 0))
            labels.append(int(obj.get('label', 0)))

    if len(rows) == 0:
        raise ValueError("No pairs found in pairs_path")

    texts = list(texts)
    emb_cache = EmbeddingCache(emb_model_name)
    print(f"[INFO] Encoding {len(texts)} unique texts (may be cached)...")
    emb_cache.bulk_encode(texts)

    # attach embeddings and features to rows
    for r in tqdm(rows, desc="Building features"):
        emb_a = emb_cache.get(r['a']['text'])
        emb_b = emb_cache.get(r['b']['text'])
        feat = make_features(emb_a, emb_b, float(r.get('time_delta_min', 99999.0)), int(r.get('same_author', 0)))
        # store as numpy array for fast conversion later
        r['features'] = np.array(feat, dtype=np.float32)
        r['label'] = int(r.get('label', 0))

    # prepare arrays for splitting
    X_idx = np.arange(len(rows))
    y = np.array([r['label'] for r in rows])
    groups_arr = np.array(groups)
    unique_groups = np.unique(groups_arr)
    n_groups = len(unique_groups)

    # adjust n_splits if necessary
    if n_groups < 2:
        # fallback: use KFold or StratifiedKFold if labels vary
        print(f"[WARN] Only {n_groups} group(s) found. Falling back to KFold (no group-wise split).")
        if len(np.unique(y)) > 1:
            # stratify if possible
            splitter = StratifiedKFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=RANDOM_SEED)
            splits = splitter.split(X_idx, y)
        else:
            splitter = KFold(n_splits=min(n_splits, len(y)), shuffle=True, random_state=RANDOM_SEED)
            splits = splitter.split(X_idx)
    else:
        if n_groups < n_splits:
            print(f"[WARN] Requested n_splits={n_splits} but only {n_groups} groups available. Using n_splits={n_groups}.")
            n_splits = n_groups
        gkf = GroupKFold(n_splits=n_splits)
        splits = gkf.split(X_idx, y, groups_arr)

    # Training loop across splits
    fold = 0
    metrics = []
    input_dim = rows[0]['features'].shape[0]

    for train_idx, val_idx in splits:
        fold += 1
        print(f"\n--- Fold {fold} ---")
        train_rows = [rows[i] for i in train_idx]
        val_rows = [rows[i] for i in val_idx]

        # convert to simple dicts for dataset
        train_ds_rows = [{'features': r['features'], 'label': r['label']} for r in train_rows]
        val_ds_rows = [{'features': r['features'], 'label': r['label']} for r in val_rows]

        train_ds = ReplyPairsDataset(train_ds_rows)
        val_ds = ReplyPairsDataset(val_ds_rows)

        model = SimpleMLP(input_dim).to(DEVICE)
        opt = torch.optim.Adam(model.parameters(), lr=lr)
        loss_fn = nn.BCELoss()

        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

        best_f1 = -1.0
        best_state = None
        best_metrics = None

        for epoch in range(1, epochs + 1):
            model.train()
            total_loss = 0.0
            for Xb, yb in train_loader:
                Xb = Xb.to(DEVICE)
                yb = yb.to(DEVICE)
                opt.zero_grad()
                preds = model(Xb)
                loss = loss_fn(preds, yb)
                loss.backward()
                opt.step()
                total_loss += loss.item() * Xb.size(0)

            avg_loss = total_loss / len(train_ds)

            # validation
            model.eval()
            ys, yps = [], []
            with torch.no_grad():
                for Xv, yv in val_loader:
                    Xv = Xv.to(DEVICE)
                    pv = model(Xv).detach().cpu().numpy()
                    ys.extend(yv.numpy().tolist())
                    yps.extend(pv.tolist())

            # compute metrics
            try:
                auc = roc_auc_score(ys, yps) if len(np.unique(ys)) > 1 else 0.0
            except Exception:
                auc = 0.0

            preds_bin = [1 if p >= 0.5 else 0 for p in yps]
            p, r, f, _ = precision_recall_fscore_support(ys, preds_bin, average='binary', zero_division=0)
            print(f"Epoch {epoch}: loss={avg_loss:.4f} val_auc={auc:.4f} P={p:.4f} R={r:.4f} F1={f:.4f}")

            # choose best by F1
            if f > best_f1:
                best_f1 = f
                best_state = {k: v.cpu() for k, v in model.state_dict().items()}
                best_metrics = {'epoch': epoch, 'auc': float(auc), 'precision': float(p), 'recall': float(r), 'f1': float(f)}

        # save fold artifacts into directory fold_{fold}
        fold_dir = os.path.join(output_dir, f'fold_{fold}')
        os.makedirs(fold_dir, exist_ok=True)
        if best_state is not None:
            model_path = os.path.join(fold_dir, 'model.pth')
            torch.save(best_state, model_path)
            metrics_path = os.path.join(fold_dir, 'metrics.json')
            with open(metrics_path, 'w', encoding='utf-8') as mf:
                json.dump(best_metrics or {}, mf, ensure_ascii=False, indent=2)
            print(f"Saved fold {fold} model to {model_path} with metrics {best_metrics}")

        metrics.append({'fold': fold, **(best_metrics or {})})

    print('\nKFold finished. Summary metrics per fold:')
    print(json.dumps(metrics, indent=2))
    return metrics


# ---------------- Prediction helper ----------------
def load_mlp_from_path(path: str, input_dim: int) -> SimpleMLP:
    model = SimpleMLP(input_dim).to(DEVICE)
    state = torch.load(path, map_location=DEVICE)
    model.load_state_dict(state)
    model.eval()
    return model


def predict_pair_mlp(model: SimpleMLP, emb_cache: EmbeddingCache, text_a: str, text_b: str, time_delta_min: float, same_author: int) -> float:
    emb_a = emb_cache.get(text_a)
    emb_b = emb_cache.get(text_b)
    feat = make_features(emb_a, emb_b, time_delta_min, same_author)
    X = torch.from_numpy(feat).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        return float(model(X).cpu().numpy().squeeze())


# CLI
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=str, default='threads_analysis/models/output/pairs_with_hard_neg.jsonl')
    parser.add_argument('--output-dir', type=str, default='threads_analysis/models/output')
    parser.add_argument('--epochs', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--folds', type=int, default=5)
    args = parser.parse_args()

    train_kfold(args.pairs, output_dir=args.output_dir, epochs=args.epochs, batch_size=args.batch_size, n_splits=args.folds)
