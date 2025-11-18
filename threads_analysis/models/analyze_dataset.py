import json
import os
from collections import defaultdict

def load_pairs(path):
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
    except:
        try:
            with open(".\\threads_analysis\\models\\output\\" + path, "r", encoding="utf-8") as f:
                for line in f:
                    rows.append(json.loads(line))
        except:
            print("ERROR: Camino incorrecto. Revisar desde donde se llama al script.")
    return rows


def is_hard_negative(r):
    """
    Tus hard negatives NO usan label = -1, sino:
        label = 0
        hard_negative = true
    """
    return r.get("label", 0) == 0 and r.get("hard_negative") is True


def analyze_dataset(path, output_json=".\\threads_analysis\\models\\output\\dataset_stats.json"):
    rows = load_pairs(path)
    total = len(rows)

    stats = {
        "total_examples": total,
        "labels": {"positive": 0, "negative": 0, "hard_negative": 0},
        "chats": {},
        "global_ratio": {},
    }

    # ---- CONTADORES GLOBALES ----
    for r in rows:
        label = r.get("label", 0)

        if label == 1:
            stats["labels"]["positive"] += 1

        elif is_hard_negative(r):
            stats["labels"]["hard_negative"] += 1

        else:
            stats["labels"]["negative"] += 1

    # ---- POR CHAT ----
    by_chat = defaultdict(list)
    for r in rows:
        cid = r.get("chat_id", -1)
        by_chat[cid].append(r)

    chat_stats = {}
    for cid, items in by_chat.items():

        pos = sum(1 for r in items if r.get("label") == 1)
        hard = sum(1 for r in items if is_hard_negative(r))
        neg = len(items) - pos - hard

        chat_stats[cid] = {
            "total": len(items),
            "positive": pos,
            "negative": neg,
            "hard_negative": hard,
            "pos_ratio": pos / len(items),
            "neg_ratio": neg / len(items),
            "hard_ratio": hard / len(items)
        }

    stats["chats"] = chat_stats

    # ---- RATIOS GLOBALES ----
    stats["global_ratio"] = {
        "positive": stats["labels"]["positive"] / total,
        "negative": stats["labels"]["negative"] / total,
        "hard_negative": stats["labels"]["hard_negative"] / total,
    }

    # ---- GUARDAR ----
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"[OK] Dataset stats saved → {output_json}")


if __name__ == "__main__":
    analyze_dataset("pairs_with_hard_neg.jsonl")
