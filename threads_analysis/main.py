# threads_analysis/main.py
import json
import os
from threads_analysis.knowledge_graph import ConversationGraphBuilder
from threads_analysis.thread_analyzer import ThreadAnalyzer

def process_chat_for_knowledge_graph(chat_filename: str, output_dir: str = "threads_analysis_results"):
    """
    Procesa un archivo de chat y genera el grafo de conocimiento
    """
    print(f"🚀 Procesando: {chat_filename}")
    
    # Cargar datos del chat
    from regex.pattern_analyzer import load_chat_messages
    messages = load_chat_messages(chat_filename)
    
    if not messages:
        print(f"❌ No se pudieron cargar mensajes desde {chat_filename}")
        return None, None, None
    
    # Obtener metadata del archivo original si existe
    try:
        with open(chat_filename, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
            if isinstance(original_data, dict) and 'metadata' in original_data:
                metadata = original_data['metadata']
            else:
                metadata = {}
    except:
        metadata = {}
    
    chat_data = {
        'metadata': {
            'chat_name': metadata.get('chat_name', os.path.splitext(os.path.basename(chat_filename))[0]),
            'total_messages': len(messages),
            'original_metadata': metadata
        },
        'messages': messages
    }
    
    print(f"📊 Cargados {len(messages)} mensajes para análisis")
    
    try:
        # Construir grafo
        builder = ConversationGraphBuilder()
        graph, threads = builder.build_graph_from_chat(chat_data)
        
        # Analizar hilos
        analyzer = ThreadAnalyzer(builder)
        thread_analysis = analyzer.analyze_conversation_threads(threads)
        
        # Guardar resultados
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(chat_filename))[0]
        
        # Guardar grafo
        graph_filename = os.path.join(output_dir, f"{base_name}_graph.json")
        builder.save_graph(graph_filename)
        
        # Guardar hilos
        threads_filename = os.path.join(output_dir, f"{base_name}_threads.json")
        with open(threads_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'threads': threads,
                'analysis': thread_analysis
            }, f, ensure_ascii=False, indent=2, default=str)
        
        # Guardar análisis
        analysis_filename = os.path.join(output_dir, f"{base_name}_analysis.json")
        with open(analysis_filename, 'w', encoding='utf-8') as f:
            json.dump(thread_analysis, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Procesamiento completado:")
        print(f"   - Grafo: {graph_filename}")
        print(f"   - Hilos: {threads_filename}")
        print(f"   - Análisis: {analysis_filename}")
        print(f"   - Total nodos: {len(graph.nodes())}")
        print(f"   - Total aristas: {len(graph.edges())}")
        print(f"   - Hilos reconstruidos: {len(threads)}")
        
        return graph, threads, thread_analysis
        
    except Exception as e:
        print(f"❌ Error en procesamiento de {chat_filename}: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

# Ejemplo de uso
if __name__ == "__main__":
    # Procesar todos los chats en la carpeta
    chat_files = [f for f in os.listdir('chats') if f.endswith('.json')]
    
    for chat_file in chat_files:
        process_chat_for_knowledge_graph(chat_file)