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
from googletrans import Translator
from nltk.corpus import sentiwordnet as swn
translator = Translator()

nlp = spacy.load("es_core_news_md")

# ================================================================
#  FUNCIONES AUXILIARES DE DEPENDENCIAS
# ================================================================

# def has_negation(token):
#     """
#     Verifica si un token está afectado por una negación.
#     Busca en:
#       - Hijos inmediatos (token.children)
#       - Ancestros hasta 3 niveles
#       - Tokens a la izquierda (lefts)
#       - Subárbol local
#     """
#     for child in token.children:
#         if child.text.lower() in NEGATORS:
#             return True

#     # Buscar en ancestros hasta 3 niveles
#     ancestor = token.head
#     for _ in range(3):
#         if not ancestor or ancestor == token:
#             break
#         if ancestor.text.lower() in NEGATORS:
#             return True
#         ancestor = ancestor.head

#     # Buscar tokens a la izquierda inmediata
#     for left in token.lefts:
#         if left.text.lower() in NEGATORS:
#             return True

#     # Buscar en el subárbol (por ejemplo “no me gusta nada”)
#     for sub in token.subtree:
#         if sub.text.lower() in NEGATORS:
#             return True

#     return False

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
    # 1. Negación sobre el propio token (caso ideal)
    for child in token.children:
        if child.lemma_.lower() in NEGATORS and child.dep_ in ["advmod", "case"]:
            return True

    # 2. "no + verbo" afecta objetos del verbo
    #    ej: "no resolvió mi problema" -> problema NO es negable
    #    pero resolvió sí lo es
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

def _analyze_sentiment(text, debug=True):
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
        # translated = translator.translate(lemma, src='es', dest='en').text.lower()
        # synsets = list(swn.senti_synsets(translated))
        # if synsets:
        #     synset = synsets[0]  # Usa el synset más común
        #     net_score = synset.pos_score() - synset.neg_score()
        #     base_score = net_score * 0.5  # Escala para no dominar el léxico local
        #     adjusted = apply_grammatical_rules(token, base_score, debug)
        #     token_score = adjusted
        # else:
        token_score = 0

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
        # "No disfruté el festival, la programación fue monótona y poco atractiva.",
        # "No disfruté el festival pero la comida estuvo excelente",
        # "La calidad de las presentaciones fue baja.",
        # "No tener problemas",
        # "El servicio al cliente fue pésimo y no resolvió mi problema."
        # "No puedo decir nada bueno de ti",
        # "Nada bueno",
        # "Nada insteresante",
        # "No tienes ningun producto de calidad",
        # "Nada insteresante",
        # "La obra de teatro superó todas mis expectativas."
        #"Los profesores están muy capacitados y comprometidos."
        #"El producto que compré se deshizo al poco tiempo de uso, una decepción que el servicio postventa no mejoró; en lugar de una solución, recibí excusas.",
        "La mayor virtud de esta película es su existencia.El hecho de que podamos jugar con los tópicos más extremos de las identidades patrias (la andaluza y la vasca) sin que nadie se escandalice ni ponga el grito en el cielo indica mucho de nuestra madurez como nación (pese a quien pese). Bueno corrijo: el hecho de que podamos jugar y hacer mofa y befa de los tópicos sobre los vascos y el nacionalismo vasco sin que nadie se escandalice ni ponga el grito en el cielo indica mucho del grado de normalización de ciertas cuestiones que antes eran llagas abiertas siempre dispuestas a sangrar. Y hago esta corrección porque los andaluces han sido motivo de guasa siempre y nunca ha pasado nada.Por esto mismo el planteamiento de Ocho Apellidos Vascos"" es valiente es oportuno y es oportunista. Seguramente sea esa una de las principales razones por la que los españoles hemos acudido en masa en una masa casi sin precedentes a los cines a ver este producto patrocinado por Tele 5. Esa junto con la acertada fecha de estreno (entre los oscar y los blockbusters del verano) y la brutal y ejemplar campaña de marketing la cual aplaudo y celebro.Eso es todo lo que puedo celebrar de este despropósito muy a mi pesar.Siempre digo y repito eso de ""el oscuro placer de ver películas malas y disfrutarlas"" y siempre insisto en que ""no hay que olvidar que el principal propósito del cine es entretener"". Lo digo y lo mantengo. El problema es que ""Ocho Apelidos Vascos"" no es lo suficientemente mala ni lo suficientemente friki ni lo suficientemente disparatada para ser una ""Peli Mala""(como Sharknado o Xanadu o Condemor). Y desgraciadamente no es lo suficientemente entretenida para perdonarle su mediocridad (siempre desde mi punto de vista).Esa es precisamente la palabra que mejor la define: ""Mediocridad"". Es dolorosamente mediocre. Es simple que no sencilla. Es impersonal y lo peor: está hecha sin ganas.Funciona porque el planteamiento interesa y no por novedoso (sacar un elemento de su entorno e introducirlo en otro totalmente ajeno y hostil es uno de los argumentos básicos en la comedia desde que el cine es cine) sino por lo que explicaba al principio.Pero todos los demás elementos apenas encajan o no lo hacen en absoluto. Toda la película es una caída en picado desde un comienzo prometedor a un final vergonzoso pasando por todas las situaciones ""cómicas"" de manual y todos los tópicos más manidos de la comedia de enredo. Que sí César que ya te oigo replicarme: ""que todas las historias están ya contadas"". Tienes  toda la razón pero se pueden seguir contando con un poco de ganas o al menos de formas si no originales sí convincentes. Y volvemos al principal problema de gran parte del cine patrio (y mucho foráneo): el guión. La mayoría de los directores confunden el argumento con el guión. El argumento es el planteamiento el guión el desarrollo. Una grandísima parte de las películas españolas que llevo años sufriendo se desinflan con suerte a la mitad de su recorrido. Pocos son los cineastas que se molestan en desarrollar sus historias menos aún en rematarlas y en hacer que las cosas encajen. Parece que en las escuelas de cine que surgen como champiñones en este país nuestro se olvidan de poner ""El Guión"" como asignatura.La que nos ocupa hoy es un ejemplo más: hay un planteamiento interesante aunque torpemente presentado y ante la incapacidad (o la falta de ganas) de su director de desarrollarlo de una manera convincente (o alocadamente convincente) se refugia en un enredo de principiante del cual no sabe cómo salir aunque todos intuímos (y tememos) desde el principio cómo lo va a hacer: a la fuerza y sin lubricante.Lo que salva este producto del descalabro total es el monologuista Dani Rovira con sus inspirados monólogos y su desparpajo y Karra Elejalde dando vida la único personaje creíble de toda la historia. Carmen Machi muy bien haciendo de Carmen Machi y de Clara Lago...llamarla actriz sería insultar al resto de la profesión (Elsa Pataki incluída).Aún con todo: - sí hay unas cuantas situaciones capaces de arrancar risas e incluso carcajadas y - sí resulta entretenida (a ratos). Pero me duele pensar que ésto es lo que el público está esperando del cine español para llenar las salas. Me duele pensar que el cine también como casi todos los ámbitos de poder está en manos de los mediocres. Y me duele pensar que sean los sub-productos como este los que vayan a salvar al cine español de las aguas en que él sólo se ha sumergido.Robándole una cita a mi amigo Regino Mateo y parafraseándola: ""no es lo mismo hacer películas que hacer cine"
    
    ]  
    for ex in examples:
        print(ex, "\n --> ",analyze_sentiment(ex, True), "\n\n")

