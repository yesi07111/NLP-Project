#sentiment_markov_chain_binary.py
import pandas as pd
import numpy as np
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
from gensim.models import Word2Vec
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from collections import defaultdict, Counter
import pickle
import os
from typing import List, Dict, Tuple, Optional

class SentimentMarkovChain:
    """
    Cadena de Markov para análisis de sentimientos usando Word2Vec para vectorización.
    """

    def __init__(self, vector_size=100, window=5, min_count=2, workers=4):
        """
        Inicializar la cadena de Markov.

        Args:
            vector_size: Dimensión de los vectores de Word2Vec
            window: Ventana de contexto para Word2Vec
            min_count: Mínima frecuencia de palabras para incluir en el modelo
            workers: Número de hilos para entrenamiento
        """
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.workers = workers

        # Inicializar componentes
        self.stemmer = SnowballStemmer('spanish')
        self.stop_words = set(stopwords.words('spanish'))

        # Modelos y estructuras de datos
        self.word2vec_model = None
        self.transition_matrices = {}
        self.vocabulary = set()
        self.sentiment_mapping = { 0: 'negativo', 1: 'positivo'}

    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocesar texto: tokenización, eliminación de stopwords, stemming.

        Args:
            text: Texto a preprocesar

        Returns:
            Lista de tokens procesados
        """
        if not isinstance(text, str):
            return []

        # Convertir a minúsculas
        text = text.lower()

        # Eliminar caracteres especiales y números
        text = re.sub(r'[^\w\sáéíóúñ]', ' ', text)
        text = re.sub(r'\d+', '', text)

        # Tokenizar
        tokens = word_tokenize(text, language='spanish')

        # Filtrar stopwords y palabras cortas, aplicar stemming
        processed_tokens = []
        for token in tokens:
            if len(token) > 2 and token not in self.stop_words:
                stemmed_token = self.stemmer.stem(token)
                processed_tokens.append(stemmed_token)

        return processed_tokens

    def train_word2vec(self, texts: List[List[str]]) -> None:
        """
        Entrenar modelo Word2Vec con los textos procesados.

        Args:
            texts: Lista de listas de tokens
        """
        print("Entrenando modelo Word2Vec...")

        # Crear modelo Word2Vec
        self.word2vec_model = Word2Vec(
            sentences=texts,
            vector_size=self.vector_size,
            window=self.window,
            min_count=self.min_count,
            workers=self.workers,
            sg=1,  # Skip-gram
            hs=0,  # Negative sampling
            negative=10,
            epochs=30
        )

        # Construir vocabulario
        self.vocabulary = set(self.word2vec_model.wv.index_to_key)
        print(f"Modelo Word2Vec entrenado con vocabulario de {len(self.vocabulary)} palabras")

    def build_transition_matrices(self, texts: List[List[str]], sentiments: List[int]) -> None:
        """
        Construir matrices de transición para cada sentimiento usando vectores Word2Vec.

        Args:
            texts: Lista de listas de tokens procesados
            sentiments: Lista de sentimientos correspondientes
        """
        print("Construyendo matrices de transición...")

        # Inicializar matrices de transición para cada sentimiento
        sentiment_matrices = {0: defaultdict(Counter), 1: defaultdict(Counter)}

        for tokens, sentiment in zip(texts, sentiments):
            if len(tokens) < 2:
                continue

            for i in range(len(tokens) - 1):
                current_word = tokens[i]
                next_word = tokens[i + 1]

                if current_word in self.vocabulary and next_word in self.vocabulary:
                    sentiment_matrices[sentiment][current_word][next_word] += 1

        # Normalizar matrices de transición
        for sentiment in [0, 1]:
            total_transitions = sum(sum(word_counts.values()) for word_counts in sentiment_matrices[sentiment].values())
            if total_transitions > 0:
                for current_word in sentiment_matrices[sentiment]:
                    total_from_current = sum(sentiment_matrices[sentiment][current_word].values())
                    for next_word in sentiment_matrices[sentiment][current_word]:
                        sentiment_matrices[sentiment][current_word][next_word] /= total_from_current

        self.transition_matrices = sentiment_matrices
        print("Matrices de transición construidas para todos los sentimientos")

    def get_word_vector(self, word: str) -> np.ndarray:
        """
        Obtener vector Word2Vec de una palabra.

        Args:
            word: Palabra para la que obtener el vector

        Returns:
            Vector de la palabra o vector de ceros si no existe
        """
        if word in self.vocabulary:
            return self.word2vec_model.wv[word]
        return np.zeros(self.vector_size)

    def predict_sentiment_sequence(self, tokens: List[str]) -> Dict[str, float]:
        """
        Predecir sentimiento basado en la secuencia de palabras usando cadena de Markov.

        Args:
            tokens: Lista de tokens procesados

        Returns:
            Diccionario con probabilidades para cada sentimiento
        """
        if len(tokens) < 2 or not self.transition_matrices:
            return {0: 0.50, 1: 0.50}

        sentiment_scores = { 0: 0.0, 1: 0.0}

        # Calcular probabilidad basada en transiciones
        for i in range(len(tokens) - 1):
            current_word = tokens[i]
            next_word = tokens[i + 1]

            if current_word in self.vocabulary and next_word in self.vocabulary:
                for sentiment in [ 0, 1]:
                    if current_word in self.transition_matrices[sentiment]:
                        prob = self.transition_matrices[sentiment][current_word].get(next_word, 0)
                        sentiment_scores[sentiment] += prob

        # Normalizar probabilidades
        total = sum(sentiment_scores.values())
        if total > 0:
            for sentiment in sentiment_scores:
                sentiment_scores[sentiment] /= total
        else:
            # Si no hay transiciones válidas, asignar probabilidades uniformes
            for sentiment in sentiment_scores:
                sentiment_scores[sentiment] = 1/2

        return sentiment_scores

    def predict_sentiment(self, text: str) -> int:
        """
        Predecir sentimiento de un texto.

        Args:
            text: Texto a clasificar

        Returns:
            Sentimiento predicho (-1, 0, 1)
        """
        tokens = self.preprocess_text(text)
        scores = self.predict_sentiment_sequence(tokens)

        # También considerar palabras individuales usando vectores Word2Vec
        word_sentiments = []
        for token in tokens:
            if token in self.vocabulary:
                # Calcular similitud con palabras de entrenamiento positivas/negativas
                vector = self.get_word_vector(token)
                # Aquí podrías implementar una clasificación basada en vectores vecinos
                # Por simplicidad, usaremos solo la cadena de Markov
                pass

        # Retornar el sentimiento con mayor probabilidad
        return max(scores, key=scores.get)

    def train(self, texts: List[str], sentiments: List[int]) -> None:
        """
        Entrenar el modelo completo.

        Args:
            texts: Lista de textos
            sentiments: Lista de sentimientos correspondientes
        """
        print("Procesando textos...")
        processed_texts = [self.preprocess_text(text) for text in texts]

        # Filtrar textos vacíos
        valid_indices = [i for i, tokens in enumerate(processed_texts) if len(tokens) > 0]
        processed_texts = [processed_texts[i] for i in valid_indices]
        sentiments = [sentiments[i] for i in valid_indices]

        print(f"Procesados {len(processed_texts)} textos válidos")

        # Entrenar Word2Vec
        self.train_word2vec(processed_texts)

        # Construir matrices de transición
        self.build_transition_matrices(processed_texts, sentiments)

    def save_model(self, filepath: str) -> None:
        """
        Guardar el modelo entrenado.

        Args:
            filepath: Ruta donde guardar el modelo
        """
        model_data = {
            'transition_matrices': self.transition_matrices,
            'vocabulary': self.vocabulary,
            'vector_size': self.vector_size,
            'word2vec_model': self.word2vec_model
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Modelo guardado en: {filepath}")

    def load_model(self, filepath: str) -> None:
        """
        Cargar modelo entrenado.

        Args:
            filepath: Ruta del modelo guardado
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.transition_matrices = model_data['transition_matrices']
        self.vocabulary = model_data['vocabulary']
        self.vector_size = model_data['vector_size']
        self.word2vec_model = model_data['word2vec_model']

        print(f"Modelo cargado desde: {filepath}")


def extract_columns_dataset():
    # Cargar datos
    df = pd.read_csv('utils/sentiments/datasets/dataset.csv')
    
    return df['texto'].tolist() , df['sentimiento'].tolist()

def extract_columns_reviews_filmaffinity():
    df = pd.read_csv('utils/sentiments/datasets/reviews_filmaffinity_ok.csv')
    
    return df['review_text'].tolist() , df['review_rate'].apply(lambda x: 1 if x >= 6 else 0).tolist()

def main():
    """
    Función principal para entrenar y evaluar el modelo.
    """
    # Cargar datos
    print("Cargando datos...")
    texts, sentiments = extract_columns_reviews_filmaffinity()

    # Dividir en entrenamiento y prueba
    train_texts, test_texts, train_sentiments, test_sentiments = train_test_split(
        texts, sentiments, test_size=0.2, random_state=42, stratify=sentiments
    )

    print(f"Datos de entrenamiento: {len(train_texts)}")
    print(f"Datos de prueba: {len(test_texts)}")

    # Crear y entrenar modelo
    markov_chain = SentimentMarkovChain(vector_size=100, window=5, min_count=2)

    print("Entrenando modelo...")
    markov_chain.train(train_texts, train_sentiments)

    # Evaluar modelo
    print("Evaluando modelo...")
    predictions = []
    for text in test_texts:
        pred = markov_chain.predict_sentiment(text)
        predictions.append(pred)

    # Calcular métricas
    accuracy = accuracy_score(test_sentiments, predictions)
    print(f"Precisión del modelo: {accuracy:.4f}")

    # Reporte de clasificación
    print("\nReporte de clasificación:")
    print(classification_report(test_sentiments, predictions,
                              target_names=['Negativo (0)', 'Positivo (1)']))

    # Guardar modelo
    os.makedirs('utils/sentiments/models', exist_ok=True)
    markov_chain.save_model('utils/sentiments/models/sentiment_markov_chain.pkl')

    # Ejemplo de uso
    test_text = "Este proyecto está increíble, me encanta trabajar en él"
    prediction = markov_chain.predict_sentiment(test_text)
    print(f"\nTexto de ejemplo: '{test_text}'")
    print(f"Predicción: {markov_chain.sentiment_mapping[prediction]}")

if __name__ == "__main__":
    # Descargar recursos de NLTK si es necesario
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Descargando recursos de NLTK...")
        nltk.download('punkt')
        nltk.download('stopwords')

    main()
