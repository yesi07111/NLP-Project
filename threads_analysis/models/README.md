# Pipeline de Entrenamiento y Evaluación de Hilos (Threads Analysis)

Este proyecto implementa un pipeline completo para:

✅ Construir dataset de entrenamiento a partir de chats de Telegram
✅ Generar *hard negatives* mediante embeddings
✅ Entrenar un modelo **Siamese / Bi-Encoder + MLP** con **K-Folds**
✅ Exportar el clasificador a ONNX
✅ Evaluar contra heurísticas existentes (knowledge_graph)
✅ Registrar todo el proceso con logs en color y barra de progreso global
✅ Detectar automáticamente el mejor *fold* según F1

---

## 📁 Estructura

```
threads_analysis/
└── models/
    ├── dataset_builder.py
    ├── siamese_bi_encoder.py
    ├── evaluation.py
    ├── onnx_export.py
    ├── pipeline_runner.py  ← (ejecuta todo el pipeline)
    └── output/
        ├── pairs_with_hard_neg.jsonl
        ├── fold_*/
        └── siamese_mlp.onnx
```

---

## ▶️ Cómo ejecutar todo

Simplemente corre:

```
python threads_analysis/models/pipeline_runner.py
```

Eso ejecutará automáticamente:

1. **Dataset Builder**
2. **Hard Negative Extraction**
3. **K-Fold Training**
4. **Selection del mejor fold (según F1)**
5. **Exportación ONNX del clasificador**
6. **Evaluación comparativa**

Todo con logs coloridos y barra de progreso global.

---

## ✅ Requisitos

Instalar dependencias:

```
pip install sentence-transformers torch scikit-learn numpy scipy tqdm pandas rich onnx onnxruntime
python -m spacy download es_core_news_md
```

---

## 📦 Entrada esperada

Debes colocar tus chats en:

```
threads_analysis_results/train_chats/*.json
```

Con la estructura:

```
{
  "metadata": {...},
  "messages": [
      {
        "id": 123,
        "text": "mensaje...",
        "reply_id": 122,
        "date": "2025-10-01T10:00:00",
        ...
      }
  ]
}
```

---

## 🎯 Salidas principales

### ✅ `pairs_with_hard_neg.jsonl`

Dataset completo ya construido.

### ✅ `fold_*/model.pth`

Almacenamiento de cada fold de entrenamiento.

### ✅ `best_model.pth`

El mejor fold automáticamente seleccionado.

### ✅ `siamese_mlp.onnx`

Clasificador exportado para inferencia sin PyTorch.

### ✅ `evaluation_report.json`

Evaluación completa comparativa.

---

## 🧠 ¿Cómo funciona el modelo?

1. **SBERT / MiniLM** genera embeddings para cada mensaje.
2. Para cada par (A,B):

   * concat(embA, embB, |A-B|, A*B)
   * * features temporales (Δt) y del autor.
3. Un MLP ligero predice probabilidad de que **A responda a B**.
4. K-fold garantiza que no haya fuga entre chats.
5. Se selecciona el fold con mejor **F1-validation**.

---

## 📊 Evaluación

El pipeline evalúa:

* F1
* Precisión
* Recall
* AUC
* Comparación con heurísticas existentes

---

## 🚀 Mejoras futuras

* Soporte para cuantización ONNX (int8)
* Exportar también el encoder a ONNX
* Dashboard interactivo con Streamlit

