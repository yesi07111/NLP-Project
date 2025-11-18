# 🚀 Pipeline de Detección de Hilos en Conversaciones

Un sistema avanzado para detectar relaciones de respuesta implícitas entre mensajes usando **tres modelos especializados** entrenados con datos enriquecidos de chats de Telegram.

---

## 📊 **Arquitectura del Sistema**

### 🎯 **Tres Modelos Especializados**

#### 1. **Bi-Encoder A** 🏎️
- **Modelo**: `paraphrase-multilingual-mpnet-base-v2`
- **Fortaleza**: Excelente para comprensión multilingüe y semántica profunda
- **Uso**: Genera embeddings de alta calidad para comparación semántica

#### 2. **Bi-Encoder B** ⚡
- **Modelo**: `sentence-transformers/all-MiniLM-L12-v2`
- **Fortaleza**: Rápido y eficiente, ideal para procesamiento en tiempo real
- **Uso**: Balance perfecto entre velocidad y precisión

#### 3. **Cross-Encoder** 🎯
- **Modelo**: `cross-encoder/ms-marco-MiniLM-L-12-v2`
- **Fortaleza**: Máxima precisión en detección de relaciones contextuales
- **Uso**: Análisis profundo de pares de mensajes para casos difíciles

---

Perfecto. Te dejo **el README actualizado**, con:

### ✔ Sección antigua reemplazada por la nueva explicación del sistema automático de selección de folds

### ✔ Inclusión de la explicación de los **modelos clásicos** (GaussianNB, LogisticRegression, LightGBM, RandomForest)

### ✔ Integrado sin alterar la estructura del documento

### ✔ Estilo consistente con el resto del README

---

# 🚀 Pipeline de Detección de Hilos en Conversaciones (README Actualizado)

Un sistema avanzado para detectar relaciones de respuesta implícitas entre mensajes usando **modelos neuronales**, **modelos clásicos**, **selección inteligente de folds**, y **datos enriquecidos** a gran escala.

---

## 📊 **Arquitectura del Sistema**

### 🎯 **Modelos Basados en Deep Learning**

#### 1. **Bi-Encoder A** 🏎️

* **Modelo**: `paraphrase-multilingual-mpnet-base-v2`
* **Uso**: Embeddings de semántica profunda
* **Fortaleza**: Excelente rendimiento multilingüe

#### 2. **Bi-Encoder B** ⚡

* **Modelo**: `sentence-transformers/all-MiniLM-L12-v2`
* **Uso**: Velocidad máxima con buena precisión
* **Fortaleza**: Ideal para despliegue rápido

#### 3. **Cross-Encoder** 🎯

* **Modelo**: `cross-encoder/ms-marco-MiniLM-L-12-v2`
* **Uso**: Clasificación contextual fina
* **Fortaleza**: Máxima precisión en casos ambiguos

---

## 🧮 **Modelos Clásicos Incluidos** 

Además de los modelos neuronales, el pipeline ahora entrena **modelos clásicos de Machine Learning** basados en las features extraídas del dataset:

| Modelo                              | Motivo                                | Ventajas                                |
| ----------------------------------- | ------------------------------------- | --------------------------------------- |
| **GaussianNB**                      | Modelo muy ligero                     | Rápido, base line simple                |
| **Logistic Regression (L2 + SAGA)** | Clasificador lineal robusto           | Estable, rápido, alta interpretabilidad |
| **LightGBM** (si está disponible)   | Ensamble basado en árboles optimizado | Muy fuerte en features tabulares        |
| **Random Forest**                   | Modelo por consenso                   | Buen rendimiento y robusto al ruido     |

Cada uno se entrena en cada fold y se **guarda su progreso inmediatamente** en:

```
fold_X/classical_training_progress.json
```

Los modelos son exportados como:

```
gaussian_nb.joblib
logistic_regression.joblib
lightgbm.joblib
random_forest.joblib
```

Los resultados clásicos **también contribuyen a la comparación global del sistema**.

---

# 📘 Sistema Automático de Selección de Folds en el Entrenamiento 

Este módulo decide automáticamente **qué esquema de validación cruzada** usar:

* **KFold tradicional**
* **GroupKFold**
* **Custom Stratified-Group-KFold** (avanzado)

La elección se basa en información generada en:

```
threads_analysis/models/output/dataset_stats.json
```

---

## 📊 ¿Qué contiene `dataset_stats.json`?

El **Dataset Analyzer** calcula:

* Número total de ejemplos
* Conteos por clase globales y por chat
* Ratios:

  * `pos_ratio`
  * `neg_ratio`
  * `hard_ratio`
* Tamaño por cada `chat_id`

Ejemplo:

```json
{
  "total_examples": 2894036,
  "labels": {...},
  "chats": {
    "13": {
      "total": 764518,
      "positive": 46205,
      "negative": 256962,
      "hard_negative": 461351,
      "pos_ratio": 0.0604,
      "neg_ratio": 0.3361,
      "hard_ratio": 0.6034
    }
  },
  "global_ratio": {
    "positive": 0.0562,
    "negative": 0.3823,
    "hard_negative": 0.5614
  }
}
```

---

# 🧠 Lógica Inteligente de Selección de Folds

### 📌 **Caso 1 — KFold simple**

Se usa cuando:

* No existe `chat_id`
* O solo existe un único grupo

### 📌 **Caso 2 — GroupKFold**

Se usa cuando:

* Hay suficientes chats (`n_groups >= 3 * n_splits`)
* La distribución entre chats es relativamente homogénea

Evita mezclar ejemplos de un mismo chat entre train/val.

### 📌 **Caso 3 — Custom Stratified-Group-KFold**

Se usa cuando:

* Hay pocos chats
* **Pero sus distribuciones son extremadamente diferentes**

#### ¿Cómo funciona?

1. Para cada chat → vector de perfil:

   ```
   [pos_ratio, neg_ratio, hard_ratio]
   ```
2. Se aplica **K-Means** → 1 cluster por fold
3. Cada cluster representa un “tipo de chat”
4. Se garantiza que los folds tengan **ratios de clases equilibrados**

Este método es crucial cuando algunos chats son gigantes y otros pequeños, o cuando sus ratios varían enormemente.

---

# 🧩 Beneficios

* Evita fugas entre train/val
* Mantiene balance entre clases
* Reduce overfitting
* Funciona incluso con datasets muy desbalanceados
* 100% automático según el dataset real

---

# 🤖 Entrenamiento de Modelos

Ahora incluye:

### ✔ 3 Modelos neuronales

### ✔ 4 Modelos clásicos

### ✔ Selección inteligente de folds

### ✔ Reportes completos por fold

---

# 📤 Exportación de Modelos

Deep Learning → ONNX
Clásicos → `.joblib`

---

# 🧪 Evaluación

La evaluación ahora incluye:

1. Heurísticas
2. Bi-Encoder A
3. Bi-Encoder B
4. Cross-Encoder
5. **GaussianNB**
6. **Logistic Regression**
7. **LightGBM** 
8. **RandomForest**

Cada uno con:

* F1
* Precision
* Recall
* AUC (modelos neuronales)

El reporte incluye todo:

```
evaluation_report.json
```

## 🏗️ **Pipeline Completo**

### 🔄 **Flujo de Procesamiento**

```mermaid
graph TD
    A[📁 Chats Telegram] --> B[🛠️ Dataset Builder]
    B --> C[📊 Dataset Enriquecido]
    C --> D[🤖 Triple Model Trainer]
    D --> E[📈 K-Fold Training]
    E --> F[🏆 Mejor Modelo]
    F --> G[📤 Exportación ONNX]
    G --> H[🧪 Evaluación]
    H --> I[📋 Reporte Final]
```

---

## 📁 **Estructura del Proyecto**

```
threads_analysis/
├── main.py                         # 🏠 Punto de entrada para procesar chats y crear su grafo
├── knowledge_graph.py              # 🔍 Construcción del grafo + heurísticas reply implícito
├── models/
│   ├── dataset_builder.py          # 🏗️ Construye dataset con hard negatives
│   ├── model_trainer.py     # 🤖 Entrena los modelos
│   ├── onnx_export.py              # 📤 Exporta modelos a ONNX
│   ├── evaluation.py               # 🧪 Evalúa vs heurísticas
│   ├── pipeline_runner.py          # 🚀 Ejecuta TODO el pipeline
│   ├── embeddings_cache/
│   │   └── sentence-transformers__all-mpnet-base-v2/
│   │       ├── 0_meta.json         # 📋 Metadatos del chat 0
│   │       ├── 0.npy               # 💾 Embeddings del chat 0
│   │       ├── 1_meta.json         # 📋 Metadatos del chat 1
│   │       ├── 1.npy               # 💾 Embeddings del chat 1
│   │       ├── 2_meta.json         # 📋 Metadatos del chat 2
│   │       ├── 2.npy               # 💾 Embeddings del chat 2
│   │       └── ...                 # 📊 Más chats numerados
│   └── output/                     # 📦 Salidas del pipeline
│       ├── pairs_with_hard_neg.jsonl
│       ├── pairs_with_hard_neg.jsonl.meta.json  # 📋 Metadatos del dataset
│       ├── training_summary.json   # 📊 Resumen entrenamiento
│       ├── fold_0/                 # 🎯 Modelos del fold 0
│       │   ├── bi_encoder_A_fold0.pth
│       │   ├── bi_encoder_B_fold0.pth
│       │   └── cross_encoder_fold0.pth
│       ├── fold_1/                 # 🎯 Modelos del fold 1
│       │   ├── bi_encoder_A_fold1.pth
│       │   └── ...
│       ├── bi_encoder_A.onnx       # 📤 Modelo exportado
│       ├── bi_encoder_B.onnx       # 📤 Modelo exportado
│       ├── cross_encoder.onnx      # 📤 Modelo exportado
│       └── evaluation_report.json  # 📈 Resultados evaluación
└── threads_analysis_results/       # 📥 Entrada de datos
    └── train_chats/
        ├── chat_1.json             # 💬 Chat de entrenamiento 1
        ├── chat_2.json             # 💬 Chat de entrenamiento 2
        └── ...                     # 💬 Más chats
```

## 🎯 **Cómo Ejecutar**

### 🚀 **Ejecutar Todo el Pipeline**
```bash
python threads_analysis/models/pipeline_runner.py
```

### ⚙️ **Parámetros Opcionales**
```bash
python threads_analysis/models/pipeline_runner.py \
    --train-chats "ruta/chats" \
    --output-dir "ruta/salida" \
    --epochs 4 \
    --batch-size 32 \
    --folds 5
```

---

## 🏗️ **Construcción del Dataset**

### 📊 **Proceso de Enriquecimiento**

#### 🔍 **Detección de Pares Reales**
```python
# Para cada mensaje con reply_id válido
par_positivo = {
    'a': mensaje_padre,      # El mensaje referenciado
    'b': mensaje_actual,     # La respuesta
    'label': 1,              # ✅ Es una respuesta real
    'time_delta_min': 0.083, # 5 segundos en minutos
    'same_author': 0         # ¿Mismo remitente?
}
```

#### 🎯 **Generación de Hard Negatives**
```python
# Busca mensajes SEMÁNTICAMENTE similares pero NO relacionados
hard_negative = {
    'a': mensaje_similar,    # Parecido semántico al mensaje real
    'b': mensaje_actual,
    'label': 0,              # ❌ NO es respuesta
    'hard_negative': True    # ⚠️ Ejemplo difícil
}
```

#### 📈 **Características Extraídas**
- **`tfidf_jaccard`**: Similitud de temas usando TF-IDF
- **`seq_ratio`**: Similitud textual directa
- **`emoji_diff`**: Diferencia en uso de emojis
- **`both_have_url`**: Ambos contienen enlaces
- **`both_all_caps`**: Ambos usan mayúsculas
- **`time_delta_min`**: Distancia temporal

---

## 🤖 **Entrenamiento de Modelos**

### 🎪 **K-Fold Cross Validation**
```python
# Entrenamiento robusto con validación cruzada
for fold in range(5):  # 5 folds
    # 1. Fine-tune bi-encoders con MultipleNegativesRankingLoss
    # 2. Entrenar MLP classifier sobre embeddings
    # 3. Entrenar cross-encoder como clasificador binario
    # 4. Validar y guardar métricas
```

### 🏆 **Selección del Mejor Modelo**
- **Métrica principal**: F1-Score en validación
- **Selección automática**: Mejor fold por modelo
- **Backup**: Todos los folds guardados

---

## 📤 **Exportación ONNX**

### 🤔 **¿Qué es ONNX?**
**ONNX** (Open Neural Network Exchange) es un formato estándar para modelos de machine learning que permite:

### 🎯 **Ventajas**
- **🚀 Inferencia más rápida**: Optimizado para producción
- **🔧 Interoperabilidad**: Funciona en múltiples frameworks
- **📱 Multiplataforma**: CPU, GPU, móviles, edge devices
- **⚡ Sin dependencias**: No requiere PyTorch/TensorFlow en producción

### 🔄 **Proceso de Exportación**
```python
# Convierte modelo PyTorch a ONNX
torch.onnx.export(
    model,                      # Modelo entrenado
    dummy_input,               # Input de ejemplo
    "modelo.onnx",             # Archivo de salida
    opset_version=11,          # Versión de operadores
    input_names=['input'],     # Nombres de inputs
    output_names=['output']    # Nombres de outputs
)
```

### 🎯 **¿Por qué Exportar a ONNX?**
1. **🚀 Despliegue en producción** sin dependencias pesadas
2. **📱 Ejecución en dispositivos** con recursos limitados
3. **🔧 Compatibilidad** con múltiples lenguajes (C++, Java, C#)
4. **⚡ Optimizaciones** específicas por hardware

---

## 🧪 **Evaluación del Sistema**

### 📊 **Métricas de Evaluación**
- **AUC**: Área bajo la curva ROC
- **Precisión**: Exactitud en predicciones positivas
- **Recall**: Capacidad de detectar todos los positivos
- **F1-Score**: Balance entre precisión y recall

### 🔍 **Comparativa Completa**
El sistema evalúa **4 enfoques**:

1. **🔍 Heurísticas Tradicionales**: Reglas basadas en knowledge graph
2. **🏎️ Bi-Encoder A**: MPNet multilingüe para semántica profunda
3. **⚡ Bi-Encoder B**: MiniLM para velocidad y eficiencia
4. **🎯 Cross-Encoder**: Máxima precisión contextual

### 📈 **Reporte de Evaluación**
```json
{
  "heuristics": {"auc": 0.75, "f1": 0.68},
  "bi_encoder_A": {"auc": 0.89, "f1": 0.82},
  "bi_encoder_B": {"auc": 0.87, "f1": 0.80},
  "cross_encoder": {"auc": 0.92, "f1": 0.85}
}
```

---

## 📦 **Salidas del Pipeline**

### ✅ **Archivos Generados**
- **`pairs_with_hard_neg.jsonl`**: Dataset completo enriquecido
- **`training_summary.json`**: Resumen de entrenamiento y mejores folds
- **`fold_*/model.pth`**: Modelos entrenados por cada fold
- **`*.onnx`**: Modelos exportados para producción
- **`evaluation_report.json`**: Comparativa completa de rendimiento

### 🎯 **Modelos ONNX Exportados**
1. **`bi_encoder_A.onnx`** - MPNet multilingüe optimizado
2. **`bi_encoder_B.onnx`** - MiniLM rápido y eficiente
3. **`cross_encoder.onnx`** - Máxima precisión contextual

---

## ⚙️ **Requisitos del Sistema**

### 📦 **Dependencias**
```bash
pip install sentence-transformers torch scikit-learn numpy scipy tqdm pandas rich onnx onnxruntime
python -m spacy download es_core_news_md
```

### 📁 **Estructura de Entrada**
Coloca tus chats en:
```
threads_analysis_results/train_chats/*.json
```

Ejemplo de estructura:
```json
{
  "metadata": {"chat_id": "grupo_1"},
  "messages": [
    {
      "id": 123,
      "text": "¿Alguien quiere pizza?",
      "reply_id": null,
      "date": "2023-10-01T10:00:00",
      "sender_id": "user1"
    }
  ]
}
```

---

## 🎯 **Casos de Uso**

### 💬 **Detección de Replies Implícitos**
```
Usuario A: "¿Alguien quiere pizza?"          🎯
Usuario B: "¡Yo sí! Con pepperoni"           ✅ Respuesta detectada
Usuario C: "Acabo de almorzar"               ✅ Respuesta detectada  
Usuario D: "Hoy hace buen día"               ❌ No relacionado
```

### 🔍 **Aplicaciones**
- **📊 Análisis de conversaciones**: Entender flujos de discusión
- **🤖 Chatbots**: Mejorar comprensión contextual
- **📈 Business Intelligence**: Analizar patrones de comunicación
- **🔍 Moderación**: Detectar hilos de conversación problemáticos

---

## 💡 **¿Por qué este Enfoque?**

### 🏆 **Ventajas Clave**
- **🎯 Precisión Máxima**: Combinación de 3 modelos especializados
- **🚀 Velocidad de Inferencia**: ONNX optimizado para producción
- **🔍 Robustez**: Hard negatives + K-fold validation
- **📊 Evaluación Completa**: Comparativa contra heurísticas existentes

### ⚡ **Ready for Production**
Los modelos ONNX exportados están listos para:
- **🎯 Despliegue inmediato** en entornos productivos
- **🚀 Inferencia rápida** sin dependencias de PyTorch
- **📱 Ejecución eficiente** en múltiples plataformas

---

**¿Listo para detectar relaciones en tus conversaciones? ¡Ejecuta el pipeline y descubre insights ocultos! ...Solo si tienes 2 días completos uno para hacer embeddings y otro para entrenar (sin gpu puede que más) y al menos estar dispuesto y con condiciones para bajar > 1.5 GB de espacio total que ocupan los modelos (sin contar los embbedings o el dataset que puede llegar a pesar mucho, con los datos usados peso ~1.4 GB) En fin, que divertidoooo... no me dolió en los datos móviles ni nada jaja... jaja... jaaaaaaa** 🥲🎉