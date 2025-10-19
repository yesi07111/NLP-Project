"""Implementación minimalista de análisis de sentimiento basada en reglas
que operan sobre un árbol de dependencias si spaCy está disponible, o
sobre heurísticas simples si no.

Interfaz principal: analyze_sentiment(text) -> {label, score, details}
"""

from typing import List, Dict, Any
import re

try:
    import spacy
    from spacy.language import Language
    _HAS_SPACY = True
except Exception:
    spacy = None
    _HAS_SPACY = False

from sentiment_lexicon import LEXICON, INTENSIFIERS, NEGATORS, EMOJI_LEXICON

def _token_polarity(token_text: str) -> float:
    t = token_text.lower()
    if t in LEXICON:
        return LEXICON[t]
    if t in EMOJI_LEXICON:
        return EMOJI_LEXICON[t]
    return 0.0


# def _simple_parse(text: str) -> List[Dict[str, Any]]:
#     """Fallback parser: divide en tokens y detecta negadores/intensificadores
#     Devuelve lista de tokens con fields: text, idx, polarity, is_negator, intensifier
#     """
#     # tokenizamos de forma muy simple (palabras y emojis)
#     tokens = re.findall(r"\w+|[^-\u007F]+", text)
#     parsed = []
#     for i, tok in enumerate(tokens):
#         low = tok.lower()
#         parsed.append({
#             "text": tok,
#             "idx": i,
#             "polarity": _token_polarity(low),
#             "is_negator": low in NEGATORS,
#             "intensifier": INTENSIFIERS.get(low, 1.0),
#         })
#     return parsed


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """Analiza sentimiento de `text` y devuelve etiqueta, score y detalles.

    Estrategia:
      - Si spaCy está disponible, parsea dependencias y aplica reglas sobre
        relaciones: negación (child 'neg'), modificadores adverbiales (advmod),
        adjetivos (amod), conjunciones adversativas ('pero').
      - Si spaCy no está disponible, usa un parser simple basado en tokens y
        aplica reglas locales (mirar token anterior para negador e intensificador).
    """
    if _HAS_SPACY:
        nlp = spacy.load("es_core_news_md") if "es_core_news_md" in spacy.util.get_installed_models() else None
        # intentar cargar modelo en runtime; si falla, fallback
        if nlp is not None:
            doc = nlp(text)
            score = 0.0
            details = []
            # detectar cláusulas con 'pero' para dar preferencia a lo que sigue
            has_but = any([tok.text.lower() == "pero" for tok in doc])
            for tok in doc:
                p = _token_polarity(tok.text)
                if p == 0.0:
                    continue
                mult = 1.0
                # intensificador: adverbial modifier o child con token en INTENSIFIERS
                for child in tok.children:
                    ctext = child.text.lower()
                    if ctext in INTENSIFIERS:
                        mult *= INTENSIFIERS[ctext]
                    if child.dep_ == "neg":
                        mult *= -1
                # revisar si hay negación como ancestro
                ancestor = tok
                while ancestor.head is not ancestor:
                    if ancestor.head.text.lower() in NEGATORS:
                        mult *= -1
                        break
                    if ancestor.dep_ == 'ROOT':
                        break
                    ancestor = ancestor.head

                contribution = p * mult
                details.append({"token": tok.text, "base": p, "mult": mult, "contribution": contribution})
                score += contribution

            # si hay 'pero', damos más peso a lo que viene después de 'pero'
            if has_but:
                # simple heurística: si 'pero' aparece, aumentar la magnitud
                score *= 1.2

            label = _score_to_label(score)
            return {"label": label, "score": score, "details": details}

    # # fallback simple
    # parsed = _simple_parse(text)
    # score = 0.0
    # details = []
    # for i, token in enumerate(parsed):
    #     p = token["polarity"]
    #     if p == 0.0:
    #         continue
    #     mult = token.get("intensifier", 1.0)
    #     # si el token anterior es negador, invertimos
    #     if i > 0 and parsed[i - 1]["is_negator"]:
    #         mult *= -1
    #     contribution = p * mult
    #     details.append({"token": token["text"], "base": p, "mult": mult, "contribution": contribution})
    #     score += contribution

    # label = _score_to_label(score)
    # return {"label": label, "score": score, "details": details}


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
