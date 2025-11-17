import csv
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns
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
    """Predict sentiment for a list of texts."""
    pred_labels = []
    
    for text in texts:
        result = analyze_sentiment(text)
        # Map sentiment labels to numerical values
        if result['score'] > 0:
            pred_labels.append(1)
        elif result['score'] < 0:
            pred_labels.append(-1)
        else:  # neutro
            pred_labels.append(0)
            
    return pred_labels

def evaluate(true_labels, pred_labels):
    """Calculate and print evaluation metrics."""
    # Calculate metrics
    accuracy = accuracy_score(true_labels, pred_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels, pred_labels, average='weighted', zero_division=0
    )
    
    # Get classification report
    report = classification_report(
        true_labels, 
        pred_labels, 
        target_names=['negativo', 'neutro', 'positivo'],
        zero_division=0
    )
    
    # Create confusion matrix
    cm = confusion_matrix(true_labels, pred_labels, labels=[-1, 0, 1])
    
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
    # Load test data
    test_file = input("Ruta del dataset: ")
    texts, true_labels = load_test_data(test_file)
    
    # Make predictions
    print("Haciendo predicciones...")
    pred_labels = predict_sentiment(texts)
    
    # Evaluate
    print("\nEvaluando resultados...")
    metrics = evaluate(true_labels, pred_labels)
    
    # Print results
    print("\nMétricas de evaluación:")
    print(f"Exactitud (Accuracy): {metrics['accuracy']:.4f}")
    print(f"Precisión (Precision): {metrics['precision']:.4f}")
    print(f"Sensibilidad (Recall): {metrics['recall']:.4f}")
    print(f"F1-Score: {metrics['f1']:.4f}")
    
    print("\nReporte de clasificación:")
    print(metrics['report'])
    
    # Plot confusion matrix
    plot_confusion_matrix(metrics['confusion_matrix'], ['Negativo', 'Neutro', 'Positivo'])
    print("\nMatriz de confusión guardada como 'confusion_matrix.png'")
    
    # Save detailed results
    results = pd.DataFrame({
        'texto': texts,
        'etiqueta_real': true_labels,
        'prediccion': pred_labels
    })
    results.to_csv('resultados_sentimiento.csv', index=False, encoding='utf-8')
    print("\nResultados detallados guardados en 'resultados_sentimiento.csv'")

if __name__ == "__main__":
    main()

