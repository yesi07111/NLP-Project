import spacy
nlp = spacy.load("es_core_news_md")

def extract_dep_patterns(sentence):
    """
    Extrae patrones basados en dependencias para una oración.
    Devuelve una lista de patrones simbólicos.
    """
    doc = nlp(sentence)
    patterns = []

    for sent in doc.sents:
        for token in sent:
            head = token.head.lemma_.lower()
            lemma = token.lemma_.lower()
            dep  = token.dep_

            # Patrón directo head -> token
            patterns.append(("HEAD_DEP", head, dep, lemma))

            # Patrón de hijos
            for child in token.children:
                patterns.append(("CHILD_DEP", lemma, child.dep_, child.lemma_.lower()))

            # Patrón de subtree de adjetivos/verbos
            if token.pos_ in ("ADJ", "VERB"):
                subtree = tuple(sorted([t.lemma_.lower() for t in token.subtree]))
                patterns.append(("SUBTREE", lemma, subtree))

    return patterns
