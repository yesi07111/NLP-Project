"""Implementación de análisis de sentimiento basada en reglas
que operan sobre un árbol de dependencias

Interfaz principal: analyze_sentiment(text) -> {label, score, details}
"""

from typing import List, Dict, Any
import re

import spacy
from spacy.language import Language

nlp = spacy.load("es_core_news_md")

from utils.sentiment_lexicon import *

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

def _process_sentence(sent, apply_intensifiers=True):
    """Procesa una oración sin conjunciones adversativas.
    
    Args:
        sent: La oración a procesar (objeto Span de spaCy)
        apply_intensifiers: Si es True, aplica los intensificadores
    """
    sent_score = 0.0
    sent_details = []
    
    for token in sent:
        if token.is_space:
            continue
            
        # Obtener polaridad del token
        polarity = _token_polarity(token)
        
        # Verificar negaciones e intensificadores
        mult = 1.0
        negated = False
        intensified = False
        
        # Verificar si hay un negador antes del token
        for child in token.children:
            if child.text.lower() in NEGATORS and child.i < token.i:
                mult *= -1
                negated = True
                break
                
        # Verificar intensificadores
        if apply_intensifiers:
            for child in token.children:
                if child.text.lower() in INTENSIFIERS and child.i < token.i:
                    mult *= INTENSIFIERS[child.text.lower()]
                    intensified = True
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
            'intensified': intensified,
            'multiplier': mult,
            'contribution': contribution,
            'start': token.idx,
            'end': token.idx + len(token.text)
        })
    
    return sent_score, sent_details

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
        sent_text = sent.text.lower()
        sent_score = 0.0
        sent_details = []
        
        # Verificar si hay conjunciones adversativas
        has_adversative = False
        adversative_conj = None
        
        # Buscar conjunciones adversativas en la oración
        for conj in ADVERSATIVE_CONJUNCTIONS:
            if conj in sent_text:
                has_adversative = True
                adversative_conj = conj
                break
        
        # Si hay conjunción adversativa, dividir la oración
        if has_adversative:
            parts = re.split(rf'(\b{re.escape(adversative_conj)}\b)', sent_text, flags=re.IGNORECASE)
            if len(parts) >= 3:
                # Primera parte (antes de la conjunción)
                first_part_text = parts[0].strip()
                if first_part_text:
                    first_part = nlp(first_part_text)
                    first_score, first_details = _process_sentence(first_part)
                else:
                    first_score, first_details = 0.0, []
                
                # Segunda parte (después de la conjunción)
                second_part_text = ''.join(parts[2:]).strip()
                if second_part_text:
                    second_part = nlp(second_part_text)
                    # Aplicar el peso de la conjunción adversativa
                    adv_weight = ADVERSATIVE_CONJUNCTIONS[adversative_conj]
                    second_score, second_details = _process_sentence(second_part)
                    second_score *= adv_weight
                    
                    # Ajustar los detalles para reflejar el peso
                    for detail in second_details:
                        detail['multiplier'] *= adv_weight
                        detail['contribution'] = detail['polarity'] * detail['multiplier']
                else:
                    second_score, second_details = 0.0, []
                
                # Calcular puntuación final de la oración
                sent_score = (first_score + second_score) / 2
                sent_details = first_details + second_details
            else:
                # Si no se puede dividir correctamente, procesar normalmente
                sent_score, sent_details = _process_sentence(sent)
        else:
            # Si no hay conjunción adversativa, procesar normalmente
            sent_score, sent_details = _process_sentence(sent)
        
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
    num_sentences = len(list(doc.sents))
    avg_score = total_score / num_sentences if num_sentences > 0 else 0.0
    
    return {
        'label': _score_to_label(avg_score),
        'score': avg_score,
        #'details': all_details,
        #'sentences': sentence_scores
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
        "No me gusta el servicio, pero la comida está buena.",
        "No me gusta el servicio, pero la comida está muy buena.",
        "No me gusta el servicio"
    ]
    for ex in examples:
        print(ex, "->", analyze_sentiment(ex))