"""
threads_analysis/models/triple_model_trainer.py

Entrena (fine-tune completo) tres modelos:
 - Bi-encoder A: paraphrase-multilingual-mpnet-base-v2
 - Bi-encoder B: sentence-transformers/all-MiniLM-L12-v2
 - Cross-encoder: cross-encoder/ms-marco-MiniLM-L-12-v2

ADICION: Entrena primero modelos One-Class SVM e Isolation Tree solo con positivos

Procedimiento:
 - Carga pairs JSONL (output de dataset_builder.py)
 - Construye folds (GroupKFold si hay >1 chat, otherwise Stratified/KFold)
 - Para cada fold, entrena primero One-Class SVM e Isolation Tree solo con positivos del train
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
# Agregar imports para modelos de anomalía
from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest
import joblib

from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.cross_encoder import CrossEncoder

from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_linear_schedule_with_warmup

BI_ENCODER_A = "paraphrase-multilingual-mpnet-base-v2"
BI_ENCODER_B = "sentence-transformers/all-MiniLM-L12-v2"
CROSS_ENCODER = "cross-encoder/ms-marco-MiniLM-L-12-v2"

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)

DEFAULT_EPOCHS = 3
DEFAULT_BATCH = 32
DEFAULT_LR = 2e-5
DEFAULT_ACCUM = 2
DEFAULT_WARMUP_PCT = 0.06
DEFAULT_FOLDS = 5

def get_training_params(model_type: str = "default") -> dict:
    """Devuelve hiperparámetros recomendados para biencoder, cross, mlp, classical o default"""
    base = {"seed": RANDOM_SEED}

    if model_type == "biencoder":
        base.update({
            "lr": 1e-5, "epochs": 2, "batch_size": 32, "warmup_pct": 0.10,
            "weight_decay": 0.01, "accum_steps": 1, "grad_clip": 1.0, "dropout_extra": 0.1
        })
    elif model_type == "cross":
        base.update({
            "lr": 8e-6, "epochs": 2, "batch_size": 16, "warmup_pct": 0.20,
            "weight_decay": 0.05, "accum_steps": 1, "grad_clip": 0.5, "label_smoothing": 0.1
        })
    elif model_type == "mlp":
        base.update({
            "lr": 2e-4, "epochs": 3, "batch_size": 256, "weight_decay": 1e-4, "dropout": 0.3
        })
    elif model_type == "classical":
        base.update({"random_state": RANDOM_SEED, "n_jobs": 4})
    elif model_type == "anomaly":
        base.update({
            "oc_svm_nu": 0.1,
            "oc_svm_kernel": "rbf",
            "oc_svm_gamma": "scale",
            "isolation_forest_contamination": 0.1,
            "isolation_forest_n_estimators": 100
        })
    else:
        base.update({
            "lr": DEFAULT_LR, "epochs": DEFAULT_EPOCHS, "batch_size": DEFAULT_BATCH,
            "warmup_pct": DEFAULT_WARMUP_PCT, "accum_steps": DEFAULT_ACCUM
        })
    return base

def sample_by_chat(rows, max_items):
    if len(rows) <= max_items:
        return rows
    by_chat = defaultdict(list)
    for r in rows:
        by_chat[r["chat_id"]].append(r)
    chat_ids = list(by_chat.keys())
    random.shuffle(chat_ids)
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

class SmallMLP(nn.Module):
    def __init__(self, input_dim: int, hidden: int = 512, hidden2: int = 128, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden2), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden2, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.net(x).squeeze(-1)

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

def load_pairs_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rows.append(json.loads(line))
    return rows

import re
def augment_rows(rows: List[Dict[str, Any]], p_swap: float = 0.05, p_punct_noise: float = 0.10, p_case_noise: float = 0.05, seed: int = RANDOM_SEED) -> List[Dict[str, Any]]:
    """Aplica augmentaciones ligeras: intercambio orden, ruido puntuacion y caso en texto"""
    random.seed(seed)
    out = []
    for r in rows:
        nr = r.copy()
        a_text = nr['a']['text'] or ""
        b_text = nr['b']['text'] or ""
        if random.random() < p_swap:
            nr = json.loads(json.dumps(nr))
            nr['a']['text'], nr['b']['text'] = b_text, a_text
        def punct_noise(s):
            if not s or random.random() >= p_punct_noise:
                return s
            pos = random.randint(0, len(s))
            if random.random() < 0.6:
                p = random.choice([",", ".", " ...", "!", "?", ";"])
                return s[:pos] + p + s[pos:]
            else:
                return re.sub(r'[,.!?;:]+', '', s, count=1)
        nr['a']['text'] = punct_noise(nr['a']['text'])
        nr['b']['text'] = punct_noise(nr['b']['text'])
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

def choose_and_build_splits(rows: List[Dict[str, Any]], n_splits: int, dataset_stats_path: str = "./threads_analysis/models/output/dataset_stats.json"):
    """Construye splits automaticamente usando KFold, GroupKFold o Custom StratifiedGroupKFold segun estadisticas del dataset"""
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

    if n_groups <= 1:
        print("📌 Usando KFold (solo 1 chat o sin chat_id).")
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
        return list(splitter.split(np.arange(len(rows))))

    pos_ratios = [st["pos_ratio"] for st in chat_stats.values()]
    hard_ratios = [st["hard_ratio"] for st in chat_stats.values()]
    pos_var = np.var(pos_ratios)
    hard_var = np.var(hard_ratios)
    heterogeneous = pos_var > 0.0004 or hard_var > 0.002

    if heterogeneous:
        print("📌 Usando Custom Stratified-Group-KFold (dataset heterogéneo).")

        chat_profiles = []
        chat_ids = []
        for cid, st in chat_stats.items():
            chat_profiles.append([st["pos_ratio"], st["neg_ratio"], st["hard_ratio"]])
            chat_ids.append(int(cid))
        chat_profiles = np.array(chat_profiles)
        chat_ids = np.array(chat_ids)

        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=n_splits, random_state=RANDOM_SEED, n_init="auto")
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

    if n_groups >= n_splits * 3:
        print("📌 Usando GroupKFold (muchos chats, ratios similares).")
    else:
        print("📌 Usando GroupKFold (pocos chats pero ratios similares).")

    splitter = GroupKFold(n_splits=n_splits)
    return list(splitter.split(np.arange(len(rows)), y, groups))

def build_mlp_features_from_embeddings(emb_a: np.ndarray, emb_b: np.ndarray, extras: Dict[str, Any]) -> np.ndarray:
    """Construye vector de características para MLP concatenando embeddings y características extra"""
    a = emb_a.astype(np.float32)
    b = emb_b.astype(np.float32)
    comb = np.concatenate([a, b, np.abs(a - b), a * b], axis=0).astype(np.float32)
    extra_list = [
        float(extras.get('len_a', 0)), float(extras.get('len_b', 0)),
        float(extras.get('tfidf_jaccard', 0.0)), float(extras.get('seq_ratio', 0.0)),
        float(extras.get('emoji_diff', 0)), float(extras.get('both_have_url', 0)),
        float(extras.get('both_all_caps', 0)), float(extras.get('time_delta_min', 1e6)),
        float(extras.get('same_author', 0))
    ]
    extra_arr = np.array(extra_list, dtype=np.float32)
    feat = np.concatenate([comb, extra_arr], axis=0)
    return feat

def train_anomaly_models_for_fold(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], 
                                  base_encoder: SentenceTransformer, fold_dir: str):
    """
    Entrena modelos One-Class SVM e Isolation Tree solo con ejemplos positivos del train.
    
    Args:
        rows_train: Lista de ejemplos de entrenamiento (todos)
        rows_val: Lista de ejemplos de validación
        base_encoder: Modelo de sentence transformer para extraer embeddings
        fold_dir: Directorio donde guardar los modelos
    """
    print("[ANOMALY] Entrenando One-Class SVM e Isolation Tree solo con positivos...")
    
    anomaly_dir = os.path.join(fold_dir, "anomaly_models")
    os.makedirs(anomaly_dir, exist_ok=True)
    
    progress_file = os.path.join(anomaly_dir, "anomaly_training_progress.json")
    progress_data = {
        "model_type": "anomaly_models",
        "fold_dir": fold_dir,
        "start_time": datetime.datetime.now().isoformat(),
        "one_class_svm": {},
        "isolation_forest": {}
    }
    
    # 1. Filtrar solo ejemplos positivos del train
    positive_rows = [r for r in rows_train if r.get('label', 0) == 1]
    
    if len(positive_rows) < 10:
        print(f"[ANOMALY] Solo {len(positive_rows)} ejemplos positivos en train. Saltando modelos de anomalía.")
        progress_data["warning"] = f"Solo {len(positive_rows)} ejemplos positivos en train"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        return None
    
    print(f"[ANOMALY] {len(positive_rows)} ejemplos positivos para entrenar modelos de anomalía")
    
    # 2. Extraer embeddings para los positivos (solo texto A, asumiendo que representan la clase "normal")
    def batch_encode_texts(texts, batch=64):
        all_embs = []
        for i in tqdm(range(0, len(texts), batch), desc="[ANOMALY ENCODE]"):
            batch_texts = texts[i:i+batch]
            embs = base_encoder.encode(batch_texts, device=DEVICE, batch_size=batch, 
                                       convert_to_numpy=True, show_progress_bar=False)
            all_embs.extend(embs)
        return all_embs
    
    # Usamos solo el texto A de los pares positivos (asumiendo que son mensajes de referencia)
    positive_texts = [r['a']['text'] or "" for r in positive_rows]
    positive_embeddings = batch_encode_texts(positive_texts)
    
    # Convertir a numpy array
    X_train_positive = np.array(positive_embeddings)
    
    # 3. Preparar datos de validación (todos los ejemplos de val)
    val_texts_a = [r['a']['text'] or "" for r in rows_val]
    val_texts_b = [r['b']['text'] or "" for r in rows_val]
    
    # Codificar ambos textos
    val_embeddings_a = batch_encode_texts(val_texts_a)
    val_embeddings_b = batch_encode_texts(val_texts_b)
    
    # Para validación, podemos usar ambos embeddings o combinarlos
    # Usamos el embedding del texto A como representación del par
    X_val = np.array(val_embeddings_a)
    y_val = np.array([int(r.get('label', 0)) for r in rows_val])
    
    # 4. Entrenar One-Class SVM
    print("[ANOMALY] Entrenando One-Class SVM...")
    anomaly_params = get_training_params("anomaly")
    
    oc_svm = OneClassSVM(
        nu=anomaly_params.get("oc_svm_nu", 0.1),
        kernel=anomaly_params.get("oc_svm_kernel", "rbf"),
        gamma=anomaly_params.get("oc_svm_gamma", "scale"),
        random_state=RANDOM_SEED
    )
    
    oc_svm.fit(X_train_positive)
    
    # Predecir en validación
    # OneClassSVM devuelve: 1 para inliers (normales), -1 para outliers
    svm_predictions = oc_svm.predict(X_val)
    # Convertir a 1 para positivo (normal/inlier) y 0 para negativo (outlier)
    svm_pred_binary = np.where(svm_predictions == 1, 1, 0)
    
    # Calcular métricas
    svm_p, svm_r, svm_f, _ = precision_recall_fscore_support(
        y_val, svm_pred_binary, average='binary', zero_division=0
    )
    
    # También obtener scores de decisión para AUC
    svm_scores = oc_svm.decision_function(X_val)
    # Normalizar scores para que mayores valores signifiquen más "normal"
    svm_scores_normalized = (svm_scores - svm_scores.min()) / (svm_scores.max() - svm_scores.min() + 1e-8)
    svm_auc = roc_auc_score(y_val, svm_scores_normalized) if len(np.unique(y_val)) > 1 else 0.0
    
    progress_data["one_class_svm"] = {
        "train_samples": len(X_train_positive),
        "nu": anomaly_params.get("oc_svm_nu", 0.1),
        "kernel": anomaly_params.get("oc_svm_kernel", "rbf"),
        "precision": float(svm_p),
        "recall": float(svm_r),
        "f1": float(svm_f),
        "auc": float(svm_auc)
    }
    
    print(f"[ANOMALY] One-Class SVM: F1={svm_f:.4f}, AUC={svm_auc:.4f}")
    
    # 5. Entrenar Isolation Forest
    print("[ANOMALY] Entrenando Isolation Forest...")
    
    iso_forest = IsolationForest(
        contamination=anomaly_params.get("isolation_forest_contamination", 0.1),
        n_estimators=anomaly_params.get("isolation_forest_n_estimators", 100),
        random_state=RANDOM_SEED,
        n_jobs=-1
    )
    
    iso_forest.fit(X_train_positive)
    
    # Predecir en validación
    # IsolationForest devuelve: 1 para inliers, -1 para outliers
    iso_predictions = iso_forest.predict(X_val)
    iso_pred_binary = np.where(iso_predictions == 1, 1, 0)
    
    # Calcular métricas
    iso_p, iso_r, iso_f, _ = precision_recall_fscore_support(
        y_val, iso_pred_binary, average='binary', zero_division=0
    )
    
    # Scores de anomalía (negativos para outliers)
    iso_scores = iso_forest.decision_function(X_val)
    # Normalizar e invertir para que mayores valores signifiquen más "normal"
    iso_scores_normalized = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-8)
    iso_auc = roc_auc_score(y_val, iso_scores_normalized) if len(np.unique(y_val)) > 1 else 0.0
    
    progress_data["isolation_forest"] = {
        "train_samples": len(X_train_positive),
        "contamination": anomaly_params.get("isolation_forest_contamination", 0.1),
        "n_estimators": anomaly_params.get("isolation_forest_n_estimators", 100),
        "precision": float(iso_p),
        "recall": float(iso_r),
        "f1": float(iso_f),
        "auc": float(iso_auc)
    }
    
    print(f"[ANOMALY] Isolation Forest: F1={iso_f:.4f}, AUC={iso_auc:.4f}")
    
    # 6. Guardar modelos
    svm_path = os.path.join(anomaly_dir, "one_class_svm.joblib")
    iso_path = os.path.join(anomaly_dir, "isolation_forest.joblib")
    
    joblib.dump(oc_svm, svm_path)
    joblib.dump(iso_forest, iso_path)
    
    # 7. Guardar embeddings base para referencia
    embeddings_info = {
        "embedding_dim": X_train_positive.shape[1],
        "model_used": str(base_encoder),
        "positive_samples": len(positive_rows)
    }
    
    embeddings_path = os.path.join(anomaly_dir, "embeddings_info.json")
    with open(embeddings_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings_info, f, ensure_ascii=False, indent=2)
    
    # 8. Guardar progreso
    progress_data["end_time"] = datetime.datetime.now().isoformat()
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)
    
    print(f"[ANOMALY] Modelos guardados en {anomaly_dir}")
    
    return {
        "one_class_svm": {"f1": svm_f, "auc": svm_auc},
        "isolation_forest": {"f1": iso_f, "auc": iso_auc}
    }

def train_mlp_for_fold(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], emb_model: SentenceTransformer,
                       output_dir: str, fold_dir: str, batch_size: int, epochs: int, lr: float, accum_steps: int):
    print("[MLP] Construyendo embeddings con GPU + codificación por lotes...")
    mlp_dir = os.path.join(fold_dir, "mlp_on_" + emb_model.__class__.__module__.split(".")[0])
    os.makedirs(mlp_dir, exist_ok=True)
    
    progress_file = os.path.join(mlp_dir, "training_progress.json")
    progress_data = {
        "model": "MLP", "fold_dir": fold_dir, "epochs": epochs, "batch_size": batch_size,
        "learning_rate": lr, "training_history": [], "start_time": datetime.datetime.now().isoformat()
    }

    def batch_encode_texts(texts, batch=64):
        all_embs = []
        for i in tqdm(range(0, len(texts), batch), desc="[ENCODE GPU]"):
            batch_texts = texts[i:i+batch]
            embs = emb_model.encode(batch_texts, device=DEVICE, batch_size=batch, convert_to_numpy=True, show_progress_bar=False)
            all_embs.extend(embs)
        return all_embs

    train_a = [r['a']['text'] or "" for r in rows_train]
    train_b = [r['b']['text'] or "" for r in rows_train]
    val_a   = [r['a']['text'] or "" for r in rows_val]
    val_b   = [r['b']['text'] or "" for r in rows_val]

    emb_train_a = batch_encode_texts(train_a)
    emb_train_b = batch_encode_texts(train_b)
    emb_val_a   = batch_encode_texts(val_a)
    emb_val_b   = batch_encode_texts(val_b)

    for i, r in enumerate(rows_train):
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(emb_train_a[i], emb_train_b[i], extras)

    for i, r in enumerate(rows_val):
        extras = r.get('features_extra', {})
        extras['time_delta_min'] = r.get('time_delta_min', 1e6)
        extras['same_author'] = r.get('same_author', 0)
        r['mlp_features'] = build_mlp_features_from_embeddings(emb_val_a[i], emb_val_b[i], extras)

    mlp_params = get_training_params("mlp")
    input_dim = rows_train[0]['mlp_features'].shape[0]
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

        epoch_data = {
            "epoch": epoch, "loss": float(avg_loss), "precision": float(p),
            "recall": float(r), "f1": float(f), "timestamp": datetime.datetime.now().isoformat()
        }
        progress_data["training_history"].append(epoch_data)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        print(f"[MLP] Epoch {epoch}: loss={avg_loss:.4f} P={p:.4f} R={r:.4f} F1={f:.4f} - Progreso guardado")

        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k, v in mlp.state_dict().items()}

    if best_state is not None:
        model_path = os.path.join(mlp_dir, "mlp_model.pth")
        torch.save(best_state, model_path)
        
        progress_data["final_f1"] = float(best_f1)
        progress_data["end_time"] = datetime.datetime.now().isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[MLP] Guardado mejor mlp en {model_path} (F1={best_f1:.4f}) - Progreso final guardado")

    return best_f1

def finetune_bi_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]],
                        output_dir: str, fold: int, epochs: int = 3, batch_size: int = 32, lr: float = 2e-5,
                        warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[BI] Fine-tuning bi-encoder {model_name} (tag={model_tag}) fold={fold}")

    model_save_path = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_save_path, exist_ok=True)
    
    progress_file = os.path.join(model_save_path, "training_progress.json")
    progress_data = {
        "model": model_name, "fold": fold, "epochs": epochs, "batch_size": batch_size,
        "learning_rate": lr, "training_history": [], "start_time": datetime.datetime.now().isoformat()
    }

    model = SentenceTransformer(model_name)
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
        print("[BI] No hay ejemplos positivos en train para este fold; saltando fine-tune bi-encoder")
        return None, model

    train_dataloader = torch.utils.data.DataLoader(train_examples, shuffle=True, batch_size=batch_size, collate_fn=model.smart_batching_collate)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    
    from sentence_transformers.evaluation import BinaryClassificationEvaluator
    val_a = [r['a']['text'] for r in rows_val]
    val_b = [r['b']['text'] for r in rows_val]
    val_labels = [int(r.get('label', 0)) for r in rows_val]
    evaluator = BinaryClassificationEvaluator(val_a, val_b, val_labels, show_progress_bar=False)

    warmup_steps = math.ceil(len(train_dataloader) * epochs * warmup_pct)
    
    class ProgressCallback:
        def __init__(self, progress_file, progress_data):
            self.progress_file = progress_file
            self.progress_data = progress_data
            
        def __call__(self, score, epoch, steps):
            epoch_data = {"epoch": epoch, "steps": steps, "score": float(score), "timestamp": datetime.datetime.now().isoformat()}
            self.progress_data["training_history"].append(epoch_data)
            
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
        callback=progress_callback
    )

    final_score = evaluator(model)
    progress_data["final_score"] = float(final_score)
    progress_data["end_time"] = datetime.datetime.now().isoformat()
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

    print(f"[BI] Guardado bi-encoder en {model_save_path} - Progreso final guardado")
    return model_save_path, final_score

def finetune_cross_encoder(model_name: str, rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], 
                           output_dir: str, fold: int, epochs: int = 3, batch_size: int = 16, lr: float = 2e-5,
                           warmup_pct: float = 0.06, accum_steps: int = 1):
    model_tag = model_name.split("/")[-1]
    print(f"[CE] Fine-tuning cross-encoder {model_name} fold={fold}")

    model_dir = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_dir, exist_ok=True)
    
    progress_file = os.path.join(model_dir, "training_progress.json")
    progress_data = {
        "model": model_name, "fold": fold, "epochs": epochs, "batch_size": batch_size,
        "learning_rate": lr, "training_history": [], "start_time": datetime.datetime.now().isoformat()
    }
    
    try:
        from huggingface_hub import hf_hub_download
        use_hf_hub = True
    except Exception:
        use_hf_hub = False

    model_dir_local = os.path.join(output_dir, f"fold_{fold}", model_tag)
    os.makedirs(model_dir_local, exist_ok=True)

    needs_download = not (os.path.exists(os.path.join(model_dir_local, "config.json")) or os.path.exists(os.path.join(model_dir_local, "pytorch_model.bin")))
    if needs_download and use_hf_hub:
        print(f"[CE] Descargando pesos/tokenizer de '{model_name}' con progreso (hf_hub)...")
        files_to_try = ["pytorch_model.bin", "tf_model.h5", "flax_model.msgpack", "config.json", "tokenizer.json"]
        for fname in files_to_try:
            try:
                hf_hub_download(repo_id=model_name, filename=fname, cache_dir=model_dir_local, force_download=False)
            except Exception:
                pass
        print("[CE] Descarga hf_hub tentativa completada. Ahora from_pretrained() puede cargar desde cache.")

    if needs_download and not use_hf_hub:
        print(f"[CE] Modelo/tokenizer no encontrado localmente. Llamando a transformers.from_pretrained() (esto descargará archivos).")
        print("[CE] Descarga en progreso... (puede tardar).")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1).to(DEVICE)

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
            if clip_value is not None:
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip_value)
            if step % accum_steps == 0:
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad()
            total_loss += (loss.item() * accum_steps)

        avg_loss = total_loss / max(1, len(train_loader))
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
        
        epoch_data = {
            "epoch": epoch, "loss": float(avg_loss), "auc": float(auc),
            "precision": float(p), "recall": float(r), "f1": float(f),
            "timestamp": datetime.datetime.now().isoformat()
        }
        progress_data["training_history"].append(epoch_data)
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        
        print(f"[CE] Epoch {epoch}: loss={avg_loss:.4f} val_AUC={auc:.4f} P={p:.4f} R={r:.4f} F1={f:.4f} - Progreso guardado")
        
        if f > best_f1:
            best_f1 = f
            best_state = {k: v.cpu() for k,v in model.state_dict().items()}

    if best_state is not None:
        torch.save(best_state, os.path.join(model_dir, "model.pth"))
        tokenizer.save_pretrained(model_dir)
        
        progress_data["final_f1"] = float(best_f1)
        progress_data["end_time"] = datetime.datetime.now().isoformat()
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CE] Guardado mejor cross-encoder en {model_dir} (F1={best_f1:.4f}) - Progreso final guardado")
    return model_dir, best_f1

def train_classical_models(rows_train: List[Dict[str, Any]], rows_val: List[Dict[str, Any]], fold_dir: str):
    """Entrena y guarda modelos clasicos: GaussianNB, LogisticRegression, LightGBM y RandomForest"""
    try:
        import joblib
        from sklearn.naive_bayes import GaussianNB
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
    except Exception as e:
        print(f"[CLASSICAL] Faltan dependencias sklearn/joblib: {e}")
        return {}

    try:
        import lightgbm as lgb
        has_lgb = True
    except Exception:
        has_lgb = False

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
    
    progress_file = os.path.join(fold_dir, "classical_training_progress.json")
    progress_data = {"models_trained": [], "start_time": datetime.datetime.now().isoformat()}

    try:
        nb = GaussianNB()
        nb.fit(X_train, y_train)
        preds = nb.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['gaussian_nb'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(nb, os.path.join(fold_dir, "gaussian_nb.joblib"))
        
        model_data = {
            "model": "GaussianNB", "f1": float(f), "precision": float(p),
            "recall": float(r), "timestamp": datetime.datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CLASSICAL] GaussianNB F1={f:.4f} - Progreso guardado")
    except Exception as e:
        print(f"[CLASSICAL] GaussianNB failed: {e}")

    try:
        lr = LogisticRegression(max_iter=1000, solver='saga', penalty='l2', n_jobs=1, random_state=RANDOM_SEED)
        lr.fit(X_train, y_train)
        preds = lr.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['logistic_regression'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(lr, os.path.join(fold_dir, "logistic_regression.joblib"))
        
        model_data = {
            "model": "LogisticRegression", "f1": float(f), "precision": float(p),
            "recall": float(r), "timestamp": datetime.datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
        print(f"[CLASSICAL] LogisticRegression F1={f:.4f} - Progreso guardado")
    except Exception as e:
        print(f"[CLASSICAL] LogisticRegression failed: {e}")

    if has_lgb:
        try:
            lgb_clf = lgb.LGBMClassifier(n_estimators=200, num_leaves=31, n_jobs=2, random_state=RANDOM_SEED)
            lgb_clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20, verbose=False)
            preds = lgb_clf.predict(X_val)
            p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
            results['lightgbm'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
            joblib.dump(lgb_clf, os.path.join(fold_dir, "lightgbm.joblib"))
            
            model_data = {
                "model": "LightGBM", "f1": float(f), "precision": float(p),
                "recall": float(r), "timestamp": datetime.datetime.now().isoformat()
            }
            progress_data["models_trained"].append(model_data)
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
                
            print(f"[CLASSICAL] LightGBM F1={f:.4f} - Progreso guardado")
        except Exception as e:
            print(f"[CLASSICAL] LightGBM failed: {e}")
    else:
        print("[CLASSICAL] LightGBM no instalado, saltando.")

    try:
        rf = RandomForestClassifier(n_estimators=100, max_depth=12, n_jobs=2, random_state=RANDOM_SEED)
        rf.fit(X_train, y_train)
        preds = rf.predict(X_val)
        p, r, f, _ = precision_recall_fscore_support(y_val, preds, average='binary', zero_division=0)
        results['random_forest'] = {'f1': float(f), 'p': float(p), 'r': float(r)}
        joblib.dump(rf, os.path.join(fold_dir, "random_forest.joblib"))
        
        model_data = {
            "model": "RandomForest", "f1": float(f), "precision": float(p),
            "recall": float(r), "timestamp": datetime.datetime.now().isoformat()
        }
        progress_data["models_trained"].append(model_data)
        progress_data["end_time"] = datetime.datetime.now().isoformat()
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
    print(f"[INFO] Cargados {len(rows)} pares de {pairs_path}")

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

    print(f"[INFO] Tamaño conjunto evaluacion (por chat): {len(rows_eval)}")
    print(f"[INFO] Tamaño Train+Val: {len(rows_trainval)}")

    eval_path = os.path.join(output_dir, "evaluation_set.jsonl")
    with open(eval_path, "w", encoding="utf-8") as f:
        for r in rows_eval:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[INFO] Guardado conjunto evaluacion → {eval_path}")

    rows = rows_trainval

    splits = choose_and_build_splits(rows, n_splits)
    print(f"[INFO] Construidos {len(splits)} splits (folds)")

    summary = {"bi_a": [], "bi_b": [], "cross": [], "anomaly": []}

    fold_idx = 0
    for train_idx, val_idx in splits:
        fold_idx += 1
        print(f"\n===== Comenzando fold {fold_idx}/{len(splits)} =====")

        fold_summary = {"fold": fold_idx, "bi_a": {}, "bi_b": {}, "cross": {}, "anomaly": {}}

        rows_train = [rows[i] for i in train_idx]
        rows_train = augment_rows(rows_train, p_swap=0.05, p_punct_noise=0.10, p_case_noise=0.05, seed=RANDOM_SEED + fold_idx)
        rows_val = [rows[i] for i in val_idx]

        MAX_TRAIN = 500_000
        MAX_VAL = 200_000

        rows_train = sample_by_chat(rows_train, MAX_TRAIN)
        rows_val   = sample_by_chat(rows_val, MAX_VAL)

        force_retrain = True

        # 1. ENTRENAR MODELOS DE ANOMALÍA PRIMERO (solo con positivos)
        print("\n=== Entrenando modelos de anomalía (One-Class SVM e Isolation Tree) ===")
        
        # Usar el bi-encoder A base (sin fine-tune) para extraer embeddings
        base_bi_encoder = SentenceTransformer(BI_ENCODER_A)
        
        # Entrenar modelos de anomalía
        anomaly_results = train_anomaly_models_for_fold(
            rows_train, rows_val, base_encoder=base_bi_encoder, fold_dir=os.path.join(output_dir, f"fold_{fold_idx}")
        )
        
        if anomaly_results:
            fold_summary["anomaly"] = anomaly_results
            summary["anomaly"].append({"fold": fold_idx, **anomaly_results})
        
        print("\n=== Continuando con modelos supervisados ===")
        
        # 2. CONTINUAR CON MODELOS SUPERVISADOS
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
                    fold=fold_idx, epochs=epochs, batch_size=batch_size,
                    lr=lr, warmup_pct=DEFAULT_WARMUP_PCT, accum_steps=accum_steps
                )
                bi_a_model = SentenceTransformer(bi_a_dir)
            except Exception as e:
                print(f"[ERROR] bi-encoder A fold {fold_idx} failed: {e}")
                bi_a_model = SentenceTransformer(BI_ENCODER_A)

        mlp_f1_a = train_mlp_for_fold(
            rows_train, rows_val, bi_a_model, output_dir, os.path.join(output_dir, f"fold_{fold_idx}"),
            batch_size=batch_size, epochs=epochs, lr=1e-3, accum_steps=1
        )

        fold_summary["bi_a"] = {"mlp_f1": mlp_f1_a, "model_dir": bi_a_out}
        summary["bi_a"].append({"fold": fold_idx, "mlp_f1": mlp_f1_a, "model_dir": bi_a_out})

        classical_a_dir = os.path.join(output_dir, f"fold_{fold_idx}", "classical_a")
        train_classical_models(rows_train, rows_val, classical_a_dir)

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
                    fold=fold_idx, epochs=epochs, batch_size=batch_size,
                    lr=lr, warmup_pct=DEFAULT_WARMUP_PCT, accum_steps=accum_steps
                )
                bi_b_model = SentenceTransformer(bi_b_dir)
            except Exception as e:
                print(f"[ERROR] bi-encoder B fold {fold_idx} failed: {e}")
                bi_b_model = SentenceTransformer(BI_ENCODER_B)

        mlp_f1_b = train_mlp_for_fold(
            rows_train, rows_val, bi_b_model, output_dir, os.path.join(output_dir, f"fold_{fold_idx}"),
            batch_size=batch_size, epochs=epochs, lr=1e-3, accum_steps=1
        )

        fold_summary["bi_b"] = {"mlp_f1": mlp_f1_b, "model_dir": bi_b_out}
        summary["bi_b"].append({"fold": fold_idx, "mlp_f1": mlp_f1_b, "model_dir": bi_b_out})

        classical_b_dir = os.path.join(output_dir, f"fold_{fold_idx}", "classical_b")
        train_classical_models(rows_train, rows_val, classical_b_dir)

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
                    fold=fold_idx, epochs=cross_params.get("epochs", epochs),
                    batch_size=cross_params.get("batch_size", max(8, batch_size//2)),
                    lr=cross_params.get("lr", lr), warmup_pct=cross_params.get("warmup_pct", DEFAULT_WARMUP_PCT),
                    accum_steps=cross_params.get("accum_steps", accum_steps)
                )
            except Exception as e:
                print(f"[ERROR] cross-encoder fold {fold_idx} failed: {e}")
                ce_f1 = None

        fold_summary["cross"] = {"cross_f1": ce_f1, "model_dir": ce_out}
        summary["cross"].append({"fold": fold_idx, "cross_f1": ce_f1, "model_dir": ce_out})

        fold_summary_path = os.path.join(output_dir, f"fold_{fold_idx}", f"training_summary_fold_{fold_idx}.json")
        with open(fold_summary_path, "w", encoding="utf-8") as f:
            json.dump(fold_summary, f, ensure_ascii=False, indent=2)

        print(f"[INFO] Guardado resumen fold → {fold_summary_path}")

    with open(os.path.join(output_dir, "training_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("[INFO] Entrenamiento completo. Resumen guardado en training_summary.json")

    best_output = os.path.join(output_dir, "best")
    os.makedirs(best_output, exist_ok=True)

    def export_best(summary_key, subdir_name, is_bi_encoder=True, is_anomaly=False):
        entries = summary.get(summary_key, [])
        if not entries:
            print(f"[WARN] No hay entradas para {summary_key}")
            return

        if is_anomaly:
            # Para anomalía, elegir el mejor fold basado en el promedio de F1 de ambos modelos
            best = None
            best_score = -1
            for entry in entries:
                if "one_class_svm" in entry and "isolation_forest" in entry:
                    svm_f1 = entry["one_class_svm"].get("f1", 0)
                    iso_f1 = entry["isolation_forest"].get("f1", 0)
                    avg_f1 = (svm_f1 + iso_f1) / 2
                    if avg_f1 > best_score:
                        best_score = avg_f1
                        best = entry
            
            if best:
                print(f"[BEST] {summary_key}: fold={best['fold']} Avg_F1={best_score:.4f}")
                fold_num = best['fold']
                
                # Copiar modelos de anomalía del mejor fold
                anomaly_src = os.path.join(output_dir, f"fold_{fold_num}", "anomaly_models")
                anomaly_dest = os.path.join(best_output, subdir_name)
                
                if os.path.exists(anomaly_src):
                    import shutil
                    shutil.copytree(anomaly_src, anomaly_dest, dirs_exist_ok=True)
                    print(f"[BEST] Copiados mejores modelos de anomalía a {anomaly_dest}")
                else:
                    print(f"[WARN] No se encontró directorio de anomalía en fold {fold_num}")
            return

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
            print(f"[WARN] No se encontro directorio de modelo para {summary_key}")
            return

        dest = os.path.join(best_output, subdir_name)
        os.makedirs(dest, exist_ok=True)

        import shutil
        shutil.copytree(model_dir, dest, dirs_exist_ok=True)
        print(f"[BEST] Copiado mejor modelo {summary_key} a {dest}")

    export_best("bi_a", "bi_encoder_A", is_bi_encoder=True)
    export_best("bi_b", "bi_encoder_B", is_bi_encoder=True)
    export_best("cross", "cross_encoder", is_bi_encoder=False)
    export_best("anomaly", "anomaly_models", is_bi_encoder=False, is_anomaly=True)

    return summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=str, required=True, help='Ruta a pairs jsonl (output dataset)')
    parser.add_argument('--output-dir', type=str, default='threads_analysis/models/output')
    parser.add_argument('--folds', type=int, default=5)
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=2e-5)
    parser.add_argument('--accum', type=int, default=2)
    args = parser.parse_args()

    train_all_models(args.pairs, output_dir=args.output_dir, n_splits=args.folds,
                     epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, accum_steps=args.accum)