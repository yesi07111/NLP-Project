# Sistema de Clasificación de Mensajes para Hilos

## **¿Qué hace el proyecto?**
Entrena modelos que deciden si un mensaje es respuesta implícita de otro para construir hilos de conversaciones automáticamente.

## **Arquitectura del Sistema**

### **1. Bi-Encoder (Codificador Dual)**
- **¿Qué es?**: Dos modelos independientes que convierten mensajes en vectores numéricos (embeddings)
- **¿Para qué?**: Calcular similitud entre mensajes A y B mediante comparación de embeddings
- **Ventaja**: Rápido para búsqueda - puedes pre-calcular embeddings
- **Modelos usados**: 
  - `paraphrase-multilingual-mpnet-base-v2` (multilingüe, más preciso)
  - `all-MiniLM-L12-v2` (ligero, más rápido)

### **2. Cross-Encoder (Codificador Cruzado)**
- **¿Qué es?**: Un modelo que procesa AMBOS mensajes juntos [A + SEP + B]
- **¿Para qué?**: Analiza la relación directa entre mensajes con más contexto
- **Ventaja**: Más preciso - ve la interacción completa
- **Desventaja**: Más lento - debe procesar cada par individualmente
- **Modelo**: `ms-marco-MiniLM-L-12-v2` (entrenado para ranking)

### **3. MLP (Red Neuronal Multicapa)**
- **¿Qué es?**: Clasificador que usa los embeddings del Bi-Encoder + características extra
- **¿Para qué?**: Mejorar la decisión combinando embeddings con features contextuales
- **Características que usa**:
  - Embeddings de A y B
  - Diferencia absoluta entre embeddings
  - Producto elemento a elemento
  - Longitudes de texto, similitud TF-IDF, diferencia de emojis
  - Mismo autor, tiempo entre mensajes, etc.

## **Flujo de Procesamiento**

### **Entrenamiento:**
1. **Carga pares** de mensajes etiquetados (es respuesta/no es respuesta)
2. **Divide en folds** manteniendo chats completos juntos
3. **Para cada modelo**:
   - Bi-Encoders: Fine-tune con `MultipleNegativesRankingLoss`
   - Cross-Encoder: Fine-tune como clasificador binario
   - MLP: Entrena sobre embeddings del Bi-Encoder + features

### **Características Extra (Features de Contexto)**
- `len_a`, `len_b`: Longitudes de texto
- `tfidf_jaccard`: Similitud de contenido
- `seq_ratio`: Proximidad en la conversación  
- `emoji_diff`: Diferencia en uso de emojis
- `both_have_url`: Ambos contienen enlaces
- `time_delta_min`: Tiempo entre mensajes
- `same_author`: Mismo remitente

## **Modelos Clásicos (Baselines)**
Se entrenan como comparación:
- **GaussianNB**: Naive Bayes - rápido y simple
- **LogisticRegression**: Regresión logística - buen baseline
- **LightGBM**: Gradient Boosting - alto rendimiento
- **RandomForest**: Ensamble de árboles - robusto

## **¿Por qué esta Arquitectura?**

### **Bi-Encoder + MLP**
- **Velocidad**: Embeddings pre-calculados
- **Precisión**: MLP aprende patrones complejos en las features
- **Flexibilidad**: Puedes añadir fácilmente nuevas características

### **Cross-Encoder**  
- **Máxima precisión**: Ve la interacción completa entre mensajes
- **Contexto rico**: Entiende relaciones complejas

## **Casos de Uso**

### **Bi-Encoder + MLP** → Producción
- Cuando necesitas procesar muchos mensajes rápidamente
- Sistemas en tiempo real

### **Cross-Encoder** → Validación crítica  
- Cuando la precisión es más importante que la velocidad
- Revisión manual o casos edge

## **Métricas de Evaluación**
- **F1-Score**: Balance entre precisión y recall
- **Precisión**: De los que predice como respuesta, cuántos realmente lo son
- **Recall**: De todas las respuestas reales, cuántas detecta
- **AUC-ROC**: Capacidad de distinguir entre clases

### **Ejemplo Simple:**
"Imaginen dos mensajes: 
- A: '¿Vas a venir a la reunión?'
- B: 'Sí, en 5 minutos'

Nuestros modelos analizan no solo el contenido, sino también el tiempo entre mensajes, si es el mismo autor, patrones de escritura, etc., para decidir si B responde a A."