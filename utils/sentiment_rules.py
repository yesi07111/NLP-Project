"""Implementación minimalista de análisis de sentimiento basada en reglas
que operan sobre un árbol de dependencias si spaCy está disponible, o
sobre heurísticas simples si no.

Interfaz principal: analyze_sentiment(text) -> {label, score, details}
"""

from typing import List, Dict, Any
import re

import spacy
from spacy.language import Language

nlp = spacy.load("es_core_news_md")

from sentiment_lexicon import *

def _token_polarity(token) -> float:
    """Calcula la polaridad de un token, considerando su forma base (lema).
    
    Args:
        token: Token de spaCy que incluye información de lematización y POS
        
    Returns:
        float: Puntuación de sentimiento del token
    """
    # Primero buscar el token original en minúsculas
    t = token.text.lower()
    
    # Buscar el lema del token (forma base)
    lemma = token.lemma_.lower() if hasattr(token, 'lemma_') else t
    
    # Buscar en el léxico principal con el texto original
    if t in LEXICON:
        return LEXICON[t]
    
    # Si no se encuentra, buscar el lema
    if lemma in LEXICON and lemma != t:
        return LEXICON[lemma]
    
    # Buscar en el diccionario de emojis
    if t in EMOJI_LEXICON:
        return EMOJI_LEXICON[t]
    
    # Manejar palabras que cambian de polaridad según el contexto
    if t in CONTEXT_DEPENDENT:
        word_info = CONTEXT_DEPENDENT[t]
        # Verificar si coincide la categoría gramatical
        if token.pos_ == word_info['POS']:
            # Buscar contexto en los hijos (palabras modificadas por este token)
            for child in token.children:
                if child.text.lower() in word_info['contexts']:
                    return word_info['contexts'][child.text.lower()]
            # Si no se encuentra contexto específico, devolver el valor por defecto
            return word_info['score']
    
    # Si no se encuentra en ningún diccionario, devolver 0.0 (neutro)
    return 0.0


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analiza el sentimiento de un texto.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Dict con las claves:
        - label: 'positivo', 'negativo' o 'neutro'
        - score: Puntuación numérica del sentimiento
        - details: Lista de tokens con su contribución al sentimiento
        - sentences: Lista de oraciones con sus puntuaciones
    """
    if not text.strip():
        return {
            'label': 'neutro',
            'score': 0.0,
            'details': [],
            'sentences': []
        }
    
    doc = nlp(text)
    total_score = 0.0
    all_details = []
    sentence_scores = []
    
    # Procesar cada oración por separado
    for sent in doc.sents:
        sent_score = 0.0
        sent_details = []
        i = 0
        
        while i < len(sent):
            # Verificar si hay una expresión idiomática que comience en esta posición
            remaining_text = sent[i:].text.lower()
            idiom_found = False
            
            for expr, expr_score in IDIOMATIC_EXPRESSIONS.items():
                if remaining_text.startswith(expr.lower()):
                    # Contar cuántas palabras tiene la expresión
                    expr_word_count = len(expr.split())
                    sent_score += expr_score
                    sent_details.append({
                        'text': ' '.join(t.text for t in sent[i:i+expr_word_count]),
                        'score': expr_score,
                        'type': 'idiom',
                        'start': sent[i].idx,
                        'end': sent[i+expr_word_count-1].idx + len(sent[i+expr_word_count-1].text)
                    })
                    i += expr_word_count
                    idiom_found = True
                    break
            
            if idiom_found:
                continue
                
            # Análisis de tokens individuales
            token = sent[i]
            
            # Saltar espacios en blanco
            if token.is_space:
                i += 1
                continue
                
            # Obtener polaridad del token
            polarity = _token_polarity(token)
            
            # Verificar negaciones e intensificadores
            mult = 1.0
            negated = False
            
            # Verificar si hay un negador antes del token
            for child in token.children:
                if child.text.lower() in NEGATORS and child.i < token.i:
                    mult *= -1
                    negated = True
                    break
                    
            # Verificar intensificadores
            for child in token.children:
                if child.text.lower() in INTENSIFIERS and child.i < token.i:
                    mult *= INTENSIFIERS[child.text.lower()]
                    break
            
            # Aplicar la polaridad
            contribution = polarity * mult
            sent_score += contribution
            
            sent_details.append({
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'polarity': polarity,
                'negated': negated,
                'multiplier': mult,
                'contribution': contribution,
                'start': token.idx,
                'end': token.idx + len(token.text)
            })
            
            i += 1
        
        # Añadir puntuación de la oración al total
        total_score += sent_score
        all_details.extend(sent_details)
        
        # Guardar información de la oración
        sentence_scores.append({
            'text': sent.text,
            'score': sent_score,
            'label': _score_to_label(sent_score)
        })
    
    # Calcular el puntaje promedio
    avg_score = total_score / len(list(doc.sents)) if len(list(doc.sents)) > 0 else 0.0
    
    return {
        'label': _score_to_label(avg_score),
        'score': avg_score,
        'details': all_details,
        'sentences': sentence_scores
    }


def _score_to_label(score: float, pos_thr: float = 0.3, neg_thr: float = -0.3) -> str:
    if score >= pos_thr:
        return "positivo"
    if score <= neg_thr:
        return "negativo"
    return "neutro"


if __name__ == "__main__":
    examples = [
        "Me gusta mucho esto, es excelente 👍",
        "No me gustó, estuvo terrible",
        "Está bien, pero podría ser mejor",
        "No me gusta el servicio, pero la comida está muy buena."
    ]
    for ex in examples:
        print(ex, "->", analyze_sentiment(ex))