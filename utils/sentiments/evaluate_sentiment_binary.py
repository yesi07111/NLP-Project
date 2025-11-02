import csv
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
from sentiment_rules import analyze_sentiment

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

def load_existing_results(output_file):
    """Load existing results from file if it exists."""
    try:
        df = pd.read_csv(output_file)
        return df['texto'].tolist(), df['prediccion'].tolist()
    except (FileNotFoundError, KeyError):
        return [], []

def save_results_incrementally(text, prediction, output_file):
    """Save a single prediction result to the output file."""
    import os
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['texto', 'prediccion'])
        writer.writerow([text, prediction])

def predict_sentiment(texts, output_file='resultados_sentimiento_temp.csv'):
    """Predict sentiment for a list of texts using binary classification.
    
    Args:
        texts: List of texts to analyze
        output_file: File to save incremental results
        
    Returns:
        List of predicted labels (0 for negative, 1 for positive)
    """
    # Load existing results
    processed_texts, pred_labels = load_existing_results(output_file)
    
    # Skip already processed texts
    start_idx = len(processed_texts)
    
    print(f"Found {start_idx} previously processed texts. Resuming from index {start_idx}...")
    
    # Process remaining texts
    for i in range(start_idx, len(texts)):
        text = texts[i]
        
        result = analyze_sentiment(text)
        # Binary classification: positive if score > 0, negative otherwise
        pred = 1 if result['score'] > 0 else 0
        pred_labels.append(pred)
        
        # Save result immediately
        save_results_incrementally(text, pred, output_file)        
          
    return pred_labels

def evaluate(true_labels, pred_labels):
    """Calculate and print evaluation metrics for binary classification."""
    # Map true_labels to binary: -1 and 0 -> 0 (negativo), 1 -> 1 (positivo)
    true_labels_binary = [1 if label == 1 else 0 for label in true_labels]
    
    # Calculate metrics
    accuracy = accuracy_score(true_labels_binary, pred_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels_binary, pred_labels, average='weighted', zero_division=0
    )
    
    # Get classification report for binary
    report = classification_report(
        true_labels_binary, 
        pred_labels, 
        target_names=['negativo', 'positivo'],
        zero_division=0
    )
    
    # Create confusion matrix
    cm = confusion_matrix(true_labels_binary, pred_labels, labels=[0, 1])
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'report': report,
        'confusion_matrix': cm
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
    temp_output = 'resultados_sentimiento_temp.csv'
    final_output = 'resultados_sentimiento_final.csv'
    
    # Load test data
    print("Cargando datos de prueba...")
    texts, true_labels = load_test_data(test_file)
    
    # Make predictions with incremental saving
    print("\nIniciando predicciones (se guardarán incrementalmente)...")
    pred_labels = predict_sentiment(texts, temp_output)
    
    # Filter out any None values from failed predictions
    valid_indices = [i for i, pred in enumerate(pred_labels) if pred is not None]
    valid_texts = [texts[i] for i in valid_indices]
    valid_true_labels = [true_labels[i] for i in valid_indices]
    valid_pred_labels = [pred_labels[i] for i in valid_indices]
    
    # Save final results with true labels
    final_results = pd.DataFrame({
        'texto': valid_texts,
        'etiqueta_real': valid_true_labels,
        'prediccion': valid_pred_labels
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
