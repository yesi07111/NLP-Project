# sentiment_rules.py
import spacy
from utils.sentiments.sentiment_lexicon import (
    LEXICON,
    NEGATORS,
    INTENSIFIERS,
    ADVERSATIVE_CONJUNCTIONS,
    POSITIVE_WORDS,
    NEGATIVE_WORDS
)
from pprint import pprint
import json
import os
import re

# ================================================================
#  CONFIGURACIÓN DE TRADUCTOR CON FALLBACK
# ================================================================

# Intentar importar googletrans con fallback
try:
    from googletrans import Translator
    translator = Translator()
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    print("⚠️  googletrans no disponible, usando traducción manual limitada")
    GOOGLETRANS_AVAILABLE = False
    translator = None

# ================================================================
#  CARGAR NLTK CON FALLBACK
# ================================================================

SENTIWORDNET_AVAILABLE = False
FALLBACK_CACHE_FILE = "fallback_cache.json"

# Cargar la caché si existe
if os.path.exists(FALLBACK_CACHE_FILE):
    with open(FALLBACK_CACHE_FILE, "r", encoding="utf-8") as f:
        FALLBACK_CACHE = json.load(f)
else:
    FALLBACK_CACHE = {}  # cache vacía

# Intentar cargar NLTK y SentiWordNet
try:
    import nltk
    # Verificar si tenemos los recursos necesarios
    try:
        nltk.data.find('corpora/sentiwordnet')
    except LookupError:
        print("⚠️  SentiWordNet no encontrado, descargando...")
        try:
            nltk.download('sentiwordnet', quiet=True)
        except:
            print("❌ No se pudo descargar SentiWordNet")
            raise
    
    from nltk.corpus import sentiwordnet as swn
    SENTIWORDNET_AVAILABLE = True
    print("✅ SentiWordNet cargado correctamente")
except Exception as e:
    print(f"⚠️  NLTK/SentiWordNet no disponible: {e}")
    print("ℹ️  Usando análisis léxico simplificado")
    SENTIWORDNET_AVAILABLE = False
    swn = None

def save_fallback_cache():
    """Guarda la caché de fallback en disco."""
    try:
        with open(FALLBACK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(FALLBACK_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  Error guardando caché: {e}")

def get_fallback_score(lemma):
    """
    Obtiene el puntaje de una palabra que no está en el léxico:
    - Usa la caché si ya existe
    - Si no, intenta usar SentiWordNet si está disponible
    - Si no, usa un diccionario manual básico
    """
    lemma = lemma.lower()

    # 1. Revisar caché primero
    if lemma in FALLBACK_CACHE:
        return FALLBACK_CACHE[lemma]

    # Diccionario manual básico de palabras comunes en español
    MANUAL_SCORES = {
        # Positivos
        'bueno': 0.5, 'buena': 0.5, 'excelente': 0.8, 'genial': 0.7,
        'fantástico': 0.8, 'perfecto': 0.9, 'maravilloso': 0.8,
        'increíble': 0.7, 'mejor': 0.6, 'útil': 0.5,
        
        # Negativos
        'malo': -0.5, 'mala': -0.5, 'terrible': -0.8, 'horrible': -0.9,
        'pésimo': -0.9, 'fatal': -0.8, 'decepcionante': -0.7,
        'inútil': -0.6, 'peor': -0.7, 'problemático': -0.6,
        
        # Neutrales/contextuales
        'normal': 0.0, 'regular': -0.1, 'aceptable': 0.2,
        'suficiente': 0.1, 'adecuado': 0.3, 'correcto': 0.3,
    }

    # 2. Verificar si está en el diccionario manual
    if lemma in MANUAL_SCORES:
        score = MANUAL_SCORES[lemma]
        FALLBACK_CACHE[lemma] = score
        save_fallback_cache()
        return score

    # 3. Intentar usar SentiWordNet si está disponible
    if SENTIWORDNET_AVAILABLE and GOOGLETRANS_AVAILABLE:
        try:
            # Traducir al inglés
            translated = translator.translate(lemma, src='es', dest='en').text.lower()
            
            # Obtener synsets en inglés
            synsets = list(swn.senti_synsets(translated))
            
            if synsets:
                synset = synsets[0]  # el más común
                # Score neto = positivo - negativo
                net_score = synset.pos_score() - synset.neg_score()
                scaled_score = round(net_score * 0.5, 4)
                
                FALLBACK_CACHE[lemma] = scaled_score
                save_fallback_cache()
                return scaled_score
        except Exception as e:
            print(f"⚠️  Error usando SentiWordNet para '{lemma}': {e}")

    # 4. Fallback: análisis léxico básico
    # Buscar patrones de sufijos comunes
    positive_patterns = [
        r'.*(able|ible)$',  # amable, posible
        r'.*(oso|osa)$',    # amoroso, maravillosa
        r'.*(ivo|iva)$',    # creativo, positiva
    ]
    
    negative_patterns = [
        r'.*(oso|osa)$',    # peligroso, asquerosa (algunos son negativos)
        r'.*(ante)$',       # decepcionante
        r'.*(or|ora)$',     # traidor, vengadora (contextual)
    ]
    
    for pattern in positive_patterns:
        if re.match(pattern, lemma):
            score = 0.3
            FALLBACK_CACHE[lemma] = score
            save_fallback_cache()
            return score
    
    for pattern in negative_patterns:
        if re.match(pattern, lemma):
            score = -0.3
            FALLBACK_CACHE[lemma] = score
            save_fallback_cache()
            return score

    # 5. Final fallback: neutro
    FALLBACK_CACHE[lemma] = 0.0
    save_fallback_cache()
    return 0.0

# ================================================================
#  CARGAR SPACY CON FALLBACK
# ================================================================

try:
    nlp = spacy.load("es_core_news_md")
    SPACY_AVAILABLE = True
except Exception as e:
    print(f"⚠️  No se pudo cargar spaCy es_core_news_md: {e}")
    print("ℹ️  Usando tokenizador simple")
    SPACY_AVAILABLE = False
    
    class SimpleTokenizer:
        """Tokenizador simple para cuando spaCy no está disponible"""
        def __init__(self):
            self.stemmer = None
            # Diccionario simple de categorías gramaticales
            self.pos_tags = {}
        
        def __call__(self, text):
            # Tokenización simple por espacios y puntuación
            import re
            tokens = re.findall(r'\b\w+\b', text.lower())
            return SimpleDoc(tokens)
    
    class SimpleDoc:
        """Documento simple para simular spaCy"""
        def __init__(self, tokens):
            self.tokens = [SimpleToken(tok) for tok in tokens]
            self.sents = [SimpleSent(self.tokens)]
    
    class SimpleToken:
        """Token simple para simular spaCy"""
        def __init__(self, text):
            self.text = text
            self.lemma_ = text.lower()
            self.lower_ = text.lower()
            self.pos_ = 'NOUN'  # Asumimos sustantivo por defecto
            self.dep_ = 'dep'   # Dependencia desconocida
            self.head = self     # Auto-referencia
            self.children = []   # Sin hijos
            self.i = 0           # Índice
            
            # Estimar categoría gramatical simple
            if text.endswith(('ar', 'er', 'ir')):
                self.pos_ = 'VERB'
            elif text.endswith(('o', 'a', 'os', 'as')):
                self.pos_ = 'ADJ'
            elif text.endswith(('mente')):
                self.pos_ = 'ADV'
    
    class SimpleSent:
        """Oración simple"""
        def __init__(self, tokens):
            self.text = ' '.join(t.text for t in tokens)
            self.tokens = tokens
    
    nlp = SimpleTokenizer()

# ================================================================
#  FUNCIONES AUXILIARES DE DEPENDENCIAS
# ================================================================

def has_negation(token):
    """
    Nueva versión (NO propagativa).
    La negación aplica SOLO si:
      - El token tiene un hijo negador (no, nunca, jamas)
      - O el token depende de un verbo que tiene un negador directo
    NO revisa el subárbol completo.
    NO revisa lefts arbitrarios.
    NO sube varios niveles.
    """
    if not SPACY_AVAILABLE:
        # Versión simple sin spaCy
        text = token.text.lower()
        return text in NEGATORS or any(child.text.lower() in NEGATORS for child in token.children)
    
    # 1. Negación sobre el propio token (caso ideal)
    for child in token.children:
        if child.lemma_.lower() in NEGATORS and child.dep_ in ["advmod", "case"]:
            return True

    # 2. "no + verbo" afecta objetos del verbo
    if token.head and token.head.pos_ == "VERB":
        for child in token.head.children:
            if child.lemma_.lower() in NEGATORS and child.dep_ == "advmod":
                # Verbo negado, pero no negamos el objeto ni sus modificadores
                if token.pos_ == "VERB":
                    return True
                else:
                    return False

    return False


def get_intensity_multiplier(token):
    """
    Devuelve un multiplicador si el token tiene intensificadores asociados.
    """
    mult = 1.0
    
    if not SPACY_AVAILABLE:
        # Versión simple
        text = token.text.lower()
        if text in INTENSIFIERS:
            return INTENSIFIERS[text]
        return mult
    
    # Versión con spaCy (original)
    for child in token.children:
        if child.dep_ in ("advmod", "amod"):
            if child.text.lower() in INTENSIFIERS:
                mult *= INTENSIFIERS[child.text.lower()]
    
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
    """
    if not SPACY_AVAILABLE:
        # Versión simple por texto
        text = sent.text.lower()
        for conj in ADVERSATIVE_CONJUNCTIONS:
            if conj in text:
                return True, conj
        return False, None
    
    # Versión original con spaCy
    for token in sent:
        if token.text.lower() in ADVERSATIVE_CONJUNCTIONS:
            return True, token.text.lower()
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

def rule_nada_bueno_pattern(token):
    """
    Maneja patrones del tipo:
    - 'nada bueno'
    - 'nada interesante'
    - 'nada positivo'
    - 'no puedo decir nada bueno'
    Si 'nada' modifica a un adjetivo positivo → sentimiento muy negativo.
    """

    # Caso 1: token == 'nada' y tiene hijo ADJ evaluativo
    if token.lemma_ == "nada":
        for child in token.children:
            if child.pos_ == "ADJ" and child.lemma_.lower() in POSITIVE_WORDS:
                return -2.5

    # Caso 2: token es ADJ con hijo 'nada'
    if token.pos_ == "ADJ":
        for child in token.children:
            if child.lemma_ == "nada":
                # invertir la polaridad del adjetivo positivo
                base = POSITIVE_WORDS.get(token.lemma_.lower(), 1)
                return -2.0 * abs(base)

    # Caso 3: 'nada' en el subtree del adjetivo (frases largas)
    subtree_lemmas = {t.lemma_ for t in token.subtree}
    if token.pos_ == "ADJ" and token.lemma_.lower() in POSITIVE_WORDS:
        if "nada" in subtree_lemmas:
            return -2.0 * abs(POSITIVE_WORDS[token.lemma_.lower()])

    return 0

def rule_verb_with_negative_object(token):
    """
    Detecta patrones donde un verbo neutral/positivo tiene como
    objeto un sustantivo negativo:
    
    - recibir [excusa, queja, reclamo]
    - dar [mala noticia]
    - obtener [resultado malo]
    - presentar [problemas]
    """
    # Solo aplica a verbos
    if token.pos_ != "VERB":
        return 0

    negative_nouns = {
        "excusa", "excusas",
        "problema", "problemas",
        "queja", "quejas",
        "crítica", "críticas",
        "error", "errores",
        "mala_noticia", "noticia_mala",
        "malas", "mala"
    }

    # revisar objetos directos u oblicuos
    for child in token.children:
        if child.dep_ in ("obj", "dobj", "obl", "nmod"):
            lemma = child.lemma_.lower()
            
            # Caso 1: el objeto está en tu léxico de negativos
            if lemma in NEGATIVE_WORDS:
                return NEGATIVE_WORDS[lemma] * 1.2   # más fuerte, porque el verbo lo enfatiza
            
            # Caso 2: objeto multinuclear (malas noticias)
            # ejemplo token: "dar", child="noticias", child has amod="malas"
            for subchild in child.children:
                if subchild.pos_ == "ADJ" and subchild.lemma_ in NEGATIVE_WORDS:
                    return NEGATIVE_WORDS[subchild.lemma_] * 1.3

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
        (rule_nada_bueno_pattern, "nada_bueno_pattern"),
        (rule_verb_with_negative_object, "verb_with_negative_object"),

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

def analyze_sentiment_simple(text, debug=True):
    """
    Análisis de sentimientos simplificado para cuando spaCy no está disponible.
    Basado solo en el léxico y palabras clave.
    """
    if not text or not isinstance(text, str):
        return {"text": text, "score": 0.0, "sentiment": "neutro", "details": []}
    
    # Tokenización simple
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    
    total_score = 0.0
    details = []
    
    for word in words:
        lemma = word
        
        # Buscar en léxico
        if lemma in LEXICON:
            base_score = LEXICON[lemma]
            
            # Aplicar negación simple (si la palabra anterior es negador)
            idx = words.index(word)
            if idx > 0 and words[idx-1] in NEGATORS:
                base_score *= -1
            
            # Aplicar intensificadores simples
            if idx > 0 and words[idx-1] in INTENSIFIERS:
                base_score *= INTENSIFIERS[words[idx-1]]
            
            total_score += base_score
    
    # Determinar polaridad
    if total_score > 0.1:
        sentiment = "positivo"
    elif total_score < -0.1:
        sentiment = "negativo"
    else:
        sentiment = "neutro"
    
    if debug:
        return {
            "text": text,
            "score": round(total_score, 3),
            "sentiment": sentiment,
            "details": [{
                "sentence": text,
                "score": round(total_score, 3),
                "rules": ["simple_analysis"]
            }]
        }
    return sentiment

def _analyze_sentiment(text, debug=True):
    """
    Función principal de análisis con fallback automático.
    Usa spaCy si está disponible, si no usa el método simple.
    """
    if not SPACY_AVAILABLE:
        print("⚠️  Usando análisis de sentimientos simplificado (spaCy no disponible)")
        return analyze_sentiment_simple(text, debug)
    
    try:
        # Usar la versión original con spaCy
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
                    # Aplicar reglas gramaticales
                    # (simplificado sin el árbol completo)
                    
                    # Negación simple
                    if has_negation(token):
                        base *= -1
                        sent_debug.append("negation")
                    
                    # Intensificadores
                    mult = get_intensity_multiplier(token)
                    if mult != 1.0:
                        base *= mult
                        sent_debug.append(f"intensifier(x{mult})")
                    
                    sent_score += base

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
            
    except Exception as e:
        print(f"⚠️  Error en análisis con spaCy: {e}")
        print("ℹ️  Cambiando a análisis simplificado")
        return analyze_sentiment_simple(text, debug)

# ================================================================
#  NUEVO ANALIZADOR BASADO EN EL ÁRBOL (POSTORDER)
# ================================================================

def compute_subtree_sentiment(token, visited, debug):
    """
    Evalúa el sentimiento de un subárbol completo usando un recorrido postorder.
    Retorna el score del subárbol.
    
    visited evita que un token se procese varias veces.
    """

    if token.i in visited:
        return 0.0
    visited.add(token.i)

    # --- 1. Recorrer hijos primero (POSTORDER) ---
    child_scores = []
    for child in token.children:
        child_scores.append(compute_subtree_sentiment(child, visited, debug))

    # --- 2. Procesar el propio token ---
    lemma = token.lemma_.lower()
    base_score = 0.0

    if lemma in LEXICON:
        base_score = LEXICON[lemma]

        # Aplicar reglas gramaticales (las mismas funciones que ya tienes)
        adjusted = apply_grammatical_rules(token, base_score, debug)
        token_score = adjusted
    else:
        token_score = 0 # get_fallback_score(lemma)

    # --- 3. Fusionar hijos con el token (promedio ponderado simple) ---
    if child_scores:
        # Unimos el sentimiento del token con sus hijos
        fused = token_score + sum(child_scores)
    else:
        fused = token_score

    return fused

def analyze_sentence_tree(sent):
    """
    Evalúa una oración usando análisis basado en el árbol de dependencias.
    """
    # Obtener el ROOT (la cabeza de la oración)
    root = [t for t in sent if t.dep_ == "ROOT"]
    if not root:
        return 0.0, []

    root = root[0]

    debug = []
    visited = set()

    score = compute_subtree_sentiment(root, visited, debug)

    # Manejar cláusulas adversativas ("pero", "aunque", etc.)
    has_adv, conj = detect_adversative_clauses(sent)
    if has_adv:
        mult = ADVERSATIVE_CONJUNCTIONS.get(conj, 1.0)
        score *= mult
        debug.append(f"adversative({conj}, x{mult})")

    return score, debug

def analyze_sentiment(text, debug=True):
    """
    VERSIÓN PARALELA:
    Analiza sentimiento usando recorrido postorder del árbol.
    NO reemplaza la versión original.
    """
    doc = nlp(text)
    total_score = 0.0
    details = []

    for sent in doc.sents:
        sent_score, sent_debug = analyze_sentence_tree(sent)

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
        "Me gusta mucho esto, es excelente 👍",
        "No me gustó, estuvo terrible",
        "Está bien, pero podría ser mejor",
        "La calidad de las presentaciones fue baja.",
        "No tener problemas",
        "El servicio al cliente fue pésimo y no resolvió mi problema."
    ]  
    
    print("=" * 80)
    print("PRUEBAS DE ANÁLISIS DE SENTIMIENTOS")
    print("=" * 80)
    print(f"spaCy disponible: {SPACY_AVAILABLE}")
    print(f"SentiWordNet disponible: {SENTIWORDNET_AVAILABLE}")
    print(f"googletrans disponible: {GOOGLETRANS_AVAILABLE}")
    print("=" * 80)
    
    for ex in examples:
        print(f"\nTexto: {ex}")
        result = analyze_sentiment(ex, True)
        print(f"Resultado: {result['sentiment']} (score: {result['score']})")
        print("-" * 40)