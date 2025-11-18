import re
import os
import json
from datetime import datetime
from typing import Dict, List, Any


def load_chat_messages(chat_filename: str) -> List[Dict]:
    """
    Carga mensajes desde un archivo JSON en la carpeta chats.
    
    Args:
        chat_filename: Nombre del archivo JSON en la carpeta chats
        
    Returns:
        Lista de mensajes cargados desde el archivo
    """
    try:
        # Primero intentar con la ruta completa
        with open(chat_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Si el archivo tiene estructura con metadata y messages
            if isinstance(data, dict) and 'messages' in data:
                return data.get('messages', [])
            # Si el archivo es directamente una lista de mensajes
            elif isinstance(data, list):
                return data
            else:
                print(f"❌ Formato no reconocido en {chat_filename}")
                return []
    except FileNotFoundError:
        # Si no encuentra, intentar en la carpeta chats
        chat_path = os.path.join('chats', chat_filename)
        try:
            with open(chat_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'messages' in data:
                    return data.get('messages', [])
                elif isinstance(data, list):
                    return data
                else:
                    print(f"❌ Formato no reconocido en {chat_path}")
                    return []
        except Exception as e:
            print(f"❌ Archivo {chat_filename} no encontrado: {e}")
            return []
    except Exception as e:
        print(f"❌ Error cargando {chat_filename}: {e}")
        return []
    
def save_patterns_summary(chat_filename: str, messages: List[Dict]):
    """
    Guarda el resumen de patrones en un archivo JSON.
    
    Args:
        chat_filename: Nombre del archivo original
        messages: Lista de mensajes analizados
        
    Returns:
        Datos de patrones guardados
    """    
    patterns_data = create_patterns_summary(messages)
    
    base_name = os.path.splitext(os.path.basename(chat_filename))[0]
    patterns_filename = f"{base_name}_patterns.json"
    # CAMBIO: Guardar directamente en threads_analysis_results
    patterns_path = os.path.join('threads_analysis_results', patterns_filename)
    
    # Asegurar que existe la carpeta threads_analysis_results
    os.makedirs('threads_analysis_results', exist_ok=True)
    
    with open(patterns_path, 'w', encoding='utf-8') as f:
        json.dump(patterns_data, f, ensure_ascii=False, indent=2)
    
    print(f"Resumen de patrones guardado: {patterns_path}")
    return patterns_data

def create_patterns_summary(messages: List[Dict], chat_filename: str = None) -> Dict[str, Any]:
    """
    Crea un resumen completo de todos los patrones encontrados en los mensajes.
    
    Args:
        messages: Lista de mensajes a analizar
        chat_filename: Nombre del archivo de chat (opcional)
        
    Returns:
        Diccionario con el resumen completo de patrones
    """
    from regex.regex_extractor import extract_regex_patterns, analyze_text_patterns
    
    # Obtener el nombre real del chat
    actual_chat_names = set()
    for msg in messages:
        chat_name = msg.get('chat_name')
        if chat_name and chat_name != 'unknown':
            actual_chat_names.add(chat_name)
    
    # Si no encontramos nombres válidos, usar el nombre del archivo
    if not actual_chat_names and chat_filename:
        base_name = os.path.splitext(os.path.basename(chat_filename))[0]
        # Limpiar el nombre (remover fechas y otros patrones)
        clean_name = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}$', '', base_name)
        clean_name = re.sub(r'_+', ' ', clean_name).strip()
        if clean_name:
            actual_chat_names.add(clean_name)
    
    # Si todavía no hay nombres, usar "Chat"
    if not actual_chat_names:
        actual_chat_names.add("Chat")
    
    summary = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_messages": len(messages),
            "chats_analyzed": list(actual_chat_names),
            "analysis_version": "regex_patterns_v1"
        },
        "extracted_patterns": {
            "financial": extract_financial_patterns(messages),
            "temporal": extract_temporal_patterns(messages),
            "social": extract_social_patterns(messages),
            "contact": extract_contact_patterns(messages),
            "technical": extract_technical_patterns(messages)
        },
        "message_analysis": [],
        "conversation_metrics": calculate_conversation_metrics(messages)
    }
    
    # Analizar cada mensaje individualmente
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            # Usar el primer nombre de chat válido para todos los mensajes
            chat_name = list(actual_chat_names)[0] if actual_chat_names else "Chat"
            summary["message_analysis"].append({
                "message_id": msg.get('id'),
                "chat_name": chat_name,
                "timestamp": msg.get('date'),
                "patterns_detected": patterns,
                "enriched_text": analyze_text_patterns(text)
            })
    
    return summary

def extract_financial_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume patrones financieros de todos los mensajes.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    financial_data = {
        "explicit_currencies": [],
        "implicit_prices": [],
        "currency_breakdown": {},
        "total_monetary_references": 0
    }
    
    all_currencies = []
    all_prices = []
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            all_currencies.extend(patterns.get('monedas_explicitas', []))
            all_prices.extend(patterns.get('precios_implicitos', []))
    
    # Eliminar duplicados
    financial_data["explicit_currencies"] = list(set(all_currencies))
    financial_data["implicit_prices"] = list(set(all_prices))
    financial_data["total_monetary_references"] = len(all_currencies) + len(all_prices)
    
    # Breakdown por tipo de moneda
    for currency in all_currencies:
        for coin_type in ['mlc', 'mn', 'usd', 'cup', 'eur']:
            if coin_type in str(currency).lower():
                financial_data["currency_breakdown"][coin_type] = financial_data["currency_breakdown"].get(coin_type, 0) + 1
                break
    
    return financial_data

# def extract_temporal_patterns(messages: List[Dict]) -> Dict:
#     """
#     Extrae y resume patrones temporales de todos los mensajes.
#     """
#     from regex.regex_extractor import extract_regex_patterns
    
#     temporal_data = {
#         "absolute_dates": [],
#         "relative_references": [],
#         "time_expressions": [],
#         "total_temporal_references": 0
#     }
    
#     all_dates = []
    
#     for msg in messages:
#         text = msg.get('text', '')
#         if text:
#             patterns = extract_regex_patterns(text)
#             # Recoger todas las fechas de diferentes categorias
#             for key in patterns:
#                 if key.startswith('dates_'):
#                     all_dates.extend(patterns[key])
    
#     temporal_data["absolute_dates"] = [d for d in all_dates if re.search(r'\d', str(d))]
#     temporal_data["relative_references"] = [d for d in all_dates if any(kw in str(d).lower() for kw in 
#         ['hoy', 'ayer', 'mañana', 'semana', 'mes', 'año', 'próximo', 'pasado'])]
#     temporal_data["time_expressions"] = list(set(all_dates))
#     temporal_data["total_temporal_references"] = len(all_dates)
    
#     return temporal_data

def extract_temporal_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume patrones temporales de todos los mensajes con contexto y usuarios.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    temporal_data = {
        "patterns_with_context": {},
        "absolute_dates": [],
        "relative_references": [],
        "time_expressions": [],
        "total_temporal_references": 0
    }
    
    # Diccionario para acumular patrones con contexto
    patterns_dict = {}
    
    for msg in messages:
        text = msg.get('text', '')
        user_id = msg.get('user_id', 'Unknown')
        message_id = msg.get('id', '')
        timestamp = msg.get('timestamp', '')
        
        if text:
            patterns = extract_regex_patterns(text)
            
            # Procesar cada categoría de patrones temporales
            temporal_categories = [key for key in patterns.keys() if key.startswith('dates_')]
            
            for category in temporal_categories:
                for pattern in patterns[category]:
                    if not pattern:
                        continue
                        
                    # Normalizar el patrón
                    if isinstance(pattern, tuple):
                        pattern_text = ' '.join(str(p) for p in pattern if p)
                    else:
                        pattern_text = str(pattern)
                    
                    # Limpiar y normalizar el patrón
                    pattern_text = pattern_text.strip().lower()
                    
                    # Extraer contexto alrededor del patrón
                    context = extract_temporal_context(text, pattern_text)
                    
                    # Crear clave única para el patrón
                    pattern_key = pattern_text
                    
                    if pattern_key not in patterns_dict:
                        patterns_dict[pattern_key] = {
                            'pattern': pattern_text,
                            'category': category,
                            'occurrences': [],
                            'total_count': 0,
                            'users': [],  # Cambiado de set() a lista
                            'example_contexts': []
                        }
                    
                    # Añadir ocurrencia
                    patterns_dict[pattern_key]['occurrences'].append({
                        'user_id': user_id,
                        'message_id': message_id,
                        'timestamp': timestamp,
                        'context': context,
                        'full_text': text[:200] + "..." if len(text) > 200 else text  # Texto completo truncado
                    })
                    
                    patterns_dict[pattern_key]['total_count'] += 1
                    
                    # Añadir usuario si no está en la lista (mantener única)
                    if user_id not in patterns_dict[pattern_key]['users']:
                        patterns_dict[pattern_key]['users'].append(user_id)
                    
                    # Mantener máximo 3 contextos de ejemplo
                    if len(patterns_dict[pattern_key]['example_contexts']) < 3:
                        patterns_dict[pattern_key]['example_contexts'].append(context)
    
    # Convertir a la estructura final
    temporal_data['patterns_with_context'] = patterns_dict
    
    # Mantener compatibilidad con la estructura anterior
    all_dates = []
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            for key in patterns:
                if key.startswith('dates_'):
                    all_dates.extend(patterns[key])
    
    temporal_data["absolute_dates"] = [d for d in all_dates if re.search(r'\d', str(d))]
    temporal_data["relative_references"] = [d for d in all_dates if any(kw in str(d).lower() for kw in 
        ['hoy', 'ayer', 'mañana', 'semana', 'mes', 'año', 'próximo', 'pasado'])]
    temporal_data["time_expressions"] = list(set(all_dates))
    temporal_data["total_temporal_references"] = len(all_dates)
    
    return temporal_data

def extract_temporal_context(text: str, pattern: str) -> str:
    """
    Extrae el contexto alrededor de un patrón temporal en el texto.
    Devuelve la frase o parte del texto que contiene el patrón.
    """
    # Buscar el patrón en el texto (case insensitive)
    pattern_lower = pattern.lower()
    text_lower = text.lower()
    
    start_idx = text_lower.find(pattern_lower)
    if start_idx == -1:
        return text[:100] + "..." if len(text) > 100 else text
    
    end_idx = start_idx + len(pattern)
    
    # Extender el contexto hacia atrás hasta el inicio de la frase
    context_start = start_idx
    for i in range(start_idx - 1, max(0, start_idx - 50), -1):
        if text[i] in '.!?;\n':
            context_start = i + 1
            break
        if i == max(0, start_idx - 50):
            context_start = i
            break
    
    # Extender el contexto hacia adelante hasta el fin de la frase
    context_end = end_idx
    for i in range(end_idx, min(len(text), end_idx + 50)):
        if text[i] in '.!?;\n':
            context_end = i
            break
        if i == min(len(text), end_idx + 50) - 1:
            context_end = i + 1
            break
    
    context = text[context_start:context_end].strip()
    
    # Limpiar el contexto
    context = re.sub(r'\s+', ' ', context)  # Reemplazar múltiples espacios
    context = context.strip()
    
    return context

def extract_social_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume patrones sociales de todos los mensajes.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    social_data = {
        "hashtags": [],
        "mentions": [],
        "urls": [],
        "emojis": [],
        "social_engagement_score": 0
    }
    
    all_hashtags = []
    all_mentions = []
    all_urls = []
    all_emojis = []
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            all_hashtags.extend(patterns.get('hashtags', []))
            all_mentions.extend(patterns.get('mentions', []))
            all_urls.extend(patterns.get('urls_raw', []))
            all_emojis.extend(patterns.get('emojis', []))
    
    social_data["hashtags"] = list(set(all_hashtags))
    social_data["mentions"] = list(set(all_mentions))
    social_data["urls"] = list(set(all_urls))
    social_data["emojis"] = list(set(all_emojis))
    social_data["social_engagement_score"] = len(all_hashtags) + len(all_mentions) + len(all_urls)
    
    return social_data

def extract_contact_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume informacion de contacto de todos los mensajes.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    contact_data = {
        "emails": [],
        "phone_numbers": [],
        "contact_entities": [],
        "total_contact_points": 0
    }
    
    all_emails = []
    all_phones = []
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            all_emails.extend(patterns.get('emails', []))
            # Filtrar telefonos validos
            valid_phones = [p for p in patterns.get('phone_numbers', []) if p and re.search(r'\d{5,}', str(p))]
            all_phones.extend(valid_phones)
    
    contact_data["emails"] = list(set(all_emails))
    contact_data["phone_numbers"] = list(set(all_phones))
    contact_data["contact_entities"] = contact_data["emails"] + contact_data["phone_numbers"]
    contact_data["total_contact_points"] = len(contact_data["emails"]) + len(contact_data["phone_numbers"])
    
    return contact_data

def extract_technical_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume patrones tecnicos de todos los mensajes.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    technical_data = {
        "coordinates": [],
        "ip_addresses": [],
        "measurements": [],
        "technical_entities": [],
        "total_technical_patterns": 0
    }
    
    all_coordinates = []
    all_ips = []
    all_measurements = []
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            all_coordinates.extend(patterns.get('coordinates', []))
            all_ips.extend(patterns.get('ip_addresses', []))
            all_measurements.extend(patterns.get('measurements', []))
    
    technical_data["coordinates"] = list(set(all_coordinates))
    technical_data["ip_addresses"] = list(set(all_ips))
    technical_data["measurements"] = list(set(all_measurements))
    technical_data["technical_entities"] = technical_data["coordinates"] + technical_data["ip_addresses"] + technical_data["measurements"]
    technical_data["total_technical_patterns"] = len(technical_data["technical_entities"])
    
    return technical_data

def calculate_conversation_metrics(messages: List[Dict]) -> Dict:
    """
    Calcula metricas generales de la conversacion basadas en los patrones encontrados.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    metrics = {
        "total_messages_with_patterns": 0,
        "patterns_per_message_avg": 0,
        "most_active_categories": [],
        "temporal_distribution": {}
    }
    
    total_patterns = 0
    category_counts = {
        "financial": 0,
        "temporal": 0, 
        "social": 0,
        "contact": 0,
        "technical": 0
    }
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            msg_patterns = sum(len(patterns[key]) for key in patterns)
            
            if msg_patterns > 0:
                metrics["total_messages_with_patterns"] += 1
                total_patterns += msg_patterns
                
                # Contar por categoria
                category_counts["financial"] += len(patterns.get('monedas_explicitas', [])) + len(patterns.get('precios_implicitos', []))
                category_counts["temporal"] += sum(len(patterns.get(key, [])) for key in patterns if key.startswith('dates_'))
                category_counts["social"] += len(patterns.get('hashtags', [])) + len(patterns.get('mentions', [])) + len(patterns.get('urls_raw', [])) + len(patterns.get('emojis', []))
                category_counts["contact"] += len(patterns.get('emails', [])) + len(patterns.get('phone_numbers', []))
                category_counts["technical"] += len(patterns.get('coordinates', [])) + len(patterns.get('ip_addresses', [])) + len(patterns.get('measurements', []))
    
    # Calcular promedios
    if len(messages) > 0:
        metrics["patterns_per_message_avg"] = total_patterns / len(messages)
    
    # Categorias mas activas
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    metrics["most_active_categories"] = [{"category": cat, "count": count} for cat, count in sorted_categories]
    
    return metrics
