import pandas as pd
from collections import Counter
from utils.sentiments.sentiment_rules import analyze_sentiment  # Importa la función existente

def get_sentiment_summary(messages: list) -> dict:
    """
    Calcula un resumen general de sentimiento para una lista de mensajes,
    incluyendo análisis por participante.
    
    Args:
        messages (list): Lista de mensajes (cada uno como dict con 'text' y otros campos).
        
    Returns:
        dict: Resumen con métricas agregadas y por usuario.
    """
    if not messages:
        return {'error': 'No hay mensajes para analizar'}
    
    sentiments = []
    scores = []
    user_data = {}  # Para agrupar por usuario
    
    for msg in messages:
        text = msg.get('text', '')
        sender = msg.get('sender_name', 'Unknown')
        if not text.strip():
            continue
        
        result = analyze_sentiment(text)
        label = result['label']
        score = result['score']
        
        sentiments.append(label)
        scores.append(score)
        
        # Agrupar por usuario
        if sender not in user_data:
            user_data[sender] = {'sentiments': [], 'scores': []}
        user_data[sender]['sentiments'].append(label)
        user_data[sender]['scores'].append(score)
    
    if not sentiments:
        return {'error': 'No se pudo analizar ningún mensaje'}
    
    # Métricas generales
    label_counts = Counter(sentiments)
    total = len(sentiments)
    percentages = {label: (count / total) * 100 for label, count in label_counts.items()}
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    # Análisis por usuario
    user_sentiments = {}
    for user, data in user_data.items():
        user_label_counts = Counter(data['sentiments'])
        user_total = len(data['sentiments'])
        user_avg_score = sum(data['scores']) / user_total if user_total > 0 else 0.0
        user_percentages = {label: (count / user_total) * 100 for label, count in user_label_counts.items()}
        user_most_common = user_label_counts.most_common(1)[0][0] if user_label_counts else 'N/A'
        
        user_sentiments[user] = {
            'total_messages': user_total,
            'average_score': round(user_avg_score, 2),
            'most_common_sentiment': user_most_common,
            'distribution': dict(user_label_counts),
            'percentages': {k: round(v, 2) for k, v in user_percentages.items()}
        }
    
    summary = {
        'total_messages': total,
        'average_score': round(avg_score, 2),
        'distribution': dict(label_counts),
        'percentages': {k: round(v, 2) for k, v in percentages.items()},
        'most_common_sentiment': label_counts.most_common(1)[0][0] if label_counts else 'N/A',
        'user_sentiments': user_sentiments  # Nuevo campo
    }
    
    return summary

# Ejemplo de uso (para pruebas rápidas)
if __name__ == "__main__":
    # Ejemplo de mensajes (simulando del JSON)
    example_messages = [
        {'text': 'Me encanta este proyecto, es genial!'},
        {'text': 'No me gustó, estuvo terrible'},
        {'text': 'Está bien, pero podría mejorar'},
        {'text': '¡Qué maravilla! 👍'},
        {'text': 'Odio esto, es horrible 😠'}
    ]
    
    summary = get_sentiment_summary(example_messages)
    print("Resumen de Sentimiento:")
    for key, value in summary.items():
        print(f"{key}: {value}")