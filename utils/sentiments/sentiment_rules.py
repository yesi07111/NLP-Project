import spacy
from sentiment_lexicon import (
    LEXICON,
    NEGATORS,
    INTENSIFIERS,
    ADVERSATIVE_CONJUNCTIONS,
)
from pprint import pprint


nlp = spacy.load("es_core_news_md")

# ================================================================
#  FUNCIONES AUXILIARES DE DEPENDENCIAS
# ================================================================

def has_negation(token):
    """
    Verifica si un token está afectado por una negación.
    Busca en:
      - Hijos inmediatos (token.children)
      - Ancestros hasta 3 niveles
      - Tokens a la izquierda (lefts)
      - Subárbol local
    """
    for child in token.children:
        if child.text.lower() in NEGATORS:
            return True

    # Buscar en ancestros hasta 3 niveles
    ancestor = token.head
    for _ in range(3):
        if not ancestor or ancestor == token:
            break
        if ancestor.text.lower() in NEGATORS:
            return True
        ancestor = ancestor.head

    # Buscar tokens a la izquierda inmediata
    for left in token.lefts:
        if left.text.lower() in NEGATORS:
            return True

    # Buscar en el subárbol (por ejemplo “no me gusta nada”)
    for sub in token.subtree:
        if sub.text.lower() in NEGATORS:
            return True

    return False


def get_intensity_multiplier(token):
    """
    Devuelve un multiplicador si el token tiene intensificadores asociados.
    Busca modificadores adverbiales o adjetivales (advmod, amod).
    """
    mult = 1.0
    for child in token.children:
        if child.dep_ in ("advmod", "amod"):
            if child.text.lower() in INTENSIFIERS:
                mult *= INTENSIFIERS[child.text.lower()]
    # También revisar ancestros (ej. “muy bien hecho” → “hecho” tiene intensificador “muy” arriba)
    ancestor = token.head
    for _ in range(2):
        if not ancestor or ancestor == token:
            break
        if ancestor.text.lower() in INTENSIFIERS:
            mult *= INTENSIFIERS[ancestor.text.lower()]
        ancestor = ancestor.head
    return mult


def detect_adversative_clauses(sent):
    """
    Detecta si hay conjunciones adversativas (ej. 'pero', 'aunque') en la oración.
    Devuelve True/False y la conjunción detectada.
    """
    for token in sent:
        if token.text.lower() in ADVERSATIVE_CONJUNCTIONS:
            return True, token.text.lower()
        # Buscar conjunciones por dependencias (cc o mark)
        if token.dep_ in ("cc", "mark") and token.text.lower() in ADVERSATIVE_CONJUNCTIONS:
            return True, token.text.lower()
    return False, None


# ================================================================
#  APLICACIÓN DE REGLAS GRAMATICALES
# ================================================================

def apply_grammatical_rules(token, base_score, debug_info):
    """
    Aplica reglas gramaticales (dependientes del árbol de dependencias)
    y devuelve el nuevo puntaje ajustado.
    """
    score = base_score
    applied_rules = []

    # --- Regla 1: Negación ---
    if has_negation(token):
        score *= -1
        applied_rules.append("negation")

    # --- Regla 2: Intensificadores ---
    mult = get_intensity_multiplier(token)
    if mult != 1.0:
        score *= mult
        applied_rules.append(f"intensifier(x{mult})")

    # --- (Hook para futuras reglas) ---
    # Ejemplo futuro: cláusulas concesivas, sarcasmo, modales, etc.

    debug_info.extend(applied_rules)
    return score


# ================================================================
#  FUNCIÓN PRINCIPAL DE ANÁLISIS
# ================================================================

def analyze_sentiment(text, debug=True):
    """
    Analiza el sentimiento de un texto aplicando reglas basadas en dependencias.
    Devuelve un diccionario con el puntaje y, si debug=True, los detalles.
    """
    doc = nlp(text)
    total_score = 0.0
    details = []

    for sent in doc.sents:
        sent_score = 0.0
        sent_debug = []

        # Detectar conjunciones adversativas en la oración
        has_adv, conj = detect_adversative_clauses(sent)

        for token in sent:
            lemma = token.lemma_.lower()
            if lemma in LEXICON:
                base = LEXICON[lemma]
                adjusted = apply_grammatical_rules(token, base, sent_debug)
                sent_score += adjusted

        # Si hay conjunción adversativa, aplicar peso
        if has_adv:
            mult = ADVERSATIVE_CONJUNCTIONS.get(conj, 1.0)
            sent_score *= mult
            sent_debug.append(f"adversative({conj},x{mult})")

        total_score += sent_score
        details.append({
            "sentence": sent.text.strip(),
            "score": round(sent_score, 3),
            "rules": sent_debug
        })

    polarity = (
        "positivo" if total_score > 0
        else "negativo" if total_score < 0
        else "neutro"
    )

    if debug:
        return {
            "text": text,
            "score": round(total_score, 3),
            "sentiment": polarity,
            "details": details
        }
    else:
        return polarity

if __name__ == "__main__":
    examples = [
        # "Me gusta mucho esto, es excelente 👍",
        # "No me gustó, estuvo terrible",
        # "Está bien, pero podría ser mejor",
        # "No me gusta el servicio, pero la comida está buena.",
        # "No me gusta el servicio, pero la comida está muy buena.",
        # "No me gusta el servicio",
        # "El servicio esta malo",
        # "El servicio no esta malo",
        # "El servicio no esta muy bueno",
        # "La obra de teatro careció de emoción y profesionalismo.",
        # "La entrega tardó mucho más de lo esperado.",
        # "La visita guiada al sitio arqueológico fue educativa y emocionante, el guía explicaba cada detalle con gran entusiasmo y conocimiento.",
        # "La conferencia educativa a la que asistí fue inspiradora, los ponentes eran expertos en su área y brindaron conocimientos muy valiosos.",
        # "El museo tenía pocas exposiciones abiertas y la mayoría estaban en malas condiciones, fue una experiencia frustrante para los visitantes.",
        # "No puedo decir nada bueno de ti",
        # "No disfruté el festival, la programación fue monótona y poco atractiva.",
        "No disfruté el festival pero la comida estuvo excelente",

    ]
    for ex in examples:
        analyse = analyze_sentiment(ex, True)
        print(ex, "->",analyse )