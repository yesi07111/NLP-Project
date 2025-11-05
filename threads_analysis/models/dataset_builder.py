from __future__ import annotations
import os
import json
import math
import random
from glob import glob
from typing import List, Dict, Any

import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

EMB_MODEL = 'all-MiniLM-L6-v2'
CACHE_DIR = "threads_analysis/models/embedding_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Chat loading
# ------------------------------------------------------------
def load_chats(input_dir: str) -> List[Dict[str, Any]]:
    files = glob(os.path.join(input_dir, '*.json'))
    chats = []
    for i, fp in enumerate(files):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_file_path'] = fp
                data['_chat_id'] = i
                chats.append(data)
        except Exception as e:
            print(f"Error leyendo {fp}: {e}")
    return chats


# ------------------------------------------------------------
# Pair building
# ------------------------------------------------------------
def build_pairs(chats: List[Dict[str, Any]], neg_ratio: int = 2, max_prev: int = 10) -> List[Dict[str, Any]]:
    pairs = []
    for chat in chats:
        messages = chat.get('messages', [])
        id2msg = {m['id']: m for m in messages}
        msgs_sorted = sorted(messages, key=lambda m: m.get('date', ''))

        for i, msg in enumerate(msgs_sorted):
            mid = msg.get('id')
            if mid is None:
                continue

            # positives
            reply_id = msg.get('reply_id')
            if reply_id and reply_id in id2msg:
                parent = id2msg[reply_id]
                td = _compute_time_delta_min(parent.get('date'), msg.get('date'))
                pairs.append({
                    'a': {'id': parent.get('id'), 'text': parent.get('text', ''),
                          'sender_id': parent.get('sender_id'), 'date': parent.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''),
                          'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 1,
                    'time_delta_min': td,
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
                    'a': {'id': rand.get('id'), 'text': rand.get('text', ''),
                          'sender_id': rand.get('sender_id'), 'date': rand.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''),
                          'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 0,
                    'time_delta_min': td,
                    'same_author': int(rand.get('sender_id') == msg.get('sender_id')),
                    'chat_id': chat.get('_chat_id')
                })

            # temporal negative
            start = max(0, i - max_prev)
            candidates = [msgs_sorted[j] for j in range(start, i) if msgs_sorted[j].get('id') != reply_id]
            if candidates:
                tmp = random.choice(candidates)
                td = _compute_time_delta_min(tmp.get('date'), msg.get('date'))
                pairs.append({
                    'a': {'id': tmp.get('id'), 'text': tmp.get('text', ''),
                          'sender_id': tmp.get('sender_id'), 'date': tmp.get('date')},
                    'b': {'id': msg.get('id'), 'text': msg.get('text', ''),
                          'sender_id': msg.get('sender_id'), 'date': msg.get('date')},
                    'label': 0,
                    'time_delta_min': td,
                    'same_author': int(tmp.get('sender_id') == msg.get('sender_id')),
                    'chat_id': chat.get('_chat_id')
                })

    return pairs


# ------------------------------------------------------------
# Embedding cache helpers
# ------------------------------------------------------------
def load_cache(chat_id: int):
    emb_path = os.path.join(CACHE_DIR, f"{chat_id}.npy")
    meta_path = os.path.join(CACHE_DIR, f"{chat_id}_meta.json")

    if not os.path.exists(emb_path) or not os.path.exists(meta_path):
        return None

    try:
        embeddings = np.load(emb_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return {
            "_embeddings": embeddings,
            "_texts": meta["texts"],
            "_ids": meta["ids"],
        }
    except:
        return None


def save_cache(chat_id: int, texts, ids, embeddings):
    emb_path = os.path.join(CACHE_DIR, f"{chat_id}.npy")
    meta_path = os.path.join(CACHE_DIR, f"{chat_id}_meta.json")

    np.save(emb_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"texts": texts, "ids": ids}, f, ensure_ascii=False)


# ------------------------------------------------------------
# HARD NEGATIVES + CACHE
# ------------------------------------------------------------
def add_hard_negatives(pairs: List[Dict[str, Any]], chats: List[Dict[str, Any]],
                       model_name: str = EMB_MODEL,
                       top_k: int = 20, take_k: int = 2, sim_threshold: float = 0.5):

    model = SentenceTransformer(model_name)

    # ------ EMBEDDINGS POR CHAT (CON CACHE) ------
    for chat in tqdm(chats, desc='Computing embeddings per chat'):
        cid = chat["_chat_id"]
        cached = load_cache(cid)

        if cached:
            chat["_texts"] = cached["_texts"]
            chat["_embeddings"] = cached["_embeddings"]
            chat["_ids"] = cached["_ids"]
            continue

        msgs = chat.get("messages", [])
        texts = [m.get("text", "") or "" for m in msgs]
        ids = [m.get("id") for m in msgs]

        if not texts:
            chat["_embeddings"] = np.zeros((0, 384))
            chat["_texts"] = []
            chat["_ids"] = []
            continue

        embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        chat["_texts"] = texts
        chat["_embeddings"] = embs
        chat["_ids"] = ids

        save_cache(cid, texts, ids, embs)

    # ------ AGRUPAR POSITIVOS POR CHAT ------
    pos_by_chat = {}
    for p in pairs:
        if p["label"] == 1:
            pos_by_chat.setdefault(p["chat_id"], []).append(p)

    # ------ MINAR HARD NEGATIVES ------
    new_neg = []

    for chat_id, positives in tqdm(pos_by_chat.items(), desc='Mining hard negatives'):
        chat = next((c for c in chats if c["_chat_id"] == chat_id), None)
        if chat is None:
            continue

        embs = chat.get("_embeddings")
        if embs is None or len(embs) == 0:
            continue  # ✅ FIJA EL ERROR AMBIGUO

        texts = chat["_texts"]
        ids = chat["_ids"]
        msgs = chat["messages"]

        for p in positives:
            b_text = p["b"]["text"]

            emb_b = model.encode(b_text, convert_to_numpy=True)
            cosines = util.cos_sim(emb_b, embs)[0]

            top_idx = np.argsort(-cosines)[:top_k]
            taken = 0

            for idx in top_idx:
                idx = int(idx)
                cand_id = ids[idx]
                cand_text = texts[idx]

                if cand_id == p["a"]["id"] or cand_id == p["b"]["id"]:
                    continue

                sim = float(cosines[idx])
                if sim < sim_threshold:
                    continue

                td = _compute_time_delta_min(
                    msgs[idx].get("date"),
                    p["b"]["date"]
                )

                new_neg.append({
                    'a': {'id': cand_id, 'text': cand_text,
                          'sender_id': msgs[idx].get('sender_id'),
                          'date': msgs[idx].get('date')},
                    'b': p["b"],
                    'label': 0,
                    'time_delta_min': td,
                    'same_author': int(msgs[idx].get('sender_id') == p['b']['sender_id']),
                    'chat_id': chat_id,
                    'hard_negative': True
                })

                taken += 1
                if taken >= take_k:
                    break

    print(f"Added {len(new_neg)} hard negatives")
    pairs_ext = pairs + new_neg
    random.shuffle(pairs_ext)
    return pairs_ext


# ------------------------------------------------------------
# Saving
# ------------------------------------------------------------
def save_pairs(pairs: List[Dict[str, Any]], out_file: str):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w', encoding='utf-8') as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + '\n')
    print(f"Saved {len(pairs)} pairs to {out_file}")


# ------------------------------------------------------------
# Cache validation
# ------------------------------------------------------------
def read_metadata(meta_path: str):
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def write_metadata(meta_path: str, chat_files: List[str], total_messages: int, embedding_model: str):
    meta = {
        "chat_files": chat_files,
        "total_messages": total_messages,
        "embedding_model": embedding_model,
        "version": 1
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def compute_chat_signature(chats: List[Dict[str, Any]]):
    chat_files = [os.path.basename(c["_file_path"]) for c in chats]
    total_msgs = sum(len(c.get("messages", [])) for c in chats)
    return sorted(chat_files), total_msgs


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-dir', type=str, default='threads_analysis_results/train_chats')
    parser.add_argument('--output',     type=str, default='threads_analysis/models/output/pairs_with_hard_neg.jsonl')
    parser.add_argument('--neg-ratio', type=int, default=2)
    parser.add_argument('--max-prev',  type=int, default=10)
    parser.add_argument('--top-k',     type=int, default=20)
    parser.add_argument('--take-k',    type=int, default=2)
    parser.add_argument('--sim-threshold', type=float, default=0.5)

    args = parser.parse_args()

    # Load chats
    chats = load_chats(args.input-dir)
    print(f"Loaded {len(chats)} chats")

    chat_files, total_messages = compute_chat_signature(chats)

    # metadata path
    meta_path = args.output + ".meta.json"

    # read existing meta
    meta = read_metadata(meta_path)

    # ---------------- CHECK CACHE ----------------
    if meta:
        if (sorted(meta.get("chat_files", [])) == chat_files and
            meta.get("total_messages") == total_messages and
            meta.get("embedding_model") == EMB_MODEL):

            print(f"[CACHE HIT] Using cached pairs file: {args.output}")
            print("Chats, messages and embedding model match previous run.")
            exit(0)
        else:
            print("[CACHE MISMATCH] Regenerating pairs...")

    # ---------------- BUILD BASE PAIRS ----------------
    pairs = build_pairs(chats, neg_ratio=args.neg_ratio, max_prev=args.max_prev)
    print(f"Built base pairs: {len(pairs)}")

    # ---------------- HARD NEG MINING ----------------
    pairs = add_hard_negatives(
        pairs, chats,
        top_k=args.top_k,
        take_k=args.take_k,
        sim_threshold=args.sim_threshold
    )

    save_pairs(pairs, args.output)

    # ---------------- WRITE META ----------------
    write_metadata(meta_path, chat_files, total_messages, EMB_MODEL)
    print(f"Metadata saved: {meta_path}")

