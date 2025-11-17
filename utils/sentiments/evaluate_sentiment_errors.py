import csv
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
from utils.sentiments.sentiment_rules import analyze_sentiment

def load_test_data(filepath):
    """Load test data from CSV file."""
    texts = []
    true_labels = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row['texto'])
            true_labels.append(int(row['sentimiento']))
            
    return texts, true_labels


def predict_sentiment(texts):
    """Predict sentiment for each text and return full results."""
    results = []

    for text in texts:
        analysis = analyze_sentiment(text, debug=True)
        score = analysis['score']
        pred = 1 if score > 0 else 0

        # Flatten rules from all sentences
        all_rules = []
        for s in analysis["details"]:
            all_rules.extend(s["rules"])

        results.append({
            "texto": text,
            "prediccion": pred,
            "score": score,
            "rules": ";".join(all_rules)
        })

    return results


def evaluate(true_labels, pred_labels):
    """Calculate evaluation metrics for binary classification."""
    true_labels_binary = [1 if label == 1 else 0 for label in true_labels]
    
    accuracy = accuracy_score(true_labels_binary, pred_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels_binary, pred_labels, average='weighted', zero_division=0
    )
    
    report = classification_report(
        true_labels_binary, 
        pred_labels, 
        target_names=['negativo', 'positivo'],
        zero_division=0
    )
    
    cm = confusion_matrix(true_labels_binary, pred_labels, labels=[0, 1])
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'report': report,
        'confusion_matrix': cm
    }


def main():
    test_file = input("Ruta del dataset: ")
    output_errors = "errores_clasificacion.csv"
    output_full = "predicciones_completas.csv"

    print("Cargando datos de prueba...")
    texts, true_labels = load_test_data(test_file)

    print("\nGenerando predicciones detalladas...")
    pred_results = predict_sentiment(texts)

    # Extract preds only for metrics
    pred_labels = [r["prediccion"] for r in pred_results]

    print("\nEvaluando resultados...")
    metrics = evaluate(true_labels, pred_labels)

    # Mostrar métricas
    print("\nMétricas de evaluación:")
    print(f"Exactitud (Accuracy): {metrics['accuracy']:.4f}")
    print(f"Precisión (Precision): {metrics['precision']:.4f}")
    print(f"Sensibilidad (Recall): {metrics['recall']:.4f}")
    print(f"F1-Score: {metrics['f1']:.4f}")
    
    print("\nReporte de clasificación:")
    print(metrics['report'])

    # Guardar predicciones completas
    df_full = pd.DataFrame(pred_results)
    df_full["etiqueta_real"] = true_labels
    df_full.to_csv(output_full, index=False, encoding="utf-8")

    # Filtrar errores
    errores = df_full[df_full["prediccion"] != df_full["etiqueta_real"]].copy()
    errores["tipo_error"] = errores.apply(
        lambda row: "FN" if row["etiqueta_real"] == 1 else "FP", axis=1
    )
    errores["error_magnitud"] = errores["score"].abs()

    errores.to_csv(output_errors, index=False, encoding="utf-8")

    print(f"\n✅ Se guardaron {len(errores)} textos mal clasificados en '{output_errors}'")
    print(f"✅ Predicciones completas guardadas en '{output_full}'")
    print("Proceso completado.")


if __name__ == "__main__":
    main()
