"""Pequeño lexicón de ejemplo para polaridad e intensificadores.

Este archivo contiene un lexicón minimalista en español para prototipar
el análisis de sentimiento basado en reglas. Es intencionalmente pequeño —
puedes reemplazarlo por SentiLex-ESP u otros recursos más completos.
"""

LEXICON = {
    "bueno": 1.0,
    "excelente": 1.5,
    "genial": 1.3,
    "fantástico": 1.6,
    "bien": 0.8,
    "agradable": 0.9,
    "malo": -1.0,
    "terrible": -1.6,
    "horrible": -1.5,
    "feo": -0.8,
    "pésimo": -1.4,
}

INTENSIFIERS = {
    "muy": 1.5,
    "súper": 1.4,
    "super": 1.4,
    "re": 1.2,
    "poco": 0.7,
}

NEGATORS = {"no", "nunca", "jamás", "jamas", "nadie", "sin"}

EMOJI_LEXICON = {
    "👍": 1.0,
    "👎": -1.0,
    "❤️": 1.0,
    "😂": 0.5,
    "😡": -1.2,
}
