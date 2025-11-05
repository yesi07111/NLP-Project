"""
threads_analysis/models/evaluation.py

Compara el rendimiento del clasificador MLP (usando embeddings + MLP) vs las heurísticas
definidas en ConversationGraphBuilder._calculate_reply_probability.

Requiere que tengas:
- el archivo de pares (JSONL) generado por dataset_builder
- modelos entrenados (pytorch .pth)
- el módulo knowledge_graph con la clase ConversationGraphBuilder accesible

Salida: métricas por fold y comparativa heuristics vs model
"""
from __future__ import annotations
import os
import json
from typing import List, Dict, Any
import numpy as np
from tqdm import tqdm

import torch
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

# importa tu builder de heurísticas
from threads_analysis.knowledge_graph import ConversationGraphBuilder
from threads_analysis.models.siamese_bi_encoder import EmbeddingCache, load_mlp_from_path, make_features, SimpleMLP


def evaluate_model_vs_heuristics(pairs_path: str, model_pth: str, input_dim: int, topk: int = 1):
    # load model
    model = load_mlp_from_path(model_pth, input_dim)
    emb_cache = EmbeddingCache()
    kg = ConversationGraphBuilder()

    ys = []
    yps_model = []
    yps_heur = []

    with open(pairs_path, 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            a = obj['a']
            b = obj['b']
            label = int(obj['label'])

            ys.append(label)

            # model prediction
            emb_a = emb_cache.get(a['text'])
            emb_b = emb_cache.get(b['text'])
            time_delta = float(obj.get('time_delta_min', 99999.0))
            same_author = int(obj.get('same_author', 0))
            feat = make_features(emb_a, emb_b, time_delta, same_author)
            X = torch.from_numpy(feat).unsqueeze(0)
            with torch.no_grad():
                score_model = float(model(X.to('cpu')).cpu().numpy().squeeze())
            yps_model.append(score_model)

            # heuristics
            try:
                score_heur = kg._calculate_reply_probability(a, b)
            except Exception:
                score_heur = 0.0
            yps_heur.append(float(score_heur))

    # metrics
    auc_model = roc_auc_score(ys, yps_model)
    auc_heur = roc_auc_score(ys, yps_heur)

    p_m, r_m, f_m, _ = precision_recall_fscore_support(ys, [1 if p>=0.5 else 0 for p in yps_model], average='binary', zero_division=0)
    p_h, r_h, f_h, _ = precision_recall_fscore_support(ys, [1 if p>=0.5 else 0 for p in yps_heur], average='binary', zero_division=0)

    print('Model: AUC={:.4f} P={:.4f} R={:.4f} F1={:.4f}'.format(auc_model, p_m, r_m, f_m))
    print('Heur : AUC={:.4f} P={:.4f} R={:.4f} F1={:.4f}'.format(auc_heur, p_h, r_h, f_h))

    return {
        'model': {'auc': auc_model, 'p': p_m, 'r': r_m, 'f1': f_m},
        'heuristics': {'auc': auc_heur, 'p': p_h, 'r': r_h, 'f1': f_h}
    }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pairs', type=str, default='threads_analysis/models/output/pairs_with_hard_neg.jsonl')
    parser.add_argument('--model-pth', type=str, required=True)
    parser.add_argument('--input-dim', type=int, required=True)
    args = parser.parse_args()

    evaluate_model_vs_heuristics(args.pairs, args.model_pth, args.input_dim)
