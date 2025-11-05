# knowledge_graph/graph_builder.py
import json
import networkx as nx
import spacy
from datetime import datetime
from typing import Dict, List, Any

class ConversationGraphBuilder:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_md")
        self.graph = nx.DiGraph()
        self.message_nodes = {}
        self.user_nodes = {}
        
    def build_graph_from_chat(self, chat_data: Dict) -> nx.DiGraph:
        """
        Construye el grafo de conocimiento a partir de los datos del chat
        """
        print("🔨 Construyendo grafo de conocimiento...")
        
        # 1. Procesar metadata
        self._add_metadata(chat_data.get('metadata', {}))
        
        # 2. Crear nodos de usuarios y mensajes
        messages = chat_data.get('messages', [])
        for message in messages:
            self._process_message(message)
        
        # 3. Establecer conexiones explícitas (reply_id)
        self._add_explicit_connections(messages)
        
        # 4. Establecer conexiones implícitas (probabilísticas)
        self._add_implicit_connections(messages)
        
        # 5. Reconstruir hilos de conversación
        conversation_threads = self._reconstruct_threads()
        
        return self.graph, conversation_threads
    
    def _add_metadata(self, metadata: Dict):
        """Añade metadata del chat al grafo"""
        self.graph.graph['metadata'] = {
            'chat_name': metadata.get('chat_name', 'unknown'),
            'total_messages': metadata.get('total_messages', 0),
            'date_range': {
                'start': metadata.get('start_date'),
                'end': metadata.get('end_date')
            },
            'built_at': datetime.now().isoformat()
        }
    
    def _process_message(self, message: Dict):
        """Procesa un mensaje y crea los nodos correspondientes"""
        # Verificar que message sea un diccionario
        if not isinstance(message, dict):
            print(f"⚠️  Mensaje no es un diccionario: {type(message)}")
            return
            
        msg_id = message.get('id')
        if not msg_id:
            print(f"⚠️  Mensaje sin ID: {message}")
            return
            
        # Crear nodo de usuario si no existe
        user_id = message.get('sender_id') or message.get('sender_name')
        if user_id and user_id not in self.user_nodes:
            self._create_user_node(user_id, message)
        
        # Crear nodo de mensaje
        self._create_message_node(message)
    
    def _create_user_node(self, user_id: Any, message: Dict):
        """Crea un nodo de usuario"""
        user_data = {
            'node_type': 'user',
            'name': message.get('sender_name', 'Unknown'),
            'username': message.get('sender_username', ''),
            'message_count': 0,
            'first_seen': message.get('date'),
            'last_seen': message.get('date')
        }
        
        self.graph.add_node(f"user_{user_id}", **user_data)
        self.user_nodes[user_id] = f"user_{user_id}"
    
    def _create_message_node(self, message: Dict):
        """Crea un nodo de mensaje con análisis avanzado"""
        msg_id = message.get('id')
        user_id = message.get('sender_id') or message.get('sender_name')
        
        # Análisis con spaCy para lenguaje libre de contexto
        text = message.get('text', '')
        doc = self.nlp(text)
        
        # Extraer entidades y dependencias
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        dependencies = [(token.text, token.dep_, token.head.text) for token in doc]
        
        # Análisis de intención básico
        intention = self._detect_intention(text, doc)
        
        # Patrones de regex (usaremos tu sistema existente)
        from regex.regex_extractor import extract_regex_patterns
        patterns = extract_regex_patterns(text)
        
        message_data = {
            'node_type': 'message',
            'text': text,
            'timestamp': message.get('date'),
            'clean_text': self._clean_text_for_analysis(text),
            'intention': intention,
            'entities': entities,
            'dependencies': dependencies,
            'patterns': patterns,
            'reactions': message.get('reactions', {}),
            'has_media': bool(message.get('media') and message.get('media').get('type')),
            'user_id': user_id
        }
        
        # Añadir nodo al grafo
        node_id = f"msg_{msg_id}"
        self.graph.add_node(node_id, **message_data)
        self.message_nodes[msg_id] = node_id
        
        # Conectar usuario → mensaje
        if user_id in self.user_nodes:
            self.graph.add_edge(
                self.user_nodes[user_id], 
                node_id, 
                relationship='sent',
                weight=1.0,
                timestamp=message.get('date')
            )
    
    def _clean_text_for_analysis(self, text: str) -> str:
        """Limpia el texto para análisis semántico"""
        # Eliminar emojis y caracteres especiales innecesarios
        import re
        cleaned = re.sub(r'[^\w\s.,!?¿¡]', '', text)
        return cleaned.strip()
    
    def _detect_intention(self, text: str, doc) -> str:
        """Detección básica de intención usando análisis lingüístico"""
        text_lower = text.lower()
        
        # Patrones de intención basados en estructura lingüística
        if any(token.text.lower() in ['?', '¿'] for token in doc):
            return 'question'
        elif any(word in text_lower for word in ['vendo', 'vendo', 'disponible', 'tengo']):
            return 'offer'
        elif any(word in text_lower for word in ['busco', 'necesito', 'compro']):
            return 'request'
        elif any(word in text_lower for word in ['gracias', 'thank']):
            return 'gratitude'
        elif any(word in text_lower for word in ['hola', 'hi', 'hello', 'buenos']):
            return 'greeting'
        elif any(token.dep_ == 'ROOT' and token.lemma_ in ['decir', 'informar', 'comunicar'] for token in doc):
            return 'information'
        
        return 'statement'
    
    def _add_explicit_connections(self, messages: List[Dict]):
        """Añade conexiones explícitas basadas en reply_id"""
        for message in messages:
            msg_id = message.get('id')
            reply_id = message.get('reply_id')
            
            if reply_id and msg_id in self.message_nodes and reply_id in self.message_nodes:
                self.graph.add_edge(
                    self.message_nodes[reply_id],
                    self.message_nodes[msg_id],
                    relationship='reply_to',
                    weight=1.0,
                )
    
    def _add_implicit_connections(self, messages: List[Dict]):
        """Añade conexiones implícitas basadas en probabilidades"""
        print("🔍 Calculando conexiones implícitas...")
        
        # Ordenar mensajes por timestamp
        sorted_messages = sorted(messages, key=lambda x: x.get('date', ''))
        
        for i, current_msg in enumerate(sorted_messages):
            current_id = current_msg.get('id')
            if current_id not in self.message_nodes:
                continue
                
            # Buscar mensajes anteriores como posibles padres
            for j in range(max(0, i-10), i):  # Ventana de 10 mensajes anteriores
                previous_msg = sorted_messages[j]
                previous_id = previous_msg.get('id')
                
                if (previous_id in self.message_nodes and 
                    current_id != previous_id and
                    not self.graph.has_edge(self.message_nodes[previous_id], self.message_nodes[current_id])):
                    
                    probability = self._calculate_reply_probability(previous_msg, current_msg)
                    
                    if probability > 0.3:  # Threshold
                        self.graph.add_edge(
                            self.message_nodes[previous_id],
                            self.message_nodes[current_id],
                            relationship='likely_reply_to',
                            weight=probability,
                            probability=probability
                        )
    
    def _calculate_reply_probability(self, msg1: Dict, msg2: Dict) -> float:
        """Calcula la probabilidad de que msg2 sea respuesta de msg1"""
        factors = {
            'temporal': self._temporal_proximity(msg1, msg2),
            'semantic': self._semantic_similarity(msg1, msg2),
            'social': self._social_connection(msg1, msg2),
            'structural': self._structural_patterns(msg1, msg2)
        }
        
        # Combinación de factores (media ponderada)
        weights = {'temporal': 0.4, 'semantic': 0.3, 'social': 0.2, 'structural': 0.1}
        total_prob = sum(factors[factor] * weights[factor] for factor in factors)
        
        return total_prob
    
    def _temporal_proximity(self, msg1: Dict, msg2: Dict) -> float:
        """Calcula proximidad temporal con lógica difusa"""
        try:
            time1 = datetime.fromisoformat(msg1.get('date', '').replace('Z', '+00:00'))
            time2 = datetime.fromisoformat(msg2.get('date', '').replace('Z', '+00:00'))
            
            time_diff = abs((time2 - time1).total_seconds() / 60)  # Diferencia en minutos
            
            # Lógica difusa para proximidad temporal
            if time_diff <= 2:   # 0-2 minutos: alta probabilidad
                return 1.0
            elif time_diff <= 5: # 2-5 minutos: media-alta
                return 0.7
            elif time_diff <= 10: # 5-10 minutos: media
                return 0.4
            elif time_diff <= 30: # 10-30 minutos: baja
                return 0.2
            else:                # >30 minutos: muy baja
                return 0.1
                
        except:
            return 0.1
    
    def _semantic_similarity(self, msg1: Dict, msg2: Dict) -> float:
        """Calcula similitud semántica entre mensajes"""
        text1 = msg1.get('text', '')
        text2 = msg2.get('text', '')
        
        if not text1 or not text2:
            return 0.0
        
        # Análisis básico de similitud (podría mejorarse con embeddings)
        doc1 = self.nlp(text1.lower())
        doc2 = self.nlp(text2.lower())
        
        # Similitud léxica básica
        words1 = set(token.lemma_ for token in doc1 if not token.is_stop and not token.is_punct)
        words2 = set(token.lemma_ for token in doc2 if not token.is_stop and not token.is_punct)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        # Boost si hay patrones similares
        from regex.regex_extractor import extract_regex_patterns
        patterns1 = extract_regex_patterns(text1)
        patterns2 = extract_regex_patterns(text2)
        
        pattern_similarity = self._compare_patterns(patterns1, patterns2)
        
        return min(1.0, similarity + pattern_similarity * 0.3)
    
    def _compare_patterns(self, patterns1: Dict, patterns2: Dict) -> float:
        """Compara patrones de regex entre mensajes"""
        common_patterns = 0
        total_patterns = 0
        
        for category in patterns1:
            if category in patterns2:
                set1 = set(str(p) for p in patterns1[category])
                set2 = set(str(p) for p in patterns2[category])
                common = set1.intersection(set2)
                common_patterns += len(common)
                total_patterns += len(set1.union(set2))
        
        return common_patterns / total_patterns if total_patterns > 0 else 0.0
    
    def _social_connection(self, msg1: Dict, msg2: Dict) -> float:
        """Analiza conexiones sociales entre mensajes"""
        # Menciones cruzadas
        text1 = msg1.get('text', '').lower()
        text2 = msg2.get('text', '').lower()
        
        user1 = msg1.get('sender_name', '').lower()
        user2 = msg2.get('sender_name', '').lower()
        
        # Si msg2 menciona al usuario de msg1
        if user1 in text2:
            return 0.8
        # Si msg1 menciona al usuario de msg2
        elif user2 in text1:
            return 0.6
        # Misma conversación entre mismos usuarios
        elif user1 == user2:
            return 0.3
        
        return 0.1
    
    def _structural_patterns(self, msg1: Dict, msg2: Dict) -> float:
        """Analiza patrones estructurales de conversación"""
        # Pregunta → Respuesta
        text1 = msg1.get('text', '')
        intention1 = self._detect_intention(text1, self.nlp(text1))
        intention2 = self._detect_intention(msg2.get('text', ''), self.nlp(msg2.get('text', '')))
        
        if intention1 == 'question' and intention2 != 'question':
            return 0.7
        
        # Agradecimiento → De nada / Respuesta positiva
        if intention1 == 'gratitude' and intention2 in ['statement', 'information']:
            return 0.5
        
        return 0.1
    
    def _reconstruct_threads(self) -> Dict[str, List]:
        """Reconstruye hilos de conversación a partir del grafo"""
        print("🧵 Reconstruyendo hilos de conversación...")
        
        threads = {}
        
        # Encontrar mensajes raíz (sin padres o con muy pocos)
        root_messages = []
        for node_id in self.message_nodes.values():
            in_edges = list(self.graph.in_edges(node_id))
            # Solo contar edges de tipo reply
            reply_edges = [edge for edge in in_edges if 
                          self.graph.edges[edge].get('relationship') in ['reply_to', 'likely_reply_to']]
            
            if len(reply_edges) == 0:
                root_messages.append(node_id)
        
        # Para cada mensaje raíz, reconstruir el hilo completo
        for i, root_msg in enumerate(root_messages):
            thread_id = f"thread_{i+1}"
            thread_messages = self._bfs_traverse(root_msg)
            
            if len(thread_messages) > 1:  # Solo hilos con al menos 2 mensajes
                threads[thread_id] = {
                    'root_message': root_msg,
                    'messages': thread_messages,
                    'depth': self._calculate_thread_depth(thread_messages),
                    'participants': list(set(msg['user_id'] for msg in thread_messages if msg.get('user_id')))
                }
        
        return threads
    
    def _bfs_traverse(self, start_node: str) -> List[Dict]:
        """Recorrido BFS para encontrar todos los mensajes conectados"""
        visited = set()
        queue = [start_node]
        thread_messages = []
        
        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                # Añadir información del mensaje actual
                node_data = self.graph.nodes[current]
                thread_messages.append({
                    'node_id': current,
                    'text': node_data.get('text', ''),
                    'timestamp': node_data.get('timestamp'),
                    'user_id': node_data.get('user_id'),
                    'intention': node_data.get('intention', '')
                })
                
                # Añadir hijos (respuestas)
                for successor in self.graph.successors(current):
                    edge_data = self.graph.edges[current, successor]
                    if edge_data.get('relationship') in ['reply_to', 'likely_reply_to']:
                        if successor not in visited:
                            queue.append(successor)
        
        return thread_messages
    
    def _calculate_thread_depth(self, thread_messages: List[Dict]) -> int:
        """Calcula la profundidad máxima del hilo"""
        if not thread_messages:
            return 0
        
        # Para simplificar, usamos el número de mensajes como indicador de profundidad
        return len(thread_messages)
    
    def save_graph(self, filename: str):
        """Guarda el grafo en formato JSON"""
        graph_data = {
            'metadata': self.graph.graph,
            'nodes': {},
            'edges': []
        }
        
        # Nodos
        for node_id, node_data in self.graph.nodes(data=True):
            graph_data['nodes'][node_id] = node_data
        
        # Aristas
        for source, target, edge_data in self.graph.edges(data=True):
            graph_data['edges'].append({
                'source': source,
                'target': target,
                'data': edge_data
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 Grafo guardado en: {filename}")