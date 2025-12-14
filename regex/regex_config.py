"""
Configuración centralizada de expresiones regulares para el sistema de alarmas
"""
import re

# Importar extractores desde regex_extractor.py
from regex.regex_extractor import extract_regex_patterns, _extract_monetary_patterns, _extract_date_patterns

def get_all_predefined_patterns():
    """
    Devuelve todos los patrones predefinidos del sistema
    """
    patterns = {
        # Patrones básicos de regex_extractor
        "📧 Correos Electrónicos": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "📞 Números de Teléfono": r'\b(?:\+\d{1,3}[\s\-]?)?(?:\(\d+\)[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}[\s\-]?\d{0,4}\b',
        "#️⃣ Hashtags": r'#\w+',
        "@️⃣ Menciones": r'@\w+',
        "💳 Tarjetas de Crédito": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
        "📍 Coordenadas": r'\b-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+\b',
        "🌐 Direcciones IP": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "₿ Direcciones Cripto": r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\b0x[a-fA-F0-9]{40}\b',
        "📚 Códigos ISBN": r'\b(?:ISBN(?:-1[03])?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9X]\b',
        "🚗 Placas de Vehículos": r'\b[A-Z]{1,3}\s?-?\s?\d{1,4}\s?[A-Z]{0,2}\b',
        "📏 Medidas": r'\b\d+(?:\.\d+)?\s*(?:kg|g|mg|lb|oz|m|cm|mm|km|ft|in|L|ml|gal|m²|m2|cm²|cm2)\b',
        "📊 Porcentajes": r'\b\d+(?:\.\d+)?%\b',
        
        # Patrones de fechas mejorados
        "🗓️ Fechas absolutas": r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        "🗓️ Fechas español": r'\b\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de?\s+\d{2,4}\b',
        
        # Patrones monetarios personalizados
        "💰 Precios explícitos": r'\b\d+(?:[.,]\d+)?\s*(?:mlc|mn|usd|clásica|clasica|dólares|dolares|pesos|eur|euros|cup|clp|mxn|moneda nacional|dinero cubano)\b',
        "💰 Precios con $": r'\$\s?\d+(?:[.,]\d+)?\s*(?:mlc|mn|usd)?\b',
        "💰 Rangos de precios": r'\b\d+\s*-\s*\d+\s*(?:mlc|mn|usd|dólares|dolares|pesos)',
    }
    
    # Agregar patrones de redes sociales desde link_processor
    social_patterns = get_social_media_patterns()
    patterns.update(social_patterns)
    
    return patterns

def get_social_media_patterns():
    """
    Patrones de redes sociales basados en los extractores disponibles
    """
    return {
        "🛒 Enlaces de Amazon": r'https?://(?:www\.)?amazon\.[a-z.]{2,6}/[^\s]+',
        "💬 Enlaces de Discord": r'https?://(?:www\.)?discord(?:app)?\.com/[^\s]+',
        "👥 Enlaces de Facebook": r'https?://(?:www\.)?facebook\.com/[^\s]+',
        "📸 Enlaces de Flickr": r'https?://(?:www\.)?flickr\.com/[^\s]+',
        "🎬 Enlaces de Likee": r'https?://(?:www\.)?likee\.video/[^\s]+',
        "💼 Enlaces de LinkedIn": r'https?://(?:www\.)?linkedin\.com/[^\s]+',
        "📝 Enlaces de Medium": r'https?://(?:www\.)?medium\.com/[^\s]+',
        "📌 Enlaces de Pinterest": r'https?://(?:www\.)?pinterest\.com/[^\s]+',
        "👾 Enlaces de Reddit": r'https?://(?:www\.)?reddit\.com/[^\s]+',
        "👻 Enlaces de Snapchat": r'https?://(?:www\.)?snapchat\.com/[^\s]+',
        "💻 Enlaces de StackOverflow": r'https?://(?:www\.)?stackoverflow\.com/[^\s]+',
        "🧵 Enlaces de Threads": r'https?://(?:www\.)?threads\.net/[^\s]+',
        "📝 Enlaces de Tumblr": r'https?://(?:www\.)?tumblr\.com/[^\s]+',
        "🐦 Enlaces de Twitter/X": r'https?://(?:www\.)?(?:twitter|x)\.com/[^\s]+',
        "💬 Enlaces de WhatsApp": r'https?://(?:wa\.me/|whatsapp\.com/)[^\s]+',
        "🎬 Enlaces de YouTube": r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s]+',
        "💻 Enlaces de GitHub": r'https?://(?:www\.)?github\.com/[^\s]+',
        "💻 Enlaces de GitLab": r'https?://(?:www\.)?gitlab\.com/[^\s]+',
        "🔍 Enlaces de Google": r'https?://(?:www\.)?google\.com/[^\s]+',
        "🖼️ Enlaces de Imgur": r'https?://(?:www\.)?imgur\.com/[^\s]+',
        "📷 Enlaces de Instagram": r'https?://(?:www\.)?instagram\.com/[^\s]+',
    }

def extract_with_custom_patterns(text, custom_patterns):
    """
    Extrae patrones del texto usando patrones personalizados
    """
    results = {}
    
    for i, pattern in enumerate(custom_patterns):
        try:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results[f"custom_pattern_{i}"] = matches
        except re.error as e:
            print(f"Error en patrón {pattern}: {e}")
    
    return results

def get_ai_prompt_for_regex(description):
    """
    Genera el prompt para que la IA cree una expresión regular
    """
    return f"""Eres un experto en expresiones regulares. Dada la siguiente descripción, crea UNA expresión regular en Python que extraiga lo solicitado. La solicitud es una descripción de que se desea que capture la expresión regular.

Ejemplo de expresión regular en python que detecta la cadena literal 'amor': r'amor' 
Ejemplo de expresión regular en python compleja para validar emails:  r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

Descripción del usuario: {description}

REGLAS:
1. Devuelve SOLO la expresión regular, sin explicaciones, sin código adicional
2. La expresión regular debe estar en formato Python válido
3. Usa grupos de captura solo si son necesarios
4. Considera que el texto puede estar en español o inglés
5. Incluye manejo de mayúsculas/minúsculas cuando sea apropiado
6. A menos que el usuario especifique que quiere algo literal, no lo tomes así
7. SIEMPRE debe empezar con r' y terminar en '

 

Expresión regular:"""

def get_alarm_message_prompt(extracted_data, chat_title):
    """
    Genera el prompt para que la IA cree un mensaje de alarma bonito
    """
    data_summary = format_extracted_data_for_prompt(extracted_data)
    
    return f"""Eres un asistente que crea mensajes de alarma informativos y atractivos.

INFORMACIÓN EXTRAÍDA:
{data_summary}

CHAT: {chat_title}

INSTRUCCIONES:
1. Crea un mensaje de alarma breve y útil
2. Usa emojis relevantes para cada tipo de información
3. Organiza la información claramente
4. Incluye el nombre del chat
5. No uses markdown, solo texto plano
6. Máximo 300 caracteres
7. Sé específico con los datos encontrados
8. No añadas preámbulos como "Aquí está tu alarma" - empieza directamente con la información

FORMATO ESPERADO:
📊 RESUMEN DEL CHAT: [Nombre del chat]
• [Tipo de dato 1]: [cantidad] encontrados
• [Tipo de dato 2]: [ejemplos destacados]
⏰ Próxima revisión: [fecha estimada]

Mensaje de alarma:"""

def format_extracted_data_for_prompt(extracted_data):
    """
    Formatea los datos extraídos para el prompt de IA
    """
    if not extracted_data:
        return "No se encontró información nueva en el análisis."
    
    summary = []
    for key, values in extracted_data.items():
        if values:
            if isinstance(values, list):
                count = len(values)
                examples = ', '.join(str(v) for v in values[:3])
                if count > 3:
                    examples += f" y {count - 3} más"
                summary.append(f"{key}: {count} encontrados (ej: {examples})")
            else:
                summary.append(f"{key}: {values}")
    
    return "\n".join(summary)