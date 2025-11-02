import spacy
from sentiment_lexicon import (
    LEXICON,
    NEGATORS,
    INTENSIFIERS,
    ADVERSATIVE_CONJUNCTIONS,
    POSITIVE_WORDS,
    NEGATIVE_WORDS
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

def rule_dejar_mucho_que_desear(token):
    # buscamos "dejar" con intensificación + desear en subtree
    if token.lemma_ == "dejar":
        subtree_lemmas = {t.lemma_ for t in token.subtree}
        if "mucho" in subtree_lemmas and "desear" in subtree_lemmas:
            return -3.0  # muy negativo
    return 0

def rule_bien_mucho(token):
    if token.lemma_ == "bien":
        for child in token.children:
            if child.dep_ == "advmod" and child.lemma_ == "mucho":
                return +1.5
    return 0

def rule_negated_performance_verbs(token):
    """
    Regla A: Verbos de desempeño negados → muy negativo.
    Cubre: tener, cumplir, lograr, preparar, reflejar, disponible.
    """
    strong_neg = {"tener", "cumplir", "lograr", "preparar", "reflejar", "disponible"}

    if token.lemma_ in strong_neg:
        for child in token.children:
            if child.dep_ == "advmod" and child.lemma_ == "no":
                return -2.0
    return 0

def rule_negation_with_intensifiers(token):
    """
    Regla C: Si en el subtree hay una negación y un intensificador 
    (realmente, correctamente) → más negativo.
    """
    intensifiers = {"realmente", "correctamente"}
    subtree_lemmas = {t.lemma_ for t in token.subtree}

    if "no" in subtree_lemmas and subtree_lemmas.intersection(intensifiers):
        return -1.5
    return 0

def rule_facil_intuitivo_usar(token):
    """
    Regla E: ADJ ∈ {fácil, intuitivo} y el subtree contiene 'usar'
    → positivo fuerte.
    """
    target_adjs = {"fácil", "intuitivo"}

    if token.lemma_ in target_adjs:
        subtree_lemmas = {t.lemma_ for t in token.subtree}
        if "usar" in subtree_lemmas:
            return +2.0
    return 0

def rule_verbs_appreciation(token):
    """
    Regla F: Verbos de apreciación.
     - encantar, gustar → +2.5
     - superar + 'expectativa' → +3.0
    """
    appreciation = {"encantar", "gustar", "superar"}

    if token.lemma_ in appreciation:
        subtree_lemmas = {t.lemma_ for t in token.subtree}

        if token.lemma_ == "superar" and "expectativa" in subtree_lemmas:
            return +3.0
        return +2.5
    return 0

def rule_contento_intensified(token):
    """
    Regla G: 'contento' intensificado → muy positivo.
    """
    if token.lemma_ == "contento":
        for child in token.children:
            if child.dep_ == "advmod" and child.lemma_ in {"mucho", "muy"}:
                return +2.0
    return 0

def rule_bien_usage_context(token):
    """
    Regla H: 'bien' modificando verbos como usar, funcionar, servir
    → positivo moderado.
    """
    if token.lemma_ == "bien":
        head = token.head
        if head.lemma_ in {"usar", "funcionar", "servir"} and head.pos_ == "VERB":
            return +1.5
    return 0

def rule_no_tener_complement(token):
    """
    Maneja casos de 'no tener X' donde el complemento X define la polaridad real.
    Ejemplos:
      - 'no tener problemas' → positivo
      - 'no tener nada malo' → positivo
      - 'no tener calidad' → negativo
    """
    if token.lemma_ != "tener":
        return 0
    
    # Verificar negación directa
    if not has_negation(token):
        return 0
    
    # Buscar complemento nominal
    complement_nouns = [child for child in token.children if child.dep_ in ("obj", "dobj", "obl", "nmod")]
    if not complement_nouns:
        return -1.0  # default: 'no tener' suele ser negativo suave
    
    score = 0
    for comp in complement_nouns:
        lemma = comp.lemma_.lower()
        
        # Si el complemento está en el léxico, lo usamos
        if lemma in NEGATIVE_WORDS:
            # no tener [algo negativo] => positivo
            score += abs(NEGATIVE_WORDS[lemma])  
        
        elif lemma in POSITIVE_WORDS:
            # no tener [algo positivo] => negativo
            score -= abs(POSITIVE_WORDS[lemma])
        
        # Casos especiales comunes
        elif lemma in {"problema", "problemas", "queja", "quejas", "malo"}:
            score += 1.5  # positivo fuerte: no tener problemas
        
        elif lemma in {"calidad", "valor", "mérito"}:
            score -= 1.5  # negativo fuerte: no tener calidad

    return score

def rule_calidad_baja(token):
    """
    Detecta patrones del tipo:
    - 'calidad baja'
    - 'la calidad es baja'
    - 'calidad muy baja'
    """
    if token.lemma_ not in {"bajo", "baja"}:
        return 0
    
    # Buscar si el adjetivo modifica 'calidad'
    for child in token.children:
        if child.dep_ in ("nsubj", "nsubj:pass", "obl", "obj"):
            if child.lemma_ == "calidad":
                return -2.0  # negativo fuerte
    
    # O si el head es 'calidad'
    if token.head.lemma_ == "calidad":
        return -2.0

    return 0

def rule_no_lograr(token):
    """
    Maneja casos de 'no lograr X' como negativo fuerte.
    """
    if token.lemma_ != "lograr":
        return 0
    
    if has_negation(token):
        return -2.5  # más fuerte que tu regla actual

    return 0

def rule_decepcionante_bastante(token):
    """
    'decepcionante' intensificado con 'bastante' suele ser negativo muy fuerte.
    """
    if token.lemma_ != "decepcionante":
        return 0
    
    for child in token.children:
        if child.dep_ == "advmod" and child.lemma_ == "bastante":
            return -2.5
    
    return 0

def rule_visitado_cerrado(token):
    """
    Si se visita un sitio y está 'cerrado', 'incompleto', 'vacío' → negativo fuerte.
    """
    if token.lemma_ not in {"visitar", "visité", "visite"}:
        return 0
    
    subtree_lemmas = {t.lemma_ for t in token.subtree}
    
    negative_states = {"cerrado", "completo", "incompleto", "vacío", "dañado"}

    if subtree_lemmas.intersection(negative_states):
        return -2.0

    return 0

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

    for rule_fn, rule_name in [
        (rule_dejar_mucho_que_desear, "dejar_mucho_que_desear"),
        (rule_bien_mucho, "bien_mucho"),
        (rule_negated_performance_verbs, "neg_performance_verbs"),
        (rule_negation_with_intensifiers, "neg_intensifiers"),
        (rule_facil_intuitivo_usar, "facil_intuitivo_usar"),
        (rule_verbs_appreciation, "verbs_appreciation"),
        (rule_contento_intensified, "contento_intensified"),
        (rule_bien_usage_context, "bien_usage_context"),

        (rule_no_tener_complement, "no_tener_complement"),
        (rule_calidad_baja, "calidad_baja"),
        (rule_no_lograr, "no_lograr"),
        (rule_decepcionante_bastante, "decepcionante_bastante"),
        (rule_visitado_cerrado, "visitado_cerrado"),
        ]:

        adjustment = rule_fn(token)
        if adjustment != 0:
            score += adjustment   # o multiplicar según el caso
            applied_rules.append(rule_name)

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
        # "No disfruté el festival pero la comida estuvo excelente",
        # "La calidad de las presentaciones fue baja.",
        "No tener problemas",

    ]
    for ex in examples:
        analyse = analyze_sentiment(ex, True)
        print(ex, "->",analyse )