import spacy
from  utils.sentiments.sentiment_lexicon import LEXICON
nlp = spacy.load("es_core_news_md")

# ==========================================================
# CONFIGURACIONES IMPORTANTES
# ==========================================================

# POS relevantes para polaridad
RELEVANT_POS = {"ADJ", "ADV", "VERB"}

# DEP relevantes para relaciones semánticas
RELEVANT_DEP = {
    "amod",     # adjetivo modificando a sustantivo
    "advmod",   # adverbio modificando adjetivo/verbo
    "obj",      # objeto directo
    "nsubj",    # sujeto
    "acomp",    # complemento adjetival
    "xcomp",    # complementos
    "ccomp",    # cláusula completiva
    "obl",      # modificador oblicuo
    "neg",      # negación
}

# Palabras que probablemente aportan polaridad
SEED_SENTIMENT_WORDS = {
    "bueno","malo","excelente","terrible","pésimo","genial","horrible",
    "decepcionante","asombroso","fantástico","lento","rápido",
    "gustar","encantar","odiar","amar","molestar","fallar",
    "muy","bastante","demasiado","poco","nada"
}


# ==========================================================
# FILTROS DE PATRONES (para eliminar ruido)
# ==========================================================

def is_relevant_token(token):
    """
    Un token es relevante si:
    - su POS es potencialmente emocional (ADJ, VERB, ADV), o
    - su lemma está en una lista inicial de palabras con polaridad
    """
    return (
        token.pos_ in RELEVANT_POS
        or token.lemma_.lower() in SEED_SENTIMENT_WORDS
        or token.lemma_.lower() in LEXICON
    )


def is_relevant_dep(dep):
    """Solo dependencias informativas para sentimiento."""
    return dep in RELEVANT_DEP


# ==========================================================
# EXTRACTOR FILTRADO
# ==========================================================

def extract_filtered_patterns(sentence):
    """
    Extrae SOLO los patrones sintácticos útiles para reglas de sentimiento.
    Filtra por POS, DEP y relevancia semántica.
    """
    doc = nlp(sentence)
    patterns = []

    for sent in doc.sents:
        for token in sent:

            # ----------------------------------------------------
            # 1. Ignorar tokens no relevantes
            # ----------------------------------------------------
            if not is_relevant_token(token):
                continue

            lemma = token.lemma_.lower()

            # ----------------------------------------------------
            # 2. Relaciones HEAD → TOKEN relevantes
            # ----------------------------------------------------
            dep = token.dep_
            head = token.head.lemma_.lower()

            if is_relevant_dep(dep):
                patterns.append(("HEAD_REL", head, dep, lemma))

            # ----------------------------------------------------
            # 3. Relaciones TOKEN → HIJOS relevantes
            # ----------------------------------------------------
            for child in token.children:
                dep2 = child.dep_
                if is_relevant_dep(dep2) and is_relevant_token(child):
                    patterns.append(("CHILD_REL", lemma, dep2, child.lemma_.lower()))

            # ----------------------------------------------------
            # 4. SUBTREES emocionalmente densos
            #    Solo si el subtree contiene al menos otro token relevante
            # ----------------------------------------------------
            subtree_lemmas = [
                t.lemma_.lower()
                for t in token.subtree
                if is_relevant_token(t)
            ]

            if len(subtree_lemmas) > 1:  # evitar SUBTREE inútiles de 1 palabra
                patterns.append(("SUBTREE", lemma, tuple(sorted(subtree_lemmas))))

    return patterns


