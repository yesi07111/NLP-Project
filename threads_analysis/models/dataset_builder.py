"""
threads_analysis/models/dataset_builder.py

Construye el dataset a partir de chats en threads_analysis_results/train_chats.
Características principales:
- Caching de embeddings por chat + por modelo (npy + meta)
- Caching del archivo de pairs con sidecar .meta.json (chat list, total_messages, params)
- Nuevas features extraídas desde los mensajes:
  * length_a, length_b
  * tfidf_jaccard (jaccard sobre tokens TF-IDF non-zero)
  * seq_ratio (dif. con difflib SequenceMatcher)
  * emoji_diff
  * both_have_url
  * both_all_caps
- Hard negative mining usando embeddings (configurable: top_k, take_k, sim_threshold)
- Soporta grandes chats (optimizado para memoria: guarda embeddings en disco)
- Uso:
    python -m threads_analysis.models.dataset_builder --input-dir threads_analysis_results/train_chats \
        --output threads_analysis/models/output/pairs_mpnet_hardneg.jsonl \
        --emb-model sentence-transformers/all-mpnet-base-v2
"""

from __future__ import annotations
import os
import json
import math
import random
from glob import glob
from typing import List, Dict, Any, Tuple

import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
import argparse
import re
from difflib import SequenceMatcher

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Default embedding model (strong bi-encoder)
DEFAULT_EMB_MODEL = "sentence-transformers/all-mpnet-base-v2"

BASE_CACHE_DIR = "threads_analysis/models/embedding_cache"
os.makedirs(BASE_CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname("threads_analysis/models/output/pairs.jsonl"), exist_ok=True)

# emoji regex covering common ranges
EMOJI_RE = re.compile(
    '['
    '\U0001F300-\U0001F5FF'  # symbols & pictographs
    '\U0001F600-\U0001F64F'  # emoticons
    '\U0001F680-\U0001F6FF'  # transport & map symbols
    '\U0001F700-\U0001F77F'  # alchemical symbols
    '\U0001F780-\U0001F7FF'  # Geometric Shapes Extended
    '\U0001F800-\U0001F8FF'  # Supplemental Arrows-C
    '\U0001F900-\U0001F9FF'  # Supplemental Symbols and Pictographs
    '\U0001FA00-\U0001FA6F'  # Chess etc
    '\U00002702-\U000027B0'  # Dingbats
    '\U000024C2-\U0001F251'
    ']+', flags=re.UNICODE
)

URL_RE = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)


# ---------------- Helpers ----------------
def _parse_iso(ts: str):
    from datetime import datetime
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None


def _compute_time_delta_min(t1: str, t2: str) -> float:
    dt1 = _parse_iso(t1)
    dt2 = _parse_iso(t2)
    if not dt1 or not dt2:
        return 1e6
    return abs((dt2 - dt1).total_seconds()) / 60.0


# ---------------- Chat loading ----------------
def load_chats(input_dir: str) -> List[Dict[str, Any]]:
    files = sorted(glob(os.path.join(input_dir, '*.json')))
    chats = []
    for i, fp in enumerate(files):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_file_path'] = fp
                data['_chat_id'] = i
                chats.append(data)
        except Exception as e:
            print(f"[WARN] Error leyendo {fp}: {e}")
    return chats


# ---------------- Feature extraction utilities ----------------
def count_emojis(text: str) -> int:
    if not text:
        return 0
    return len(EMOJI_RE.findall(text))


def has_url(text: str) -> bool:
    if not text:
        return False
    return bool(URL_RE.search(text))


def is_all_caps(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def seq_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def tfidf_jaccard_batch(texts: List[str]) -> Tuple[TfidfVectorizer, np.ndarray]:
    """
    Build TF-IDF vectorizer and matrix for the list of texts.
    We'll use sparse non-zero sets to compute Jaccard between two texts quickly.
    Returns (vectorizer, matrix)
    """
    vect = TfidfVectorizer(max_features=8192, analyzer='word', token_pattern=r'\w+')
    X = vect.fit_transform(texts)
    return vect, X


def jaccard_from_sparse_row(row_i, row_j) -> float:
    # row_i and row_j are CSR row slices
    if row_i.nnz == 0 and row_j.nnz == 0:
        return 1.0
    set_i = set(row_i.indices.tolist())
    set_j = set(row_j.indices.tolist())
    inter = len(set_i & set_j)
    union = len(set_i | set_j)
    return float(inter) / float(union) if union else 0.0


# ---------------- Embedding cache helpers ----------------
def emb_cache_paths(chat_id: int, emb_model_name: str):
    safe_model = emb_model_name.replace('/', '__').replace(':', '__')
    emb_dir = os.path.join(BASE_CACHE_DIR, safe_model)
    os.makedirs(emb_dir, exist_ok=True)
    emb_path = os.path.join(emb_dir, f"{chat_id}.npy")
    meta_path = os.path.join(emb_dir, f"{chat_id}_meta.json")
    return emb_path, meta_path


def load_emb_cache(chat_id: int, emb_model_name: str):
    emb_path, meta_path = emb_cache_paths(chat_id, emb_model_name)
    if not os.path.exists(emb_path) or not os.path.exists(meta_path):
        return None
    try:
        embeddings = np.load(emb_path, allow_pickle=False)
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return {
            "_embeddings": embeddings,
            "_texts": meta.get("texts", []),
            "_ids": meta.get("ids", [])
        }
    except Exception:
        return None


def save_emb_cache(chat_id: int, emb_model_name: str, texts: List[str], ids: List[Any], embeddings: np.ndarray):
    emb_path, meta_path = emb_cache_paths(chat_id, emb_model_name)
    # save embeddings as float32
    np.save(emb_path, embeddings.astype(np.float32))
    with open(meta_path, "w", encoding='utf-8') as f:
        json.dump({"texts": texts, "ids": ids}, f, ensure_ascii=False)


# ---------------- Building base pairs ----------------
def build_pairs(chats: List[Dict[str, Any]], neg_ratio: int = 2, max_prev: int = 10) -> List[Dict[str, Any]]:
    pairs: List[Dict[str, Any]] = []
    for chat in chats:
        messages = chat.get('messages', [])
        id2msg = {m['id']: m for m in messages}
        msgs_sorted = sorted(messages, key=lambda m: m.get('date', ''))

        for i, msg in enumerate(msgs_sorted):
            mid = msg.get('id')
            if mid is None:
                continue

            # positive (explicit reply)
            reply_id = msg.get('reply_id')
            if reply_id and reply_id in id2msg:
                parent = id2msg[reply_id]
                td = _compute_time_delta_min(parent.get('date'), msg.get('date'))
                pairs.append({
                    'a': {'id': parent.get('id'), 'text': parent.get('text', ''), 'sender_id': parent.get('sender_id'), 'date': parent.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''), 'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 1, 'time_delta_min': td,
                    'same_author': int(parent.get('sender_id') == msg.get('sender_id')),
                    'chat_id': chat.get('_chat_id')
                })

            # random negatives
            for _ in range(neg_ratio):
                rand = random.choice(msgs_sorted)
                if rand.get('id') == mid:
                    continue
                td = _compute_time_delta_min(rand.get('date'), msg.get('date'))
                pairs.append({
                    'a': {'id': rand.get('id'), 'text': rand.get('text', ''), 'sender_id': rand.get('sender_id'), 'date': rand.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''), 'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 0, 'time_delta_min': td,
                    'same_author': int(rand.get('sender_id') == msg.get('sender_id')),
                    'chat_id': chat.get('_chat_id')
                })

            # temporal negative (recent but not parent)
            start = max(0, i - max_prev)
            candidates = [msgs_sorted[j] for j in range(start, i) if msgs_sorted[j].get('id') != reply_id]
            if candidates:
                tmp = random.choice(candidates)
                td = _compute_time_delta_min(tmp.get('date'), msg.get('date'))
                pairs.append({
                    'a': {'id': tmp.get('id'), 'text': tmp.get('text', ''), 'sender_id': tmp.get('sender_id'), 'date': tmp.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''), 'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 0, 'time_delta_min': td,
                    'same_author': int(tmp.get('sender_id') == msg.get('sender_id')),
                    'chat_id': chat.get('_chat_id')
                })

    return pairs


# ---------------- Hard negative mining ----------------
def add_hard_negatives(
    pairs: List[Dict[str, Any]],
    chats: List[Dict[str, Any]],
    emb_model_name: str = DEFAULT_EMB_MODEL,
    top_k: int = 50,
    take_k: int = 10,
    sim_threshold: float = 0.35
) -> List[Dict[str, Any]]:
    """
    For each positive pair (a->b), find top-k semantically similar candidates
    within the same chat and add up to take_k as hard negatives.
    Provides very detailed progress logging.
    """

    print("\n[HN] Cargando modelo de embeddings...")
    model = SentenceTransformer(emb_model_name)
    print("[HN] ✅ Modelo listo.\n")

    # --------------------------------------------------------
    # ETAPA 1: Embeddings por chat (con progreso detallado)
    # --------------------------------------------------------
    for chat in tqdm(chats, desc="Computing embeddings per chat"):
        cid = chat["_chat_id"]
        msgs = chat.get("messages", [])
        print(f"\n=== CHAT {cid} ===")
        print(f"[CHAT {cid}] Total mensajes: {len(msgs)}")

        cached = load_emb_cache(cid, emb_model_name)
        if cached:
            print(f"[CHAT {cid}] ✅ Cache encontrado. Cargando embeddings...")
            chat["_texts"] = cached["_texts"]
            chat["_embeddings"] = cached["_embeddings"]
            chat["_ids"] = cached["_ids"]
            continue

        print(f"[CHAT {cid}] ⚠️  No hay cache. Generando embeddings...")

        texts = [m.get("text", "") or "" for m in msgs]
        ids = [m.get("id") for m in msgs]

        # progreso por mensaje (cada 100)
        embs = []
        for idx, txt in enumerate(texts):
            if idx % 200 == 0:
                print(f"[CHAT {cid}] → {idx}/{len(texts)} mensajes codificados...")
            vec = model.encode(txt, convert_to_numpy=True, show_progress_bar=False)
            embs.append(vec)

        embs = np.vstack(embs)
        print(f"[CHAT {cid}] ✅ Embeddings generados. Guardando en cache...")

        chat["_texts"] = texts
        chat["_embeddings"] = embs
        chat["_ids"] = ids

        save_emb_cache(cid, emb_model_name, texts, ids, embs)

    # --------------------------------------------------------
    # ETAPA 2: Indexar positivos por chat
    # --------------------------------------------------------
    pos_by_chat: Dict[int, List[Dict[str, Any]]] = {}
    for p in pairs:
        if p.get("label", 0) == 1:
            pos_by_chat.setdefault(p["chat_id"], []).append(p)

    # --------------------------------------------------------
    # ETAPA 3: Hard Negative Mining (con logs extendidos)
    # --------------------------------------------------------
    new_neg = []
    for chat_id, positives in tqdm(pos_by_chat.items(), desc="Mining hard negatives (por chat)"):
        print(f"\n[HN] Procesando chat {chat_id} ({len(positives)} positivos)...")

        chat = next((c for c in chats if c["_chat_id"] == chat_id), None)
        if chat is None:
            print(f"[HN][Chat {chat_id}] ❌ Chat no encontrado")
            continue

        embs = chat.get("_embeddings")
        if embs is None or len(embs) == 0:
            print(f"[HN][Chat {chat_id}] ❌ Chat sin embeddings, se salta.")
            continue

        texts = chat["_texts"]
        ids = chat["_ids"]
        msgs = chat.get("messages", [])

        # procesar positivos con progreso
        for idx_pos, p in enumerate(positives):
            if idx_pos % 50 == 0:
                print(f"[HN][Chat {chat_id}] → Positivo {idx_pos}/{len(positives)}")

            b_text = p["b"]["text"] or ""
            emb_b = model.encode(b_text, convert_to_numpy=True)

            cosines = util.cos_sim(emb_b, embs)[0]
            top_idx = np.argsort(-cosines)[:top_k]

            taken = 0
            for idx in top_idx:
                idx = int(idx)
                cand_id = ids[idx]

                if cand_id == p["a"]["id"] or cand_id == p["b"]["id"]:
                    continue

                sim = float(cosines[idx])
                if sim < sim_threshold:
                    continue

                td = _compute_time_delta_min(msgs[idx].get("date"), p["b"]["date"])

                new_neg.append({
                    'a': {
                        'id': cand_id,
                        'text': texts[idx],
                        'sender_id': msgs[idx].get('sender_id'),
                        'date': msgs[idx].get('date')
                    },
                    'b': p['b'],
                    'label': 0,
                    'time_delta_min': td,
                    'same_author': int(msgs[idx].get('sender_id') == p['b']['sender_id']),
                    'chat_id': chat_id,
                    'hard_negative': True
                })

                taken += 1
                if taken >= take_k:
                    break

    print(f"\n[HN] ✅ Total hard negatives añadidos: {len(new_neg)}")
    pairs_ext = pairs + new_neg
    random.shuffle(pairs_ext)
    return pairs_ext


# ---------------- Feature enrichment ----------------
def enrich_pair_features(pairs: List[Dict[str, Any]], tfidf_vect: TfidfVectorizer, tfidf_matrix) -> List[Dict[str, Any]]:
    """
    Adds structural/lexical features with extended logging.
    """
    print(f"\n[Features] Enriqueciendo {len(pairs)} pairs...")

    enriched = []

    # Cache de TF-IDF por texto
    texts_pool = list({p['a']['text'] or "" for p in pairs} |
                      {p['b']['text'] or "" for p in pairs})
    print(f"[Features] TF-IDF pool: {len(texts_pool)} textos únicos.")

    idx_map = {t: i for i, t in enumerate(texts_pool)}
    X_pool = tfidf_vect.transform(texts_pool)

    for idx_feat, p in enumerate(tqdm(pairs, desc="Enriching features")):
        if idx_feat % 200000 == 0 and idx_feat > 0:
            print(f"[Features] → {idx_feat}/{len(pairs)} procesados...")

        a_text = p['a']['text'] or ""
        b_text = p['b']['text'] or ""

        row_a = X_pool[idx_map[a_text]]
        row_b = X_pool[idx_map[b_text]]
        tfidf_j = jaccard_from_sparse_row(row_a, row_b)

        seq_r = seq_similarity(a_text, b_text)
        emoji_diff = abs(count_emojis(a_text) - count_emojis(b_text))
        both_url = int(has_url(a_text) and has_url(b_text))
        both_caps = int(is_all_caps(a_text) and is_all_caps(b_text))

        p['features_extra'] = {
            'len_a': len(a_text),
            'len_b': len(b_text),
            'tfidf_jaccard': float(tfidf_j),
            'seq_ratio': float(seq_r),
            'emoji_diff': int(emoji_diff),
            'both_have_url': int(both_url),
            'both_all_caps': int(both_caps)
        }
        enriched.append(p)

    print("[Features] ✅ Enriquecimiento completado.")
    return enriched


# ---------------- Save pairs ----------------
def save_pairs(pairs: List[Dict[str, Any]], out_file: str):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f"[INFO] Saved {len(pairs)} pairs to {out_file}")


# ---------------- Meta helpers ----------------
def read_meta(meta_path: str):
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def write_meta(meta_path: str, chat_files: List[str], total_messages: int, emb_model: str, params: Dict[str, Any]):
    meta = {
        "chat_files": sorted(chat_files),
        "total_messages": total_messages,
        "embedding_model": emb_model,
        "params": params,
        "version": 2
    }
    with open(meta_path, "w", encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def compute_chat_signature(chats: List[Dict[str, Any]]) -> Tuple[List[str], int]:
    chat_files = [os.path.basename(c["_file_path"]) for c in chats]
    total_msgs = sum(len(c.get("messages", [])) for c in chats)
    return sorted(chat_files), total_msgs


# ---------------- Main (CLI) ----------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=str, default='threads_analysis_results/train_chats')
    parser.add_argument('--output', type=str, default='threads_analysis/models/output/pairs_mpnet_hardneg.jsonl')
    parser.add_argument('--emb-model', type=str, default=DEFAULT_EMB_MODEL)
    parser.add_argument('--neg-ratio', type=int, default=2)
    parser.add_argument('--max-prev', type=int, default=10)
    parser.add_argument('--top-k', type=int, default=50)
    parser.add_argument('--take-k', type=int, default=10)
    parser.add_argument('--sim-threshold', type=float, default=0.35)
    parser.add_argument('--force', action='store_true', help='Force recompute even if cache matches')
    args = parser.parse_args()

    # load chats
    chats = load_chats(args.input_dir)
    print(f"[INFO] Loaded {len(chats)} chats")

    chat_files, total_messages = compute_chat_signature(chats)
    out_meta = args.output + ".meta.json"

    params = {
        'neg_ratio': args.neg_ratio,
        'max_prev': args.max_prev,
        'top_k': args.top_k,
        'take_k': args.take_k,
        'sim_threshold': args.sim_threshold
    }

    # check cache meta
    existing_meta = read_meta(out_meta)
    if existing_meta and not args.force:
        if (existing_meta.get("chat_files") == chat_files
                and existing_meta.get("total_messages") == total_messages
                and existing_meta.get("embedding_model") == args.emb_model
                and existing_meta.get("params") == params):
            print(f"[CACHE HIT] Using cached pairs file: {args.output}")
            raise SystemExit(0)
        else:
            print("[INFO] Cache mismatch or different params -> regenerating dataset")

    # build base pairs
    pairs = build_pairs(chats, neg_ratio=args.neg_ratio, max_prev=args.max_prev)
    print(f"[INFO] Built base pairs: {len(pairs)}")

    # prepare tfidf vectorizer on all texts in pairs (for tfidf_jaccard)
    all_texts = []
    for p in pairs:
        all_texts.append(p['a']['text'] or "")
        all_texts.append(p['b']['text'] or "")
    # dedupe to reduce memory/time
    all_texts_unique = list(dict.fromkeys(all_texts))
    print(f"[INFO] Construyendo TF-IDF sobre {len(all_texts_unique)} textos únicos...")
    print("[TF-IDF] Esto puede tardar varios minutos en chats grandes.")
    tfidf_vect, tfidf_matrix = tfidf_jaccard_batch(all_texts_unique)
    print("[TF-IDF] ✅ Vectorización completada.")


    # add hard negatives (uses embedding cache)
    pairs = add_hard_negatives(
        pairs, chats,
        emb_model_name=args.emb_model,
        top_k=args.top_k,
        take_k=args.take_k,
        sim_threshold=args.sim_threshold
    )

    # enrich pairs with extra features
    pairs = enrich_pair_features(pairs, tfidf_vect, tfidf_matrix)

    # save pairs and metadata
    save_pairs(pairs, args.output)
    write_meta(out_meta, chat_files, total_messages, args.emb_model, params)
    print(f"[INFO] Metadata saved: {out_meta}")
