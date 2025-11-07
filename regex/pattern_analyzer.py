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
    
    base_name = os.path.splitext(chat_filename)[0]
    patterns_filename = f"{base_name}_patterns.json"
    patterns_path = os.path.join('patterns', patterns_filename)
    
    # Asegurar que existe la carpeta patterns
    os.makedirs('patterns', exist_ok=True)
    
    with open(patterns_path, 'w', encoding='utf-8') as f:
        json.dump(patterns_data, f, ensure_ascii=False, indent=2)
    
    print(f"Resumen de patrones guardado: {patterns_path}")
    return patterns_data

def create_patterns_summary(messages: List[Dict]) -> Dict[str, Any]:
    """
    Crea un resumen completo de todos los patrones encontrados en los mensajes.
    
    Args:
        messages: Lista de mensajes a analizar
        
    Returns:
        Diccionario con el resumen completo de patrones
    """
    from regex.regex_extractor import extract_regex_patterns, analyze_text_patterns
    
    summary = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_messages": len(messages),
            "chats_analyzed": list(set(msg.get('chat_name', 'unknown') for msg in messages)),
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
            summary["message_analysis"].append({
                "message_id": msg.get('id'),
                "chat_name": msg.get('chat_name'),
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

def extract_temporal_patterns(messages: List[Dict]) -> Dict:
    """
    Extrae y resume patrones temporales de todos los mensajes.
    """
    from regex.regex_extractor import extract_regex_patterns
    
    temporal_data = {
        "absolute_dates": [],
        "relative_references": [],
        "time_expressions": [],
        "total_temporal_references": 0
    }
    
    all_dates = []
    
    for msg in messages:
        text = msg.get('text', '')
        if text:
            patterns = extract_regex_patterns(text)
            # Recoger todas las fechas de diferentes categorias
            for key in patterns:
                if key.startswith('dates_'):
                    all_dates.extend(patterns[key])
    
    temporal_data["absolute_dates"] = [d for d in all_dates if re.search(r'\d', str(d))]
    temporal_data["relative_references"] = [d for d in all_dates if any(kw in str(d).lower() for kw in 
        ['hoy', 'ayer', 'mañana', 'semana', 'mes', 'año', 'próximo', 'pasado'])]
    temporal_data["time_expressions"] = list(set(all_dates))
    temporal_data["total_temporal_references"] = len(all_dates)
    
    return temporal_data

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
