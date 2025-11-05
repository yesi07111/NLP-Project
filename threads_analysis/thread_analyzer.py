# knowledge_graph/thread_analyzer.py
import json
from typing import Dict, List, Any
from collections import Counter

class ThreadAnalyzer:
    def __init__(self, graph_builder):
        self.graph_builder = graph_builder
        self.threads = {}
    
    def analyze_conversation_threads(self, threads: Dict) -> Dict[str, Any]:
        """Analiza los hilos de conversación reconstruidos"""
        print("📊 Analizando hilos de conversación...")
        
        analysis = {
            'thread_metrics': self._calculate_thread_metrics(threads),
            'user_engagement': self._analyze_user_engagement(threads),
            'conversation_patterns': self._analyze_conversation_patterns(threads),
            'temporal_analysis': self._analyze_temporal_patterns(threads),
            'content_analysis': self._analyze_content_patterns(threads)
        }
        
        return analysis
    
    def _calculate_thread_metrics(self, threads: Dict) -> Dict:
        """Calcula métricas generales de los hilos"""
        total_threads = len(threads)
        thread_lengths = [len(thread_data['messages']) for thread_data in threads.values()]
        
        return {
            'total_threads': total_threads,
            'avg_thread_length': sum(thread_lengths) / len(thread_lengths) if thread_lengths else 0,
            'max_thread_length': max(thread_lengths) if thread_lengths else 0,
            'min_thread_length': min(thread_lengths) if thread_lengths else 0,
            'threads_by_length': Counter(thread_lengths)
        }
    
    def _analyze_user_engagement(self, threads: Dict) -> Dict:
        """Analiza el engagement de usuarios en los hilos"""
        user_participation = Counter()
        user_thread_starts = Counter()
        
        for thread_id, thread_data in threads.items():
            participants = thread_data.get('participants', [])
            root_user = thread_data['messages'][0]['user_id'] if thread_data['messages'] else None
            
            for participant in participants:
                user_participation[participant] += 1
            
            if root_user:
                user_thread_starts[root_user] += 1
        
        return {
            'most_active_users': user_participation.most_common(10),
            'thread_starters': user_thread_starts.most_common(10),
            'user_engagement_score': dict(user_participation)
        }
    
    def _analyze_conversation_patterns(self, threads: Dict) -> Dict:
        """Analiza patrones de conversación en los hilos"""
        intention_sequences = []
        response_times = []
        
        for thread_data in threads.values():
            messages = thread_data['messages']
            thread_intentions = [msg.get('intention', 'unknown') for msg in messages]
            intention_sequences.append(thread_intentions)
            
            # Calcular tiempos de respuesta aproximados
            for i in range(1, len(messages)):
                try:
                    time1 = messages[i-1]['timestamp']
                    time2 = messages[i]['timestamp']
                    # Conversión simplificada de tiempo
                    if time1 and time2:
                        response_times.append((time2, time1))  # Para cálculo posterior
                except:
                    pass
        
        # Análisis de secuencias comunes
        common_patterns = Counter()
        for sequence in intention_sequences:
            if len(sequence) >= 2:
                pattern = ' → '.join(sequence[:3])  # Patrones de 3 intenciones
                common_patterns[pattern] += 1
        
        return {
            'common_intention_patterns': common_patterns.most_common(10),
            'total_conversation_patterns': len(intention_sequences)
        }
    
    def _analyze_temporal_patterns(self, threads: Dict) -> Dict:
        """Analiza patrones temporales en los hilos"""
        thread_start_times = []
        thread_durations = []
        
        for thread_data in threads.values():
            messages = thread_data['messages']
            if messages:
                start_time = messages[0]['timestamp']
                end_time = messages[-1]['timestamp']
                
                if start_time and end_time:
                    thread_start_times.append(start_time)
                    # Duración aproximada (simplificada)
                    thread_durations.append((end_time, start_time))  # Para cálculo posterior
        
        return {
            'thread_start_times': thread_start_times[:10],  # Primeros 10 para muestra
            'avg_thread_duration': 'N/A',  # Podría calcularse con datetime
            'threads_by_time_of_day': self._categorize_by_time(thread_start_times)
        }
    
    def _categorize_by_time(self, timestamps: List[str]) -> Dict:
        """Categoriza hilos por hora del día"""
        time_categories = Counter()
        
        for timestamp in timestamps:
            try:
                hour = int(timestamp.split('T')[1].split(':')[0])
                if 6 <= hour < 12:
                    time_categories['morning'] += 1
                elif 12 <= hour < 18:
                    time_categories['afternoon'] += 1
                elif 18 <= hour < 24:
                    time_categories['evening'] += 1
                else:
                    time_categories['night'] += 1
            except:
                pass
        
        return dict(time_categories)
    
    def _analyze_content_patterns(self, threads: Dict) -> Dict:
        """Analiza patrones de contenido en los hilos"""
        all_messages = []
        for thread_data in threads.values():
            all_messages.extend(thread_data['messages'])
        
        # Análisis básico de contenido
        text_lengths = [len(msg.get('text', '')) for msg in all_messages]
        intentions = [msg.get('intention', 'unknown') for msg in all_messages]
        
        return {
            'avg_message_length': sum(text_lengths) / len(text_lengths) if text_lengths else 0,
            'intention_distribution': Counter(intentions),
            'total_messages_analyzed': len(all_messages)
        }