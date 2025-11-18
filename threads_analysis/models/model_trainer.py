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
import datetime
import os
import json
import math
import random
from typing import List, Dict, Any

import numpy as np
from tqdm import tqdm
from collections import defaultdict

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

# ---------------------------
# FILE: threads_analysis/models/triple_model_trainer.py
# FUNCTION: get_training_params()
# Purpose: centralizar hiperparámetros recomendados para todos los entrenamientos
# ---------------------------
def get_training_params(model_type: str = "default") -> dict:
    """
    Devuelve un diccionario con hiperparámetros recomendados
    model_type: "biencoder", "cross", "mlp", "classical" o "default"
    """
    base = {
        "seed": RANDOM_SEED,
    }

    if model_type == "biencoder":
        base.update({
            "lr": 1e-5,
            "epochs": 2,
            "batch_size": 32,      # intenta 64 si tienes VRAM
            "warmup_pct": 0.10,
            "weight_decay": 0.01,
            "accum_steps": 1,
            "grad_clip": 1.0,
            "dropout_extra": 0.1
        })
    elif model_type == "cross":
        base.update({
            "lr": 8e-6,
            "epochs": 2,
            "batch_size": 16,
            "warmup_pct": 0.20,
            "weight_decay": 0.05,
            "accum_steps": 1,
            "grad_clip": 0.5,
            "label_smoothing": 0.1
        })
    elif model_type == "mlp":
        base.update({
            "lr": 2e-4,
            "epochs": 3,
            "batch_size": 256,
            "weight_decay": 1e-4,
            "dropout": 0.3
        })
    elif model_type == "classical":
        base.update({
            "random_state": RANDOM_SEED,
            "n_jobs": 4
        })
    else:
        # default gentle values
        base.update({
            "lr": DEFAULT_LR,
            "epochs": DEFAULT_EPOCHS,
            "batch_size": DEFAULT_BATCH,
            "warmup_pct": DEFAULT_WARMUP_PCT,
            "accum_steps": DEFAULT_ACCUM
        })

    return base


def sample_by_chat(rows, max_items):
    if len(rows) <= max_items:
        return rows

    # 1. Agrupar por chat
    by_chat = defaultdict(list)
    for r in rows:
        by_chat[r["chat_id"]].append(r)

    chat_ids = list(by_chat.keys())

    # 2. Random shuffle de chats
    random.shuffle(chat_ids)

    # 3. Agregar chats completos hasta el límite
    selected = []
    total = 0
    for cid in chat_ids:
        block = by_chat[cid]
        if total + len(block) > max_items:
            continue
        selected.extend(block)
        total += len(block)
        if total >= max_items:
            break

    return selected


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

# ---------------------------
# FILE: threads_analysis/models/triple_model_trainer.py
# FUNCTION: augment_rows()
# Purpose: augmentación ligera (swap orden, ruido de puntuación, case noise)
# ---------------------------
import re
def augment_rows(rows: List[Dict[str, Any]], p_swap: float = 0.05, p_punct_noise: float = 0.10, p_case_noise: float = 0.05, seed: int = RANDOM_SEED) -> List[Dict[str, Any]]:
    """
    Aplica augmentaciones ligeras a una fracción de rows (devuelve lista nueva).
    - p_swap: con prob p_swap intercambia a<->b en algunos pares para robustez (cambia label a 1->1, 0->0 — mantenemos label)
    - p_punct_noise: añade/remueve puntuación aleatoria
    - p_case_noise: cambia mayúsculas/minúsculas aleatoriamente en algunas palabras
    """
    random.seed(seed)
    out = []
    for r in rows:
        nr = r.copy()
        a_text = nr['a']['text'] or ""
        b_text = nr['b']['text'] or ""
        # swap order sometimes
        if random.random() < p_swap:
            nr = json.loads(json.dumps(nr))  # deep copy
            nr['a']['text'], nr['b']['text'] = b_text, a_text
        # punct noise on a and b (short insertions/removals)
        def punct_noise(s):
            if not s or random.random() >= p_punct_noise:
                return s
            # insert or remove a punctuation at a random position
            pos = random.randint(0, len(s))
            if random.random() < 0.6:
                # insert punctuation
                p = random.choice([",", ".", " ...", "!", "?", ";"])
                return s[:pos] + p + s[pos:]
            else:
                # try to remove punctuation
                return re.sub(r'[,.!?;:]+', '', s, count=1)
        nr['a']['text'] = punct_noise(nr['a']['text'])
        nr['b']['text'] = punct_noise(nr['b']['text'])
        # case noise
        if random.random() < p_case_noise:
            def case_noise(s):
                toks = s.split()
                for i in range(len(toks)):
                    if random.random() < 0.3:
                        if random.random() < 0.5:
                            toks[i] = toks[i].upper()
                        else:
                            toks[i] = toks[i].lower()
                return " ".join(toks)
            nr['a']['text'] = case_noise(nr['a']['text'])
            nr['b']['text'] = case_noise(nr['b']['text'])
        out.append(nr)
    return out

def choose_and_build_splits(
    rows: List[Dict[str, Any]],
    n_splits: int,
    dataset_stats_path: str = "./threads_analysis/models/output/dataset_stats.json",
):
    """
    Decide automáticamente:
    - KFold
    - GroupKFold
    - Custom StratifiedGroupKFold (por perfil de chat)
    """

    # ----------------------------------------------------
    # 1. Cargar dataset_stats.json
    # ----------------------------------------------------
    try:
        with open(dataset_stats_path, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as e:
        print("⚠ No se pudo leer dataset_stats.json:", e)
        print("→ Fallback: KFold simple.")
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
        return list(splitter.split(np.arange(len(rows))))

    chat_stats = stats.get("chats", {})
    groups = np.array([r.get("chat_id", 0) for r in rows])
    y = np.array([int(r.get("label", 0)) for r in rows])

    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)

    # ----------------------------------------------------
    # 2. CASO 1: no hay grupos o solo hay uno
    # ----------------------------------------------------
    if n_groups <= 1:
        print("📌 Usando KFold (solo 1 chat o sin chat_id).")
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
        return list(splitter.split(np.arange(len(rows))))

    # ----------------------------------------------------
    # 3. Detectar heterogeneidad (primero SIEMPRE)
    # ----------------------------------------------------
    pos_ratios = [st["pos_ratio"] for st in chat_stats.values()]
    hard_ratios = [st["hard_ratio"] for st in chat_stats.values()]

    pos_var = np.var(pos_ratios)
    hard_var = np.var(hard_ratios)

    heterogeneous = pos_var > 0.0004 or hard_var > 0.002

    # ----------------------------------------------------
    # 3A. Si es heterogéneo → usar custom fold aunque haya muchos grupos
    # ----------------------------------------------------
    if heterogeneous:
        print("📌 Usando Custom Stratified-Group-KFold (dataset heterogéneo).")

        chat_profiles = []
        chat_ids = []
        for cid, st in chat_stats.items():
            chat_profiles.append([
                st["pos_ratio"],
                st["neg_ratio"],
                st["hard_ratio"],
            ])
            chat_ids.append(int(cid))

        chat_profiles = np.array(chat_profiles)
        chat_ids = np.array(chat_ids)

        from sklearn.cluster import KMeans
        kmeans = KMeans(
            n_clusters=n_splits,
            random_state=RANDOM_SEED,
            n_init="auto"
        )
        cluster_labels = kmeans.fit_predict(chat_profiles)

        chat_to_fold = {cid: cluster_labels[i] for i, cid in enumerate(chat_ids)}

        indices = np.arange(len(rows))
        fold_indices = {i: {"val": []} for i in range(n_splits)}

        for idx, cid in zip(indices, groups):
            fold_idx = chat_to_fold[int(cid)]
            fold_indices[fold_idx]["val"].append(idx)

        splits = []
        for f in range(n_splits):
            val_ids = set(fold_indices[f]["val"])
            train_ids = [i for i in indices if i not in val_ids]
            splits.append((train_ids, list(val_ids)))

        return splits

    # ----------------------------------------------------
    # 4. Si NO es heterogéneo → decidir tipo de GroupKFold
    # ----------------------------------------------------
    if n_groups >= n_splits * 3:
        print("📌 Usando GroupKFold (muchos chats, ratios similares).")
    else:
        print("📌 Usando GroupKFold (pocos chats pero ratios similares).")

    splitter = GroupKFold(n_splits=n_splits)
    return list(splitter.split(np.arange(len(rows)), y, groups))


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

def train_mlp_for_fold(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], emb_model: SentenceTransformer,
                       output_dir: str, fold_dir: str, batch_size: int, epochs: int, lr: float, accum_steps: int):
    print("[MLP] Building embeddings with GPU + batch encode...")

    # Directorio para guardar progreso
    mlp_dir = os.path.join(fold_dir, "mlp_on_" + emb_model.__class__.__module__.split(".")[0])
    os.makedirs(mlp_dir, exist_ok=True)
    
    # Archivo para guardar progreso
    progress_file = os.path.join(mlp_dir, "training_progress.json")
    progress_data = {
        "model": "MLP",
        "fold_dir": fold_dir,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "training_history": [],
        "start_time": datetime.now().isoformat()
    }

    # --------- GPU batch encoding helper ----------
    def batch_encode_texts(texts, batch=64):
        all_embs = []
        for i in tqdm(range(0, len(texts), batch), desc="[ENCODE GPU]"):
            batch_texts = texts[i:i+batch]
            embs = emb_model.encode(
                batch_texts,
                device=DEVICE,                 # ✅ GPU
                batch_size=batch,              # ✅ batch
                convert_to_numpy=True,
                show_progress_bar=False
            )
            all_embs.extend(embs)
        return all_embs

    # Prepare texts
    train_a = [r['a']['text'] or "" for r in rows_train]
    train_b = [r['b']['text'] or "" for r in rows_train]
    val_a   = [r['a']['text'] or "" for r in rows_val]
    val_b   = [r['b']['text'] or "" for r in rows_val]

    # --------- GPU ENCODING WITH PROGRESS ----------
    emb_train_a = batch_encode_texts(train_a)
    emb_train_b = batch_encode_texts(train_b)
    emb_val_a   = batch_encode_texts(val_a)
    emb_val_b   = batch_encode_texts(val_b)

    # Attach features back
    for i, r in enumerate(rows_train):
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(
            emb_train_a[i], emb_train_b[i], extras
        )

    for i, r in enumerate(rows_val):
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(
            emb_val_a[i], emb_val_b[i], extras
        )

    # Obtener params recomendados para MLP
    mlp_params = get_training_params("mlp")
    input_dim = rows_train[0]['mlp_features'].shape[0]
    # construir MLP más pequeño y con dropout del config
    mlp = SmallMLP(input_dim, hidden=256, hidden2=64, dropout=mlp_params.get("dropout", 0.3)).to(DEVICE)
    opt = torch.optim.AdamW(mlp.parameters(), lr=mlp_params.get("lr", lr), weight_decay=mlp_params.get("weight_decay", 1e-4))
    loss_fn = nn.BCELoss()

    train_ds = EmbeddingPairsDataset(rows_train)
    val_ds   = EmbeddingPairsDataset(rows_val)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    best_f1 = -1
    best_state = None

    for epoch in range(1, epochs + 1):
        mlp.train()
        total_loss = 0

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

        # Validation
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

        # GUARDAR PROGRESO DESPUÉS DE CADA EPOCH
        epoch_data = {
            "epoch": epoch,
            "loss": float(avg_loss),
            "precision": float(p),
            "recall": float(r),
            "f1": float(f),
            "timestamp": datetime.now().isoformat()
        }
        progress_data["training_history"].append(epoch_data)
        
        # Guardar archivo de progreso inmediatamente
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        print(f"[MLP] Epoch {epoch}: loss={avg_loss:.4f} P={p:.4f} R={r:.4f} F1={f:.4f} - Progreso guardado")

        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k, v in mlp.state_dict().items()}

    # Save best
    if best_state is not None:
        model_path = os.path.join(mlp_dir, "mlp_model.pth")
        torch.save(best_state, model_path)
        
        # Actualizar progreso con resultado final
        progress_data["final_f1"] = float(best_f1)
        progress_data["end_time"] = datetime.now().isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[MLP] Saved best mlp to {model_path} (F1={best_f1:.4f}) - Progreso final guardado")

    return best_f1

# Fine-tune a bi-encoder using sentence-transformers - MODIFICADA PARA GUARDAR PROGRESO
def finetune_bi_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]],
                        output_dir: str, fold: int, epochs: int = 3, batch_size: int = 32, lr: float = 2e-5,
                        warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[BI] Fine-tuning bi-encoder {model_name} (tag={model_tag}) fold={fold}")

    # Directorio para guardar progreso
    model_save_path = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_save_path, exist_ok=True)
    
    # Archivo para guardar progreso
    progress_file = os.path.join(model_save_path, "training_progress.json")
    progress_data = {
        "model": model_name,
        "fold": fold,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "training_history": [],
        "start_time": datetime.now().isoformat()
    }

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
    
    # Callback personalizado para guardar progreso
    class ProgressCallback:
        def __init__(self, progress_file, progress_data):
            self.progress_file = progress_file
            self.progress_data = progress_data
            
        def __call__(self, score, epoch, steps):
            # Guardar progreso después de cada evaluación
            epoch_data = {
                "epoch": epoch,
                "steps": steps,
                "score": float(score),
                "timestamp": datetime.now().isoformat()
            }
            self.progress_data["training_history"].append(epoch_data)
            
            # Guardar archivo inmediatamente
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
            
            print(f"[Bi-Encoder] Epoch {epoch} - Score: {score:.4f} - Progreso guardado")
    
    progress_callback = ProgressCallback(progress_file, progress_data)
    
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        evaluator=evaluator,
        epochs=epochs,
        evaluation_steps=max(1, len(train_dataloader)),
        output_path=model_save_path,
        warmup_steps=warmup_steps,
        optimizer_params={'lr': lr},
        use_amp=torch.cuda.is_available(),
        callback=progress_callback  # Añadir callback de progreso
    )

    # Obtener score final y actualizar progreso
    final_score = evaluator(model)
    progress_data["final_score"] = float(final_score)
    progress_data["end_time"] = datetime.now().isoformat()
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

    print(f"[BI] Saved bi-encoder at {model_save_path} - Progreso final guardado")
    return model_save_path, final_score

# Cross-encoder fine-tuning 
def finetune_cross_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], 
                           output_dir: str, fold: int, epochs: int = 3, batch_size: int = 16, lr: float = 2e-5,
                           warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[CE] Fine-tuning cross-encoder {model_name} fold={fold}")

    # Directorio para guardar progreso
    model_dir = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_dir, exist_ok=True)
    
    # Archivo para guardar progreso
    progress_file = os.path.join(model_dir, "training_progress.json")
    progress_data = {
        "model": model_name,
        "fold": fold,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "training_history": [],
        "start_time": datetime.now().isoformat()
    }
    
    # Use huggingface_hub to attempt a visible download progress if available
    use_hf_hub = False
    try:
        from huggingface_hub import hf_hub_download
        from tqdm import tqdm
        use_hf_hub = True
    except Exception:
        use_hf_hub = False

    model_dir_local = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_dir_local, exist_ok=True)

    # If model/tokenizer not present locally, try to download with progress
    needs_download = not (os.path.exists(os.path.join(model_dir_local, "config.json")) or os.path.exists(os.path.join(model_dir_local, "pytorch_model.bin")))
    if needs_download and use_hf_hub:
        print(f"[CE] Descargando pesos/tokenizer de '{model_name}' con progreso (hf_hub)...")
        # Try to download the main files to show progress (best-effort)
        files_to_try = ["pytorch_model.bin", "tf_model.h5", "flax_model.msgpack", "config.json", "tokenizer.json"]
        for fname in files_to_try:
            try:
                # hf_hub_download will stream and show progress internally if network conditions allow
                hf_hub_download(repo_id=model_name, filename=fname, cache_dir=model_dir_local, force_download=False)
            except Exception:
                # ignore missing files
                pass
        print("[CE] Descarga hf_hub tentativa completada. Ahora from_pretrained() puede cargar desde cache.")

    # If hf_hub not available, print a spinner message while Transformers handles download
    if needs_download and not use_hf_hub:
        print(f"[CE] Modelo/tokenizer no encontrado localmente. Llamando a transformers.from_pretrained() (esto descargará archivos).")
        print("[CE] Descarga en progreso... (puede tardar).")

    # Load tokenizer + model (transformers will use the local cache if available)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1).to(DEVICE)

    # prepare dataset 
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

    # optimizer + scheduler with weight decay
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {'params': [p for n,p in model.named_parameters() if not any(nd in n for nd in no_decay)], 'weight_decay': 0.01},
        {'params': [p for n,p in model.named_parameters() if any(nd in n for nd in no_decay)], 'weight_decay': 0.0}
    ]
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=lr)
    total_steps = max(1, (len(train_loader) // max(1, accum_steps)) * epochs)
    warmup_steps = max(1, int(total_steps * warmup_pct))
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    from torch import amp as torch_amp
    device_type = "cuda" if torch.cuda.is_available() else "cpu"
    scaler = torch_amp.GradScaler(device_type, enabled=(device_type == "cuda"))
    loss_fn = nn.BCEWithLogitsLoss()

    best_f1 = -1.0
    best_state = None
    clip_value = get_training_params("cross").get("grad_clip", 0.5)

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
            # gradient clipping before step
            if clip_value is not None:
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip_value)
            if step % accum_steps == 0:
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            total_loss += (loss.item() * accum_steps)

        avg_loss = total_loss / max(1, len(train_loader))

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
        
        # GUARDAR PROGRESO DESPUÉS DE CADA EPOCH
        epoch_data = {
            "epoch": epoch,
            "loss": float(avg_loss),
            "auc": float(auc),
            "precision": float(p),
            "recall": float(r),
            "f1": float(f),
            "timestamp": datetime.now().isoformat()
        }
        progress_data["training_history"].append(epoch_data)
        
        # Guardar archivo de progreso inmediatamente
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        print(f"[CE] Epoch {epoch}: loss={avg_loss:.4f} val_AUC={auc:.4f} P={p:.4f} R={r:.4f} F1={f:.4f} - Progreso guardado")
        
        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k,v in model.state_dict().items()}

    # save best
    if best_state is not None:
        torch.save(best_state, os.path.join(model_dir, "model.pth"))
        tokenizer.save_pretrained(model_dir)
        
        # Actualizar progreso con resultado final
        progress_data["final_f1"] = float(best_f1)
        progress_data["end_time"] = datetime.now().isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CE] Saved best cross-encoder model to {model_dir} (F1={best_f1:.4f}) - Progreso final guardado")
    return model_dir, best_f1

# Modelos clásicos
def train_classical_models(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], fold_dir: str):
    """
    Entrena y guarda modelos clásicos. Guarda progreso inmediatamente después de cada modelo.
    """
    try:
        import joblib
        from sklearn.naive_bayes import GaussianNB
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
    except Exception as e:
        print(f"[CLASSICAL] Faltan dependencias sklearn/joblib: {e}")
        return {}

    # LightGBM optional (best-effort)
    try:
        import lightgbm as lgb
        has_lgb = True
    except Exception:
        has_lgb = False

    # Build X,y
    X_train = [r['mlp_features'].astype(float) if isinstance(r['mlp_features'], np.ndarray) else np.array(r['mlp_features'], dtype=float) for r in rows_train]
    y_train = [int(r.get('label', 0)) for r in rows_train]
    X_val = [r['mlp_features'].astype(float) if isinstance(r['mlp_features'], np.ndarray) else np.array(r['mlp_features'], dtype=float) for r in rows_val]
    y_val = [int(r.get('label', 0)) for r in rows_val]

    X_train = np.vstack(X_train)
    X_val = np.vstack(X_val)
    y_train = np.array(y_train)
    y_val = np.array(y_val)

    results = {}
    os.makedirs(fold_dir, exist_ok=True)
    
    # Archivo para guardar progreso
    progress_file = os.path.join(fold_dir, "classical_training_progress.json")
    progress_data = {
        "models_trained": [],
        "start_time": datetime.now().isoformat()
    }

    # 1) GaussianNB
    try:
        nb = GaussianNB()
        nb.fit(X_train, y_train)
        preds = nb.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['gaussian_nb'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(nb, os.path.join(fold_dir, "gaussian_nb.joblib"))
        
        # GUARDAR PROGRESO INMEDIATAMENTE
        model_data = {
            "model": "GaussianNB",
            "f1": float(f),
            "precision": float(p),
            "recall": float(r),
            "timestamp": datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CLASSICAL] GaussianNB F1={f:.4f} - Progreso guardado")
    except Exception as e:
        print(f"[CLASSICAL] GaussianNB failed: {e}")

    # 2) LogisticRegression (with l2 + saga for speed)
    try:
        lr = LogisticRegression(max_iter=1000, solver='saga', penalty='l2', n_jobs=1, random_state=RANDOM_SEED)
        lr.fit(X_train, y_train)
        preds = lr.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['logistic_regression'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(lr, os.path.join(fold_dir, "logistic_regression.joblib"))
        
        # GUARDAR PROGRESO INMEDIATAMENTE
        model_data = {
            "model": "LogisticRegression",
            "f1": float(f),
            "precision": float(p),
            "recall": float(r),
            "timestamp": datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CLASSICAL] LogisticRegression F1={f:.4f} - Progreso guardado")
    except Exception as e:
        print(f"[CLASSICAL] LogisticRegression failed: {e}")

    # 3) LightGBM
    if has_lgb:
        try:
            lgb_clf = lgb.LGBMClassifier(n_estimators=200, num_leaves=31, n_jobs=2, random_state=RANDOM_SEED)
            lgb_clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20, verbose=False)
            preds = lgb_clf.predict(X_val)
            p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
            results['lightgbm'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
            joblib.dump(lgb_clf, os.path.join(fold_dir, "lightgbm.joblib"))
            
            # GUARDAR PROGRESO INMEDIATAMENTE
            model_data = {
                "model": "LightGBM",
                "f1": float(f),
                "precision": float(p),
                "recall": float(r),
                "timestamp": datetime.now().isoformat()
            }
            progress_data["models_trained"].append(model_data)
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
            print(f"[CLASSICAL] LightGBM F1={f:.4f} - Progreso guardado")
        except Exception as e:
            print(f"[CLASSICAL] LightGBM failed: {e}")
    else:
        print("[CLASSICAL] LightGBM no instalado, saltando.")

    # 4) RandomForest (small forest to keep size reasonable)
    try:
        rf = RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=2, random_state=RANDOM_SEED)
        rf.fit(X_train, y_train)
        preds = rf.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['random_forest'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(rf, os.path.join(fold_dir, "random_forest.joblib"))
        
        # GUARDAR PROGRESO INMEDIATAMENTE
        model_data = {
            "model": "RandomForest",
            "f1": float(f),
            "precision": float(p),
            "recall": float(r),
            "timestamp": datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        progress_data["end_time"] = datetime.now().isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CLASSICAL] RandomForest F1={f:.4f} - Progreso final guardado")
    except Exception as e:
        print(f"[CLASSICAL] RandomForest failed: {e}")

    return results

def train_all_models(pairs_path: str, output_dir: str = "threads_analysis/models/output", n_splits: int = DEFAULT_FOLDS,
                     epochs: int = DEFAULT_EPOCHS, batch_size: int = DEFAULT_BATCH, lr: float = DEFAULT_LR,
                     accum_steps: int = DEFAULT_ACCUM):
    os.makedirs(output_dir, exist_ok=True)
    rows = load_pairs_jsonl(pairs_path)
    print(f"[INFO] Loaded {len(rows)} pairs from {pairs_path}")

    # Construir Evaluation Set basado en chats completos
    from collections import defaultdict
    chat_to_rows = defaultdict(list)

    for r in rows:
        cid = r.get("chat_id", 0)
        chat_to_rows[cid].append(r)

    all_chats = list(chat_to_rows.keys())
    rng = np.random.default_rng(RANDOM_SEED)
    rng.shuffle(all_chats)

    total = len(rows)
    target_eval = int(total * 0.10)

    eval_chats = []
    eval_count = 0

    for cid in all_chats:
        if eval_count >= target_eval:
            break
        eval_chats.append(cid)
        eval_count += len(chat_to_rows[cid])

    rows_eval = []
    rows_trainval = []

    for cid, msgs in chat_to_rows.items():
        if cid in eval_chats:
            rows_eval.extend(msgs)
        else:
            rows_trainval.extend(msgs)

    print(f"[INFO] Evaluation set size (by chat): {len(rows_eval)}")
    print(f"[INFO] Train+Val size: {len(rows_trainval)}")

    # Guardar evaluation set para evaluation.py
    eval_path = os.path.join(output_dir, "evaluation_set.jsonl")
    with open(eval_path, "w", encoding="utf-8") as f:
        for r in rows_eval:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[INFO] Saved evaluation set → {eval_path}")

    # A partir de aquí LOS FOLDS se construyen SOLO con rows_trainval
    rows = rows_trainval

    splits = choose_and_build_splits(rows, n_splits)
    print(f"[INFO] Built {len(splits)} splits (folds)")

    summary = {"bi_a": [], "bi_b": [], "cross": []}

    fold_idx = 0
    for train_idx, val_idx in splits:
        fold_idx += 1
        print(f"\n===== Starting fold {fold_idx}/{len(splits)} =====")

        # 📌 Resumen INDIVIDUAL por fold
        fold_summary = {
            "fold": fold_idx,
            "bi_a": {},
            "bi_b": {},
            "cross": {}
        }

        rows_train = [rows[i] for i in train_idx]
        rows_train = augment_rows(rows_train, p_swap=0.05, p_punct_noise=0.10, p_case_noise=0.05, seed=RANDOM_SEED + fold_idx)
        rows_val = [rows[i] for i in val_idx]

        MAX_TRAIN = 500_000
        MAX_VAL = 200_000

        rows_train = sample_by_chat(rows_train, MAX_TRAIN)
        rows_val   = sample_by_chat(rows_val, MAX_VAL)

        force_retrain = True

        # =============================================
        # ✅ 1) Bi-encoder A 
        # =============================================
        params = get_training_params()
        epochs = params["epochs"]
        batch_size = params["batch_size"]
        lr = params["lr"]
        accum_steps = params["accum_steps"]

        bi_a_tag = BI_ENCODER_A.split("/")[-1]
        bi_a_out = os.path.join(output_dir, f"fold_{fold_idx}", bi_a_tag)

        if not force_retrain and os.path.exists(bi_a_out):
            print(f"[SKIP] Bi-encoder A ya existe → {bi_a_out}")
            bi_a_model = SentenceTransformer(bi_a_out)
        else:
            try:
                bi_a_dir, _ = finetune_bi_encoder(
                    BI_ENCODER_A, rows_train, rows_val, output_dir,
                    fold=fold_idx,
                    epochs=epochs,
                    batch_size=batch_size,
                    lr=lr,
                    warmup_pct=DEFAULT_WARMUP_PCT,
                    accum_steps=accum_steps
                )
                bi_a_model = SentenceTransformer(bi_a_dir)
            except Exception as e:
                print(f"[ERROR] bi-encoder A fold {fold_idx} failed: {e}")
                bi_a_model = SentenceTransformer(BI_ENCODER_A)

        mlp_f1_a = train_mlp_for_fold(
            rows_train, rows_val, bi_a_model,
            output_dir, os.path.join(output_dir, f"fold_{fold_idx}"),
            batch_size=batch_size,
            epochs=epochs,
            lr=1e-3,
            accum_steps=1
        )

        fold_summary["bi_a"] = {
            "mlp_f1": mlp_f1_a,
            "model_dir": bi_a_out
        }

        summary["bi_a"].append({
            "fold": fold_idx,
            "mlp_f1": mlp_f1_a,
            "model_dir": bi_a_out
        })

        # CORRECCIÓN: Llamada corregida a train_classical_models
        classical_a_dir = os.path.join(output_dir, f"fold_{fold_idx}", "classical_a")
        train_classical_models(rows_train, rows_val, classical_a_dir)

        # =============================================
        # ✅ 2) Bi-encoder B
        # =============================================
        params = get_training_params()
        epochs = params["epochs"]
        batch_size = params["batch_size"]
        lr = params["lr"]
        accum_steps = params["accum_steps"]

        bi_b_tag = BI_ENCODER_B.split("/")[-1]
        bi_b_out = os.path.join(output_dir, f"fold_{fold_idx}", bi_b_tag)

        if not force_retrain and os.path.exists(bi_b_out):
            print(f"[SKIP] Bi-encoder B ya existe → {bi_b_out}")
            bi_b_model = SentenceTransformer(bi_b_out)
        else:
            try:
                bi_b_dir, _ = finetune_bi_encoder(
                    BI_ENCODER_B, rows_train, rows_val, output_dir,
                    fold=fold_idx,
                    epochs=epochs,
                    batch_size=batch_size,
                    lr=lr,
                    warmup_pct=DEFAULT_WARMUP_PCT,
                    accum_steps=accum_steps
                )
                bi_b_model = SentenceTransformer(bi_b_dir)
            except Exception as e:
                print(f"[ERROR] bi-encoder B fold {fold_idx} failed: {e}")
                bi_b_model = SentenceTransformer(BI_ENCODER_B)

        mlp_f1_b = train_mlp_for_fold(
            rows_train, rows_val, bi_b_model,
            output_dir, os.path.join(output_dir, f"fold_{fold_idx}"),
            batch_size=batch_size,
            epochs=epochs,
            lr=1e-3,
            accum_steps=1
        )

        fold_summary["bi_b"] = {
            "mlp_f1": mlp_f1_b,
            "model_dir": bi_b_out
        }

        summary["bi_b"].append({
            "fold": fold_idx,
            "mlp_f1": mlp_f1_b,
            "model_dir": bi_b_out
        })

        # CORRECCIÓN: Llamada corregida a train_classical_models
        classical_b_dir = os.path.join(output_dir, f"fold_{fold_idx}", "classical_b")
        train_classical_models(rows_train, rows_val, classical_b_dir)

        # =============================================
        # ✅ 3) Cross-encoder
        # =============================================
        ce_tag = CROSS_ENCODER.split("/")[-1]
        ce_out = os.path.join(output_dir, f"fold_{fold_idx}", ce_tag)

        if not force_retrain and os.path.exists(ce_out):
            print(f"[SKIP] Cross-encoder ya existe → {ce_out}")
            ce_f1 = None
        else:
            try:
                cross_params = get_training_params("cross")
                ce_dir, ce_f1 = finetune_cross_encoder(
                    CROSS_ENCODER, rows_train, rows_val, output_dir,
                    fold=fold_idx,
                    epochs=cross_params.get("epochs", epochs),
                    batch_size=cross_params.get("batch_size", max(8, batch_size//2)),
                    lr=cross_params.get("lr", lr),
                    warmup_pct=cross_params.get("warmup_pct", DEFAULT_WARMUP_PCT),
                    accum_steps=cross_params.get("accum_steps", accum_steps)
                )
            except Exception as e:
                print(f"[ERROR] cross-encoder fold {fold_idx} failed: {e}")
                ce_f1 = None

        fold_summary["cross"] = {
            "cross_f1": ce_f1,
            "model_dir": ce_out
        }

        summary["cross"].append({
            "fold": fold_idx,
            "cross_f1": ce_f1,
            "model_dir": ce_out
        })

        # =====================================================
        # 📌 GUARDAR RESUMEN DEL FOLD (INDIVIDUAL)
        # =====================================================
        fold_summary_path = os.path.join(output_dir, f"fold_{fold_idx}", f"training_summary_fold_{fold_idx}.json")
        with open(fold_summary_path, "w", encoding="utf-8") as f:
            json.dump(fold_summary, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Saved fold summary → {fold_summary_path}")

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
