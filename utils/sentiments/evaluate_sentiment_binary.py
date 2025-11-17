import csv
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from utils.sentiments.sentiment_rules import analyze_sentiment
import time
from typing import Optional, Callable, List, Any

def load_test_data(
    filepath: str,
    text_col: str = 'texto',
    label_col: str = 'sentimiento',
    label_map_fn: Optional[Callable[[Any], int]] = None,
):
    """Load test data from CSV file.

    Args:
        filepath: path to csv file
        text_col: column name containing text
        label_col: column name containing the ground-truth label
        label_map_fn: optional function(raw_value) -> 0|1 to convert label values to binary

    Returns:
        texts, true_labels (both aligned lists)
    """
    texts: List[str] = []
    true_labels: List[int] = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # get text
            text = row.get(text_col, '')
            texts.append(text)

            # get raw label and convert
            raw = row.get(label_col, '')
            if label_map_fn is not None:
                try:
                    lbl = int(label_map_fn(raw))
                    lbl = 1 if lbl == 1 else 0
                except Exception:
                    # fallback conservative: negative
                    lbl = 0
            else:
                # default behavior: treat numeric 1 as positive, else negative
                try:
                    num = float(str(raw).strip())
                    lbl = 1 if int(num) == 1 else 0
                except Exception:
                    sval = str(raw).strip().lower()
                    lbl = 1 if sval in ('1', 'true', 'positivo', 'pos', 'p', 'yes', 'y') else 0

            true_labels.append(lbl)

    return texts, true_labels

def load_existing_results(output_file: str, text_col: str = 'texto', pred_col: str = 'prediccion'):
    """Load existing results from file if it exists.

    Returns lists (texts, predictions) or empty lists if file not present or columns missing.
    """
    try:
        df = pd.read_csv(output_file)
        return df[text_col].tolist(), df[pred_col].tolist()
    except (FileNotFoundError, KeyError):
        return [], []

def save_results_incrementally(
    text,
    prediction,
    output_file: str,
    text_col: str = 'texto',
    pred_col: str = 'prediccion',
):
    """Save a single prediction result to the output file.

    Writes header if file does not exist. Column names configurable to allow using different CSV schemas.
    """
    import os
    file_exists = os.path.isfile(output_file)

    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([text_col, pred_col])
        writer.writerow([text, prediction])

def predict_sentiment(
    texts,
    output_file: str = 'resultados_sentimiento_temp.csv',
    retry_forever: bool = True,
    max_retries: Optional[int] = None,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    output_text_col: str = 'texto',
    output_pred_col: str = 'prediccion',
):
    """Predict sentiment for a list of texts using binary classification.
    
    Args:
        texts: List of texts to analyze
        output_file: File to save incremental results
        
    Returns:
        List of predicted labels (0 for negative, 1 for positive)
    """
    # Load existing results
    processed_texts, pred_labels = load_existing_results(output_file, text_col=output_text_col, pred_col=output_pred_col)
    
    # Skip already processed texts
    start_idx = len(processed_texts)
    
    print(f"Found {start_idx} previously processed texts. Resuming from index {start_idx}...")
    
    def _is_connection_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return isinstance(exc, (ConnectionError, OSError, IOError)) or 'connection' in msg

    # Process remaining texts
    for i in range(start_idx, len(texts)):
        text = texts[i]

        attempt = 0
        backoff = initial_backoff

        while True:
            try:
                result = analyze_sentiment(text)
                # Binary classification: positive if score > 0, negative otherwise
                pred = 1 if result['score'] > 0 else 0
                pred_labels.append(pred)

                # Save result immediately
                save_results_incrementally(text, pred, output_file, text_col=output_text_col, pred_col=output_pred_col)
                break

            except KeyboardInterrupt:
                # Allow user to cancel
                raise
            except Exception as e:
                # Only retry on connection-related problems
                if _is_connection_error(e):
                    attempt += 1
                    will_retry = retry_forever or (max_retries is not None and attempt <= max_retries)
                    print(f"[Warning] Error de conexión en el análisis (texto index {i}): {e}")
                    if not will_retry:
                        print(f"[Error] Se alcanzó el máximo de reintentos ({max_retries}). Saltando este texto.")
                        pred_labels.append(None)
                        break

                    # Sleep with exponential backoff
                    sleep_time = min(backoff, max_backoff)
                    print(f"Reintentando en {sleep_time:.1f}s (intento {attempt})...")
                    try:
                        time.sleep(sleep_time)
                    except KeyboardInterrupt:
                        raise
                    backoff *= 2
                    continue
                else:
                    # Non-connection error: log and append None to keep indices aligned
                    print(f"[Error] Error al analizar el texto index {i}: {e}")
                    # pred_labels.append(None)
                    # break

    return pred_labels

def evaluate(true_labels, pred_labels):
    """Calculate and return evaluation metrics for binary classification.

    true_labels may already be 0/1 or other values; we convert defensively to binary using the rule:
      - if label == 1 -> 1
      - else -> 0

    Returns a dict with accuracy, precision, recall, f1, report and confusion_matrix.
    """
    # Defensive conversion to binary
    true_labels_binary = [1 if (label == 1 or str(label).strip() == '1') else 0 for label in true_labels]

    # Ensure lengths match
    if len(true_labels_binary) != len(pred_labels):
        raise ValueError('Length mismatch between true labels and predictions')

    # Calculate metrics
    accuracy = accuracy_score(true_labels_binary, pred_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels_binary, pred_labels, average='weighted', zero_division=0
    )

    # Get classification report for present classes only (avoid mismatch when a class is missing)
    present_labels = sorted(set(true_labels_binary) | set(pred_labels))
    label_name_map = {0: 'negativo', 1: 'positivo'}
    target_names = [label_name_map.get(l, str(l)) for l in present_labels]

    report = classification_report(
        true_labels_binary,
        pred_labels,
        labels=present_labels,
        target_names=target_names,
        zero_division=0,
    )

    # Create confusion matrix
    cm = confusion_matrix(true_labels_binary, pred_labels, labels=[0, 1])

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'report': report,
        'confusion_matrix': cm,
    }

def plot_confusion_matrix(cm, labels):
    """Plot confusion matrix."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, 
        annot=True, 
        fmt='d', 
        cmap='Blues',
        xticklabels=labels,
        yticklabels=labels
    )
    plt.title('Matriz de Confusión')
    plt.ylabel('Etiqueta Verdadera')
    plt.xlabel('Predicción')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    plt.close()

def main():
    # Configuration
    test_file = input("Ruta del dataset: ")
    temp_output = input("Archivo temporal de resultados (default 'resultados_sentimiento_temp.csv'): ") or 'resultados_sentimiento_temp.csv'
    final_output = input("Archivo final de resultados (default 'resultados_sentimiento_final.csv'): ") or 'resultados_sentimiento_final.csv'

    # Ask user for column names in the dataset
    print("\nEspecifica las columnas del dataset:")
    text_col = input("Nombre de la columna que contiene el texto (default 'texto'): ") or 'texto'
    label_col = input("Nombre de la columna que contiene la etiqueta real (default 'sentimiento'): ") or 'sentimiento'

    # Ask whether to apply a mapping to labels (e.g., convert 1-10 scores to binary)
    label_map_fn = None
    convert_labels = input("¿Necesita convertir las etiquetas del dataset a binario (0/1)? [y/N]: ").strip().lower() or 'n'
    if convert_labels == 'y':
        method = input("Método de conversión: 'threshold' para umbral numérico, o 'none' para proporcionar expresión (default 'threshold'): ") or 'threshold'
        if method == 'threshold':
            th = input("Ingrese el umbral numérico (por ejemplo 6 -> etiquetas >=6 serán positivas): ")
            try:
                th_val = float(th)
            except Exception:
                print("Umbral no válido, se usará 6 por defecto.")
                th_val = 6.0

            def _map_threshold(raw):
                try:
                    return 1 if float(str(raw).strip()) >= th_val else 0
                except Exception:
                    return 0

            label_map_fn = _map_threshold
        else:
            # For now, no interactive arbitrary lambda; user can later edit this file to provide a custom mapping
            print("No se proporcionó método 'custom' interactivo. Si necesita una conversión compleja, modifique el código y pase `label_map_fn`.")

    # Optional: columns used in the incremental output file
    print("\nColumnas para el archivo de resultados incrementales:")
    out_text_col = input("Columna texto en archivo temporal (default 'texto'): ") or 'texto'
    out_pred_col = input("Columna predicción en archivo temporal (default 'prediccion'): ") or 'prediccion'

    # Load test data
    print("\nCargando datos de prueba...")
    texts, true_labels = load_test_data(test_file, text_col=text_col, label_col=label_col, label_map_fn=label_map_fn)

    # Make predictions with incremental saving
    print("\nIniciando predicciones (se guardarán incrementalmente)...")
    pred_labels = predict_sentiment(texts, temp_output, output_text_col=out_text_col, output_pred_col=out_pred_col)
    
    # Filter out any None values from failed predictions
    valid_indices = [i for i, pred in enumerate(pred_labels) if pred is not None]
    valid_texts = [texts[i] for i in valid_indices]
    valid_true_labels = [true_labels[i] for i in valid_indices]
    valid_pred_labels = [pred_labels[i] for i in valid_indices]
    
    # Save final results with true labels
    final_results = pd.DataFrame({
        'texto': valid_texts,
        'etiqueta_real': valid_true_labels,
        'prediccion': valid_pred_labels,
    })
    final_results.to_csv(final_output, index=False, encoding='utf-8')
    
    # Only evaluate if we have valid predictions
    if valid_pred_labels:
        print("\nEvaluando resultados...")
        metrics = evaluate(valid_true_labels, valid_pred_labels)
        
        # Print results
        print("\nMétricas de evaluación:")
        print(f"Exactitud (Accuracy): {metrics['accuracy']:.4f}")
        print(f"Precisión (Precision): {metrics['precision']:.4f}")
        print(f"Sensibilidad (Recall): {metrics['recall']:.4f}")
        print(f"F1-Score: {metrics['f1']:.4f}")
        
        print("\nReporte de clasificación:")
        print(metrics['report'])
        
        # Plot confusion matrix
        plot_confusion_matrix(metrics['confusion_matrix'], ['Negativo', 'Positivo'])
        print("\nMatriz de confusión guardada como 'confusion_matrix.png'")
    
    print(f"\nResultados finales guardados en '{final_output}'")
    print("Proceso completado.")

if __name__ == "__main__":
    main()
