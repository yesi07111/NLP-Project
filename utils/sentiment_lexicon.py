"""Léxico en español para análisis de sentimientos.

Incluye palabras positivas, negativas, intensificadores, negadores y expresiones idiomáticas.
"""

# Palabras positivas con sus puntuaciones (0.5 a 2.0)
POSITIVE_WORDS = {
    # Adjetivos positivos
    "bueno": 1.0, "buen": 1.0, "buena": 1.0, "buenos": 1.0, "buenas": 1.0, "bien": 1.0,
    "excelente": 1.7, "excelentes": 1.7,
    "genial": 1.4, "geniales": 1.4,
    "fantástico": 1.6, "fantástica": 1.6, "fantásticos": 1.6, "fantásticas": 1.6,
    "maravilloso": 1.5, "maravillosa": 1.5, "maravillosos": 1.5, "maravillosas": 1.5,
    "increíble": 1.5, "increíbles": 1.5,
    "perfecto": 1.6, "perfecta": 1.6, "perfectos": 1.6, "perfectas": 1.6,
    "agradable": 1.0, "agradables": 1.0,
    "encantador": 1.2, "encantadora": 1.2, "encantadores": 1.2, "encantadoras": 1.2,
    
    # Verbos positivos
    "amar": 1.4, "amo": 1.4, "amas": 1.4, "ama": 1.4, "amamos": 1.4, "aman": 1.4,
    "gustar": 1.0, "gusta": 1.0, "gustan": 1.0,
    "disfrutar": 1.2, "disfruto": 1.2, "disfrutas": 1.2, "disfruta": 1.2,
    "apreciar": 1.1, "aprecio": 1.1, "aprecias": 1.1, "aprecia": 1.1,
    "recomendar": 1.3, "recomiendo": 1.3, "recomiendas": 1.3, "recomienda": 1.3,
    
    # Sustantivos positivos
    "amor": 1.5, "alegría": 1.3, "felicidad": 1.4, "éxito": 1.3,
    "éxitos": 1.3, "sueño": 1.1, "sueños": 1.1, "logro": 1.2, "logros": 1.2,
}

# Palabras negativas con sus puntuaciones (-0.5 a -2.0)
NEGATIVE_WORDS = {
    # Adjetivos negativos
    "malo": -1.0, "mal": -1.0, "mala": -1.0, "malos": -1.0, "malas": -1.0,
    "terrible": -1.7, "terribles": -1.7,
    "horrible": -1.6, "horribles": -1.6,
    "feo": -1.0, "fea": -1.0, "feos": -1.0, "feas": -1.0,
    "pésimo": -1.5, "pésima": -1.5, "pésimos": -1.5, "pésimas": -1.5,
    "horroroso": -1.6, "horrorosa": -1.6, "horrorosos": -1.6, "horrorosas": -1.6,
    "desagradable": -1.2, "desagradables": -1.2,
    "decepcionante": -1.4, "decepcionantes": -1.4,
    "inútil": -1.3, "inútiles": -1.3,
    "pobre": -1.1, "pobres": -1.1,
    
    # Verbos negativos
    "odiar": -1.6, "odio": -1.6, "odias": -1.6, "odia": -1.6,
    "detestar": -1.5, "detesto": -1.5, "detestas": -1.5, "detesta": -1.5,
    "molestar": -1.2, "molesto": -1.2, "molestas": -1.2, "molesta": -1.2,
    "enfadar": -1.3, "enfado": -1.3, "enfadas": -1.3, "enfada": -1.3,
    "fallar": -1.2, "fallo": -1.2, "fallas": -1.2, "falla": -1.2,
    
    # Sustantivos negativos
    "odio": -1.6, "ira": -1.4, "tristeza": -1.3, "fracaso": -1.4,
    "fracasos": -1.4, "problema": -1.2, "problemas": -1.2,
    "error": -1.1, "errores": -1.1, "fallo": -1.1, "fallos": -1.1,
    "decepción": -1.3, "decepciones": -1.3,
}

# Intensificadores (modifican la fuerza de las palabras)
INTENSIFIERS = {
    # Intensificadores positivos (aumentan la intensidad)
    "muy": 1.5, "mucho": 1.5, "muchísimo": 1.8, "demasiado": 1.4,
    "súper": 1.6, "super": 1.6, "hiper": 1.7, "re": 1.3, "recontra": 1.8,
    "sumamente": 1.7, "extremadamente": 1.7, "increíblemente": 1.8,
    "realmente": 1.4, "verdaderamente": 1.4, "absolutamente": 1.6,
    "totalmente": 1.5, "completamente": 1.5,
    
    # Intensificadores negativos (reducen la intensidad)
    "poco": 0.5, "ligeramente": 0.7, "levemente": 0.7,
    "algo": 0.8, "medianamente": 0.8,
}

# Negadores (invierten el sentido de la palabra siguiente)
NEGATORS = {
    "no", "ni", "nunca", "jamás", "jamas", "nadie", "nada", "ninguno", "ninguna",
    "ningunos", "ningunas", "tampoco", "sin", "ni siquiera", "en mi vida",
    "de ninguna manera", "de ningún modo"
}

# Expresiones idiomáticas (frases hechas con significado propio)
IDIOMATIC_EXPRESSIONS = {
    "romper el corazón": -2.0,
    "partir el corazón": -2.0,
    "volver loco": 1.5,
    "volver loca": 1.5,
    "caer bien": 1.2,
    "caer mal": -1.2,
    "dar igual": -0.5,
    "dar lo mismo": -0.5,
    "estar hasta las narices": -1.8,
    "estar hasta la coronilla": -1.8,
    "estar en las nubes": 0.8,
    "ser pan comido": 1.0,
    "estar como una rosa": 1.3,
    "estar como un flan": -1.0,
    "poner los pelos de punta": -1.5,
    "ser la gota que colma el vaso": -1.7,
    "estar en la cima del mundo": 2.0,
    "tocar el cielo con las manos": 2.0,
}

# Emojis y emoticones con sus puntuaciones
EMOJI_LEXICON = {
    # Caras felices
    "😊": 1.5, "😄": 1.6, "😃": 1.5, "😁": 1.4, "😆": 1.3,
    "😍": 1.8, "😘": 1.7, "❤️": 1.8, "💕": 1.6, "💖": 1.7,
    "👍": 1.4, "👌": 1.3, "👏": 1.5, "🙌": 1.5, "🎉": 1.6,
    
    # Caras neutrales
    "😐": 0.0, "😶": 0.0, "🤔": 0.1, "😏": -0.2, "😒": -0.3,
    
    # Caras tristes/enojadas
    "😢": -1.5, "😭": -1.7, "😠": -1.6, "😡": -1.8, "👎": -1.4,
    "💔": -1.8, "😞": -1.3, "😔": -1.2, "😕": -0.8, "😤": -1.5,
}

# Combinar todos los léxicos en uno solo para búsqueda más rápida
LEXICON = {**POSITIVE_WORDS, **NEGATIVE_WORDS}

# Expresiones regulares para detectar signos de exclamación y preguntas
EXCLAMATION_REGEX = r'!+$'
QUESTION_REGEX = r'\?+$'

# Palabras que pueden cambiar de polaridad según el contexto
CONTEXT_DEPENDENT = {
    "duro": {
        'POS': 'ADJ', 'score': -0.8,  # "trabajo duro"
        'contexts': {
            'trabajo': 1.5,  # "trabajo duro" como positivo
            'golpe': -1.5,   # "golpe duro" como negativo
        }
    },
    "fuerte": {
        'POS': 'ADJ', 'score': 0.8,
        'contexts': {
            'abrazo': 1.5,    # "abrazo fuerte" como positivo
            'dolor': -1.5,    # "dolor fuerte" como negativo
        }
    },
}
