"""Léxico en español para análisis de sentimientos.

Incluye palabras positivas, negativas, intensificadores, negadores y expresiones idiomáticas.
"""

# Palabras positivas con sus puntuaciones (0.5 a 2.0)
POSITIVE_WORDS = {
    # Adjetivos positivos
    "bueno": 1.0, "buen": 1.0, "buena": 1.0, "buenos": 1.0, "buenas": 1.0, "bien": 1.0,
    "excelente": 1.7, "excelentes": 1.7, "valor": 1.5, "valioso": 1.5, "valiosa": 1.5,
    "genial": 1.4, "geniales": 1.4, "experto" : 1.4,
    "fantástico": 1.6, "fantástica": 1.6, "fantásticos": 1.6, "fantásticas": 1.6,
    "maravilloso": 1.5, "maravillosa": 1.5, "maravillosos": 1.5, "maravillosas": 1.5,
    "increíble": 1.5, "increíbles": 1.5,
    "perfecto": 1.6, "perfecta": 1.6, "perfectos": 1.6, "perfectas": 1.6,
    "agradable": 1.0, "agradables": 1.0,
    "encantador": 1.2, "encantadora": 1.2, "encantadores": 1.2, "encantadoras": 1.2,
    
    # Nuevos términos para chats
    "épico": 1.8, "epic": 1.8, "épica": 1.8, "épicas": 1.8,
    "legendario": 1.7, "legendaria": 1.7, "legendarios": 1.7, "legendarias": 1.7,
    "pro": 1.6, "crack": 1.7, "maestro": 1.5, "maestra": 1.5,
    "top": 1.5, "elite": 1.6, "vip": 1.4,
    "cool": 1.3, "awesome": 1.5, "amazing": 1.6,
    "chulo": 1.5, "chula": 1.5, "chulos": 1.5, "chulas": 1.5,
    "killer": 1.6, "pico": 1.6, "cute": 1.5,
    
    # Verbos positivos
    "amar": 1.4, "amo": 1.4, "amas": 1.4, "ama": 1.4, "amamos": 1.4, "aman": 1.4,
    "gustar": 1.0, "gusta": 1.0, "gustan": 1.0,
    "disfrutar": 1.2, "disfruto": 1.2, "disfrutas": 1.2, "disfruta": 1.2,
    "apreciar": 1.1, "aprecio": 1.1, "aprecias": 1.1, "aprecia": 1.1,
    "recomendar": 1.3, "recomiendo": 1.3, "recomiendas": 1.3, "recomienda": 1.3,
    "shippear": 1.5, "apoyar": 1.2, "apoyo": 1.2,
    "stan": 1.5, "dar apoyo": 1.3, "tener": 1.2, "recibir": 1.5, "superar": 1.5, "mejorar": 1.5,
    
    # Nuevos verbos de chats
    "like": 1.2, "likear": 1.2, "mencionar": 0.8, "mention": 0.8, 
    "compartir": 1.1, "share": 1.1, "retuitear": 1.0, "rt": 1.0,
    "streamear": 1.0, "stream": 1.0, 
    "ayudar": 1.1, "colaborar": 1.2, "brindar": 1.4, "inspirar": 1.5, "responder": 0.5,
    
    # Sustantivos positivos
    "amor": 1.5, "alegría": 1.3, "felicidad": 1.4, "éxito": 1.3, "reir": 1.5,
    "éxitos": 1.3, "sueño": 1.1, "sueños": 1.1, "logro": 1.2, "logros": 1.2,
    "meme": 0.8, "memes": 0.8, "trend": 1.2, "viral": 1.3,
    "fandom": 1.2, "fan": 1.1, "fans": 1.1, "hype": 1.4,
    "equipo": 1.0, "colaboración": 1.2, "progreso": 1.3,
    # Nuevas palabras positivas agregadas del dataset
    "alta": 1.0, "calidad": 1.2, "satisfecho": 1.5, "encanta": 1.4,
    "diseño": 1.1, "funcionalidad": 1.2, "intuitiva": 1.3, "fácil": 1.3,
    "contento": 1.4, "superó": 1.3, "expectativas": 1.2, #"evento": 1.0,
    "cultural": 1.0, "talento": 1.3, "presentación": 1.1, "museo": 1.0,
    "exhibiciones": 1.2, "interactivas": 1.3, "educativas": 1.2, "familia": 0.8,
    "festival": 1.0, "variada": 1.1, "atractiva": 1.2,
    "disfruté": 1.3, "interés": 1.1,
    "aprender": 1.1, "cómodo": 1.3,
    "moderno": 1.1, "recomendado": 1.4,
    "rápido": 1.2, "eficiente": 1.3, "puntual": 1.3,
    "impresionante": 1.5, "enriquecedor": 1.4, "entretenido": 1.3,
    "diversidad": 1.2, "capacitados": 1.4, "comprometidos": 1.3, "estimulante": 1.4,
    "excepcional": 1.6, "acogedor": 1.3, "deliciosa": 1.5,
    "velada": 1.1, "especial": 1.3,
    "amabilidad": 1.4, "emoción": 1.5,
}

# Palabras negativas con sus puntuaciones (-0.5 a -2.0)
NEGATIVE_WORDS = {
    # Adjetivos negativos
    "malo": -1.0, "mal": -1.0, "mala": -1.0, "malos": -1.0, "malas": -1.0,
    "terrible": -1.7, "terribles": -1.7,
    "horrible": -1.6, "horribles": -1.6, "frustrante": -1.6, "monótono": -1.2, 
    "feo": -1.0, "fea": -1.0, "feos": -1.0, "feas": -1.0,
    "pésimo": -1.5, "pésima": -1.5, "pésimos": -1.5, "pésimas": -1.5,
    "horroroso": -1.6, "horrorosa": -1.6, "horrorosos": -1.6, "horrorosas": -1.6,
    "desagradable": -1.2, "desagradables": -1.2,
    "decepcionante": -1.4, "decepcionantes": -1.4,
    "inútil": -1.3, "inútiles": -1.3,
    "pobre": -1.1, "pobres": -1.1,
    "noob": -1.2, "nuevo": -0.5, "tóxico": -1.5, "toxica": -1.5,
    "cringe": -1.3, "cringy": -1.3, "fail": -1.4,
    "fula": -1.3, "falso": -1.4, "fake": -1.4, "falta" : -1.5,
    
    # Verbos negativos
    "odiar": -1.6, "odio": -1.6, "odias": -1.6, "odia": -1.6,
    "detestar": -1.5, "detesto": -1.5, "detestas": -1.5, "detesta": -1.5,
    "molestar": -1.2, "molesto": -1.2, "molestas": -1.2, "molesta": -1.2,
    "enfadar": -1.3, "enfado": -1.3, "enfadas": -1.3, "enfada": -1.3,
    "fallar": -1.2, "fallo": -1.2, "fallas": -1.2, "falla": -1.2,
    "ghostear": -1.3, "bloquear": -1.0, "block": -1.0,
    "hatear": -1.5, "trollear": -1.4, "troll": -1.4,
    "matar": -1.5, "molestar": -1.2, "tirar": -0.8, "faltar" : -1.5, 
    
    # Nuevos verbos de chats
    "saltear": -0.8, "skip": -0.8, "mutear": -1.0, "mute": -1.0,
    "reportar": -1.1, "report": -1.1, "banear": -1.3, "ban": -1.3,
    "descarar": -1.2, "spamear": -1.2, "spam": -1.2, "carecer": -1.5,
    
    # Sustantivos negativos
    "odio": -1.6, "ira": -1.4, "tristeza": -1.3, "fracaso": -1.4,
    "fracasos": -1.4, "problema": -1.2, "problemas": -1.2,
    "error": -1.1, "errores": -1.1, "fallo": -1.1, "fallos": -1.1,
    "decepción": -1.3, "decepciones": -1.3,
    "hater": -1.5, "haters": -1.5, "drama": -1.3, "spam": -1.2,
    "scam": -1.6, "estafa": -1.6, "fake": -1.4, "falso": -1.4,
    "chisme": -1.1, "tiradera": -1.3, "desinformación": -1.2, "excusa": -1.2,
    # Nuevas palabras negativas agregadas del dataset
    "decepcionado": -1.4, "tardaron": -1.0, 
    "inconveniente": -1.2, "aburrido": -1.3, "monótona": -1.2,
    "presentaciones": -0.8, "baja": -1.1, "bajo": -1.1, "afecta": -1.1, "lenta": -1.2, "difícil": -1.3,
    "desactualizado": -1.1,
    "confuso": -1.2, "lento": -1.2, "dañado": -1.4,
    "cumplen": -1.1, "reemplazo": -1.0, "desordenada": -1.3,
    "vacío": -1.2, "desmotivador": -1.4,
}

# Intensificadores (modifican la fuerza de las palabras)
INTENSIFIERS = {
    # Intensificadores positivos (aumentan la intensidad)
    "muy": 1.5, "mucho": 1.5, "muchísimo": 1.8, "demasiado": 1.4,
    "súper": 1.6, "super": 1.6, "hiper": 1.7, "re": 1.3, "recontra": 1.8,
    "sumamente": 1.7, "extremadamente": 1.7, "increíblemente": 1.8,
    "realmente": 1.4, "verdaderamente": 1.4, "absolutamente": 1.6,
    "totalmente": 1.5, "completamente": 1.5,
    "mega": 1.6, "ultra": 1.7, "extra": 1.5, "plus": 1.4,
    
    # Intensificadores negativos (reducen la intensidad)
    "poco": 0.5, "ligeramente": 0.7, "levemente": 0.7,
    "algo": 0.8, "medianamente": 0.8, "más o menos": 0.7,
    "casi": 0.6, "apenas": 0.2, "un poco": 0.6,

    # Cuantificadores negativos (aumentan la negatividad)
    "nada": 0,
}

# Negadores (invierten el sentido de la palabra siguiente)
NEGATORS = {
    "no", "ni", "nunca", "jamás", "jamas", "nadie", "nada", "ninguno", "ninguna",
    "ningunos", "ningunas", "tampoco", "sin", "ni siquiera", "en mi vida",
    "de ninguna manera", "de ningún modo", "para nada", "en absoluto",
    "de ningún modo", "en lo más mínimo", "bajo ningún concepto",
    "na", "nah", "nope", "nel"
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
    
    # Nuevas expresiones para chats
    "morir de risa": 1.8, "riendo a carcajadas": 1.8,
    "estar en shock": -1.2, "quedar en shock": -1.2,
    "flipar en colores": 1.6, "alucinar": 1.4,
    "estar en la luna": 0.9, "soñar despierto": 1.0,
    "ir a toda leche": 1.3, "a toda velocidad": 1.3,
    "estar hasta los cojones": -1.9, "estar hasta el coño": -1.9,
    "pasar de todo": -0.8, "no importar": -0.8,
    "ser la leche": 1.8, "ser brutal": 1.7,
    "estar on fire": 1.6, "encendido": 1.6,
    "dar cringe": -1.5, "dar vergüenza ajena": -1.5,
    "shippear hard": 1.7, "ser otp": 1.6,
    "stan": 1.5, "ser fan absoluto": 1.5,
    "ghosting": -1.4, "dejar en visto": -1.3,
    "fomo": -1.2, "miedo a perderse algo": -1.2,
    "dar chucho": -1.3, "molestar": -1.2,
    "ser la pincha": 1.4, "tener una idea genial": 1.4,
    "dar apoyo": 1.3, "apoyar": 1.2,
}

# Emojis y emoticones con sus puntuaciones
EMOJI_LEXICON = {
    # Caras felices
    "😊": 1.5, "😄": 1.6, "😃": 1.5, "😁": 1.4, "😆": 1.3,
    "😍": 1.8, "😘": 1.7, "❤️": 1.8, "💕": 1.6, "💖": 1.7,
    "👍": 1.4, "👌": 1.3, "👏": 1.5, "🙌": 1.5, "🎉": 1.6,
    "😎": 1.4, "🥳": 1.7, "🤩": 1.8, "😜": 1.2, "😝": 1.2,
    "😇": 1.3, "😺": 1.3, "😸": 1.4, "😹": 1.5, "😻": 1.8,
    "😂": 1.6, "🤣": 1.7, "😭": -1.7, "😢": -1.5,
    
    # Caras neutrales
    "😐": 0.0, "😶": 0.0, "🤔": 0.1, "😏": -0.2, "😒": -0.3,
    "🤷": 0.0, "🤷‍♂️": 0.0, "🤷‍♀️": 0.0, "😬": -0.4, "😅": 0.5,
    
    # Caras tristes/enojadas
    "😠": -1.6, "😡": -1.8, "👎": -1.4,
    "💔": -1.8, "😞": -1.3, "😔": -1.2, "😕": -0.8, "😤": -1.5,
    "😩": -1.6, "😫": -1.7, "😖": -1.4, "😣": -1.5, "😥": -1.2,
    
    # Nuevos emojis de chats
    "🔥": 1.6, "💯": 1.8, "⭐": 1.5, "✨": 1.4, "💫": 1.3,
    "🎯": 1.4, "🏆": 1.7, "👑": 1.6, "💎": 1.5, "🚀": 1.5,
    "💀": -1.5, "☠️": -1.6, "😈": -1.3, "👹": -1.4, "👺": -1.3,
    "😱": -1.6, "😨": -1.4, "😰": -1.5, "😓": -1.2, "😪": -0.8,
    "🤡": -1.2, "🤖": 0.5, "👻": -0.3, "🎃": -0.2,
}

# Combinar todos los léxicos en uno solo para búsqueda más rápida
LEXICON = {**POSITIVE_WORDS, **NEGATIVE_WORDS}

# Conjunciones adversativas y su peso en el análisis de sentimiento
# (el peso se aplica a la cláusula que sigue a la conjunción)
ADVERSATIVE_CONJUNCTIONS = {
    'pero': 1.5,           # Aumenta el peso de la cláusula siguiente
    'sin embargo': 1.5,    
    'no obstante': 1.4,
    'aunque': 1.3,        # Aunque puede ser concesiva, a menudo introduce un contraste
    'a pesar de que': 1.3,
    'excepto': 1.4,
    'salvo': 1.4,
    'aun cuando': 1.3,
    'mas': 1.5,           # Sinónimo formal de 'pero'
    'empero': 1.5,        # Sinónimo formal de 'pero'
    'sino': 2.0,          # En construcciones como 'no solo X, sino también Y' da más peso a Y
    'sino que': 2.0,
}


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
