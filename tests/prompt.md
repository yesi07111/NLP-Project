Estoy haciendo un proyecto universitario de procesamiento del lenguaje natural, este proyecto debe contener varios temas dados en clase como expresiones regulares, lenguajes libres de contexto, arboles de conocimiento, etc. Mi tema es Telegram, asi que tengo una forma de obtener chats de telegram de grupos en formato json. De estos extraigo los link con expresiones regulares y los cambio por frases informativas asociadas al link, ademas extraigo mucha mas info con expresiones regulares y la guardo en un json.

Luego este resumen tendra su uso para un grafo de conocimiento dirigido que vamos a hacer a partir de las conversaciones de las personas, se debe hacer 1 grafo por cada chat o sea cada json. La idea es que cada nodo es un usuario o un mensaje. Los usuarios apuntan hacia los mensajes con un peso 1, los mensajes que son respuesta de otro tienen una conexión con peso 1 (desde el padre hacia el hijo). Luego los mensajes que no sean una respuesta directa de otros tienen un peso P(m1, m2) donde P es la probabilidad de que m2 sea una respuesta a m1.

Esto habría que podarlo y usar heuristicas para reducir la densidad del grafo final, por ejemplo, tomar el tiempo del mensaje en cuenta: si m1 ocurrió n minutos antes que m2, con n mayor que algún threshold entonces se asume no es respuesta. Querria usar logica difuso para esa probabilidad.

Con esto queda un grafo dirigido y sin ciclos que suelen ser muy bonitos para algoritmos de grafos. Encima tiene pesos en las aristas que sirve para Dijsktra y A*

Dime como lo harias, pero no hagas nada por ahora, solo dame las ideas de como podemos hacer esto y que uso podriamos darle a esta info sacada con expresiones regulares, que mas podemos sacar usando nltk o spacy. El objetivo final es poder reconstruir hilos de conversaciones con quien responde a que y ademas poder categorizar sus temas de conversacion y hacer otras cosas de procesamiento de lenguaje, dame ideas de que mas y de como hacer lo que ya te dije.

Ahora mismo no quiero codigo, quiero las ideas textuales de que podriamos hacer, dame varias ideas y no me des codigo. Este es el contexto del proyecto:

Readme para contexto general del proyecto:
# 🤖 Proyecto NLP — Cliente Telegram para exportar chats

## 🧠 Resumen
Este proyecto es una herramienta de **Procesamiento del Lenguaje Natural (NLP)** que funciona como cliente de Telegram. Permite iniciar sesión con una cuenta, seleccionar chats/grupos y descargar los mensajes en un formato **estructurado (JSON)** para análisis posterior. Es posible filtrar por rango de fechas y elegir si descargar contenidos multimedia (imágenes, audios, documentos).

---

## 🎯 Funcionalidades principales
- 🔐 Iniciar sesión y gestionar la sesión (incluye soporte para 2FA / contraseña de verificación).  
- 📥 Descargar mensajes por chat o grupos seleccionados.  
- 📅 Filtrar por rango de fezas.  
- ✅ Seleccionar tipos de medios a descargar: imágenes, audio, documentos.  
- 🗂️ Guardar los mensajes y metadatos en un archivo `JSON` por chat, y los archivos multimedia en carpetas `media_<nombre_del_chat>`.

---

## 📦 Formato del JSON generado
El JSON contiene dos secciones principales: `metadata` y `messages`.

- `metadata`:
  - `chat_name`: nombre del chat o canal.
  - `start_date`, `end_date`: rango de fechas solicitado.
  - `total_messages`: número total de mensajes incluidos.
  - `generated_at`: marca de tiempo de generación del JSON.

- `messages`: lista de mensajes, cada uno con campos como:
  - `id`: identificador del mensaje.
  - `sender_id`, `sender_name`, `sender_username`
  - `text`: texto limpio del mensaje (ver **Preprocesamiento**).
  - `reactions`: objeto con conteo por emoji (ej. `{ "👍": 3 }`).
  - `mentions`: lista de menciones (si aplica).
  - `reply_id`: id del mensaje al que responde (si existe).
  - `date`: marca de tiempo en formato ISO.
  - `media`: **información sobre el multimedia** (ver abajo).

### 🔎 Estructura del campo `media`
Al decidir descargar los medios, cada mensaje puede contener un objeto `media` con esta forma (si no hay medios, puede ser `null`):

```json
"media": {
  "type": "photo" | "audio" | "document" | null,
  "filename": "photo_12345.jpg" | "audio_67890.ogg" | "54321_document.pdf" | null,
  "path": "media_Grupo Estudio\\photo_12345.jpg",
  "downloaded": true | false
}
```

* Los archivos descargados se guardan en una carpeta por chat: `media_<nombre_del_chat_sanitizado>` (ej.: `media_Grupo Estudio`).
* `path` es la ruta relativa al archivo dentro del proyecto (utiliza separadores de sistema según la plataforma).
* Si `downloaded: false` o `media` es `null`, no hay archivo local disponible para ese mensaje.

#### Ejemplo breve (fragmento del JSON):

```json
{
  "id": 67890,
  "sender_id": 987654321,
  "sender_name": "Ana García",
  "sender_username": "anagarcia_dev",
  "text": "¿Quedamos para estudiar mañana?",
  "reactions": {"❤️": 2},
  "mentions": [],
  "reply_id": null,
  "date": "2024-03-15T10:30:00+00:00",
  "media": {
    "type": "photo",
    "filename": "photo_67890.jpg",
    "path": "media_Grupo Estudio\\photo_67890.jpg",
    "downloaded": true
  }
}
```

```json
{
  "id": 67900,
  "sender_id": 123456789,
  "sender_name": "Carlos López",
  "sender_username": "carlos_tech",
  "text": "Aquí está el documento que mencioné",
  "reactions": {},
  "mentions": [],
  "reply_id": 67890,
  "date": "2024-03-15T10:35:00+00:00",
  "media": {
    "type": "document",
    "filename": "67900_apuntes.pdf",
    "path": "media_Grupo Estudio\\67900_apuntes.pdf",
    "downloaded": true
  }
}
```

---

## 🧹 Preprocesamiento del texto (cómo limpiar los mensajes)

Actualmente existe un preprocesamiento centrado en:

1. **Sustitución de enlaces**

   * Utilizar expresiones regulares para localizar URLs y sustituirlas por descripciones contextualizadas (ej. `[Video de YouTube]`, `[Reel de Instagram]`, `[Invitación a grupo de Telegram]`, `[Enlace externo]`, etc.).
   * Esto evita que URLs largas ensucien el texto y facilita el análisis semántico.

2. **Markdown → Texto plano**

   * Los mensajes con formato Markdown (negritas, cursivas, listas) se transforman a HTML con `markdown.markdown(...)`.
   * Luego `BeautifulSoup` analiza ese HTML y extrae el texto plano con `soup.get_text(...)`.
   * Esto preserva el contenido semántico (texto) y elimina etiquetas de formato.

3. **Preservación de emojis y reacciones**

   * Los emojis permanecen en el campo `text`. Las reacciones se guardan en `reactions` como un objeto con recuentos por emoji.

4. **Saneamiento de nombres de archivo**

   * Para almacenar medios en disco se construyen nombres seguros (se reemplazan caracteres inválidos para el sistema de archivos).

> Ejemplo de flujo (función `clean_message_text`):
>
> * Detectar y reemplazar URLs → `replace_link(...)`.
> * Convertir Markdown a HTML → `markdown.markdown(...)`.
> * Extraer texto limpio → `BeautifulSoup(...).get_text(...)`.
> * Devolver texto ya normalizado y sin URLs crudas.

---

## 🌳 Árbol de conocimiento / reconstrucción de hilos (planificado)

Próximamente se integrará una capa que permita **reconstruir hilos de conversación** incluso cuando Telegram no indique explícitamente a qué mensaje responde un texto. La idea:

* Analizar **secuencia temporal**, menciones, palabras clave y proximidad semántica.
* Construir un **grafo/árbol** donde los nodos sean mensajes y las aristas representen relaciones de respuesta o continuidad temática.
* Utilizarlo para: reconstruir hilos, agrupar subconversaciones, extraer temas y facilitar resúmenes automáticos.

Esto permitirá **restaurar contextos** en chats donde las referencias implícitas están fragmentadas.

---

## ⚙️ Ejecución (guía rápida)

1. Instalar las dependencias desde el `requirements.txt`:

```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación principal:

```bash
python main.py
```

> El `requirements.txt` debe listar `telethon`, `markdown`, `beautifulsoup4` y demás librerías que el proyecto requiere.

---

## 🗂️ Organización de archivos (resumen)

* `main.py` → punto de entrada.
* `telegram/` → lógica del cliente y worker (Telethon).
* `ui/` → interfaz PyQt (ventanas, widgets, diálogos).
* `utils/` → utilidades: `sanitize_filename`, análisis, caché, etc.
* `media_<chat_name>/` → carpetas donde se guardan imágenes, audio y documentos descargados.
* `output/<chat_name>_<start>_<end>.json` → JSON resultante por chat.

---

## 📝 Notas finales

* El JSON y la organización de medios están diseñados para **hacer reproducible y sencillo el pipeline de análisis**.
* El preprocesamiento actual es deliberadamente conservador: prioriza mantener el contenido legible y sustituir elementos ruidosos (URLs largos) por descriptores útiles para NLP.

---


Algunos archivos .py que dan contexto especifico de lo que tengo:
utils/text_processing.py:
import re
import os
import markdown
from bs4 import BeautifulSoup
from link_processor.main import LinkProcessor

os.makedirs('chats', exist_ok=True)

def clean_message_text(text: str) -> str:
    """Limpia el texto de un mensaje reemplazando enlaces por descripciones detalladas"""

    def strip_markdown(text: str) -> str:
        html = markdown.markdown(text, extensions=["extra", "sane_lists"])
        soup = BeautifulSoup(html, "html.parser")
        cleaned = soup.get_text(separator=" ", strip=True)
        return cleaned

    link_processor = LinkProcessor()
    url_pattern = re.compile(r'https?://[^\s]+')
    cleaned = re.sub(url_pattern, link_processor.replace_link, text)
    raw = strip_markdown(cleaned)

    return raw.strip()

link_processor/main.py:
import re
from typing import Match
from urllib.parse import urlparse
from .file_detector import FileTypeDetector
from .extractors import get_extractor

class LinkProcessor:
    def __init__(self):
        self.file_detector = FileTypeDetector()
    
    def replace_link(self, match: Match) -> str:
        """Para uso con re.sub() - espera un objeto Match"""
        url = match.group(0)
        return self.process_url(url)
    
    def process_url(self, url: str) -> str:
        """Procesa una URL directamente - para uso en tests y otros contextos"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 1. Verificar si es archivo - PASAR LA URL COMPLETA, no solo el path
        file_info = self.file_detector.get_file_type(url)
        if file_info['type'] != 'unknown':
            return self.file_detector.format_file_output(file_info)
        
        # 2. Buscar extractor específico
        extractor = get_extractor(domain)
        if extractor:
            result = extractor.extract(parsed, domain)
            if result:
                return extractor.format_output(result)
        
        # 3. Enlace genérico
        return self._format_generic_link(domain)
    
    def _format_generic_link(self, domain: str) -> str:
        """Formatea enlaces genéricos"""
        # Remover www. solo para display, no para lógica de extractores
        display_domain = re.sub(r"^www\.", "", domain)
        domain_parts = display_domain.split('.')
        
        if len(domain_parts) >= 2:
            site_name = domain_parts[-2].capitalize()
            return f"[🔗 Enlace a {site_name}]"
        return "[🌐 Enlace externo]"

regex/pattern_analyzer.py:
import json
import os
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
    chat_path = os.path.join('chats', chat_filename)
    try:
        with open(chat_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        try: 
            with open(chat_filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            print(f"Archivo {chat_filename} no encontrado")
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
    from regex_extractor import extract_regex_patterns, analyze_text_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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
    from regex_extractor import extract_regex_patterns
    
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

# Funciones de compatibilidad para mantener el codigo existente
def extract_advanced_patterns(text: str) -> dict:
    """Funcion de compatibilidad - usa extract_regex_patterns"""
    from regex_extractor import extract_regex_patterns
    return extract_regex_patterns(text)

def analyze_message_patterns(text: str) -> str:
    """Funcion de compatibilidad - usa analyze_text_patterns"""
    from regex_extractor import analyze_text_patterns
    return analyze_text_patterns(text)

regex/regex_extractor.py:
import re
from typing import Dict, List, Tuple

def extract_regex_patterns(text: str) -> dict:
    """
    Extrae patrones del texto utilizando expresiones regulares.
    Esta funcion se enfoca en detectar patrones especificos mediante regex.
    
    Args:
        text: Texto de entrada para analizar
        
    Returns:
        Diccionario con todos los patrones encontrados organizados por categoria
    """
    
    patterns = {
        'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text, re.IGNORECASE),
        'phone_numbers': re.findall(r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}', text),
        'hashtags': re.findall(r'#\w+', text),
        'mentions': re.findall(r'@\w+', text),
        'urls_raw': re.findall(r'https?://[^\s]+', text),
        'emojis': re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text),
        'coordinates': re.findall(r'\b-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+\b', text),
        'ip_addresses': re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text),
        'crypto_addresses': re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\b0x[a-fA-F0-9]{40}\b', text),
        'credit_cards': re.findall(r'\b(?:\d{4}[- ]?){3}\d{4}\b', text),
        'isbn_codes': re.findall(r'\b(?:ISBN(?:-1[03])?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9X]\b', text),
        'vehicle_plates': re.findall(r'\b[A-Z]{1,3}\s?-?\s?\d{1,4}\s?[A-Z]{0,2}\b', text),
        'measurements': re.findall(r'\b\d+(?:\.\d+)?\s*(?:kg|g|mg|lb|oz|m|cm|mm|km|ft|in|L|ml|gal|m²|m2|cm²|cm2)\b', text, re.IGNORECASE),
        'percentages': re.findall(r'\b\d+(?:\.\d+)?%\b', text),
        'mathematical_operations': re.findall(r'\b\d+\s*[\+\-\*\/]\s*\d+\s*=\s*\d+\b', text),
        'all_caps_words': re.findall(r'\b[A-Z]{3,}\b', text),
        'repeated_letters': re.findall(r'\b\w*(\w)\1{2,}\w*\b', text),
        'quoted_text': re.findall(r'[""]([^""]+)[""]', text),
        'parenthetical_text': re.findall(r'\(([^)]+)\)', text),
    }
    
    # Extraer patrones monetarios
    monetary_patterns = _extract_monetary_patterns(text)
    patterns.update(monetary_patterns)
    
    # Extraer patrones de fechas
    date_patterns = _extract_date_patterns(text)
    patterns.update(date_patterns)
    
    return patterns

def _extract_monetary_patterns(text: str) -> dict:
    """
    Extrae patrones relacionados con dinero y precios usando expresiones regulares.
    Incluye monedas explicitas, precios implicitos y rangos.
    """
    monetary_data = {
        'monedas_explicitas': [],
        'precios_implicitos': [],
        'currency_ranges': [],
        'currency_ranges_extended': [],
        'currency_with_symbols': [],
        'currency_in_format': [],
        'currency_without_en': [],
        'currency_decimal': [],
        'price_changes': [],
        'labeled_prices': [],
        'preposition_prices': [],
        'discounts_percent': [],
        'discounts_absolute': []
    }
    
    # Definicion de patrones para monedas
    currency_patterns = [
        # Formato: 150-200 mlc, 140 - 340 mn (rangos)
        r'(\d+(?:\s*-\s*\d+)+)\s*(mlc|mn|usd|dólares|dolares|pesos|eur|euros|cup|clp|mxn|moneda nacional|dinero cubano)\b',
        
        # Formato: de 300 a 400 usd, entre 500 y 600 mlc
        r'(?:de|entre)\s+(\d+)\s*(?:a|y|y\s+entre)\s+(\d+)\s*(mlc|mn|usd|dólares|dolares|pesos|eur|euros|moneda nacional|dinero cubano)',
        
        # Formato simple: 20 mn, 30 mlc, 40 usd
        r'(\d+)\s*(mlc|mn|usd|dólares|dolares|pesos|eur|euros|cup|clp|mxn|moneda nacional|dinero cubano)\b',
        
        # Formato con simbolos: $20, 20€, 20 USD
        r'(?:\$|€|¥|£)?\s*(\d+(?:\.\d+)?)\s*(?:usd|dólares|dolares|pesos|eur|euros|mlc|mn|moneda nacional|dinero cubano)',
        
        # Formato con "en": 20 en clasica, 20 en mlc
        r'(\d+)\s*en\s*(clásica|clasica|mlc|mn|usd|dólares|moneda nacional|dinero cubano)',
        
        # Formato sin "en": 20 clasica, 20 mlc
        r'(\d+)\s*(clásica|clasica|mlc|mn|usd|dólares|moneda nacional|dinero cubano)',
        
        # Formato con decimales: 150.50 mlc, 200,00 mn
        r'(\d+(?:[.,]\d+)?)\s*(mlc|mn|usd|dólares|dolares|pesos|moneda nacional|dinero cubano)',
    ]
    
    # Patrones para precios implicitos
    implicit_patterns = [
        # "sale en 700", "son 700", "cuesta 700"
        r'(?:sale\s+en|son|cuesta|vale|esta\s+en|está\s+en)\s+(\d+(?:[.,]\d+)?)',
        
        # "subio a 400", "bajo a 300"
        r'(subió|subio|bajó|bajo)\s+(?:a\s+)?(\d+(?:[.,]\d+)?)',
        
        # "precio: 500", "valor: 300"
        r'(?:precio|valor|costo|costó)\s*:?\s*(\d+(?:[.,]\d+)?)',
        
        # "por 800", "a 600", "desde 400"
        r'(?:por|a|desde|hasta)\s+(\d+(?:[.,]\d+)?)',
        
        # Descuentos porcentuales
        r'(\d+)%\s*(?:off|de\s+descuento|descuento)',
        r'rebajado\s+(?:a\s+)?(\d+(?:[.,]\d+)?)'
    ]
    
    # Procesar patrones de monedas
    for i, pattern in enumerate(currency_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE)
        if i == 0:
            monetary_data['currency_ranges'] = matches
        elif i == 1:
            monetary_data['currency_ranges_extended'] = matches
        elif i == 2:
            monetary_data['monedas_explicitas'] = matches
        elif i == 3:
            monetary_data['currency_with_symbols'] = matches
        elif i == 4:
            monetary_data['currency_in_format'] = matches
        elif i == 5:
            monetary_data['currency_without_en'] = matches
        elif i == 6:
            monetary_data['currency_decimal'] = matches
    
    # Procesar patrones implicitos
    for i, pattern in enumerate(implicit_patterns):
        matches = re.findall(pattern, text, re.IGNORECASE)
        if i == 0:
            monetary_data['precios_implicitos'] = matches
        elif i == 1:
            monetary_data['price_changes'] = matches
        elif i == 2:
            monetary_data['labeled_prices'] = matches
        elif i == 3:
            monetary_data['preposition_prices'] = matches
        elif i == 4:
            monetary_data['discounts_percent'] = matches
        elif i == 5:
            monetary_data['discounts_absolute'] = matches
    
    return monetary_data

def _extract_date_patterns(text: str) -> dict:
    """
    Extrae patrones relacionados con fechas y tiempos usando expresiones regulares.
    Incluye fechas absolutas, relativas y referencias temporales.
    """
    date_data = {
        'dates_absolute': [],
        'dates_spanish_format': [],
        'dates_month_first': [],
        'dates_relative_simple': [],
        'dates_relative_quantified': [],
        'dates_weeks': [],
        'dates_weekends': [],
        'dates_months': [],
        'dates_years': [],
        'dates_months_specific': [],
        'dates_weekdays': [],
        'dates_seasons': [],
        'dates_holidays': [],
        'dates_additional': []
    }
    
    # Definicion de patrones para fechas
    date_patterns = [
        # Fechas absolutas
        (r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', 'dates_absolute'),
        
        # Formato español: 15 de enero de 2024
        (r'\b\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de?\s+\d{2,4}\b', 'dates_spanish_format'),
        
        # Mes primero: enero 15, 2024
        (r'\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{1,2},?\s+\d{4}\b', 'dates_month_first'),
        
        # Referencias relativas simples
        (r'\b(hoy|ayer|antier|anteayer|mañana|pasado|pasado\s+mañana)\b', 'dates_relative_simple'),
        
        # Referencias con cantidad: en 5 dias, hace 3 semanas - ARREGLADO: incluye singular y plural
        (r'\b(en|hace)\s+(\d+)\s+(dias|días|dia|día|semanas|semana|meses|mes|años|año)\b', 'dates_relative_quantified'),
        
        # Referencias de semanas
        (r'\b(semana\s+que\s+viene|semana\s+pasada|esta\s+semana|semana\s+anterior|semana\s+pr[oó]xima|pr[oó]xima\s+semana)\b', 'dates_weeks'),
        
        # Referencias de fines de semana
        (r'\b(este\s+fin\s+de\s+semana|este\s+finde|finde\s+que\s+viene|fin\s+de\s+semana\s+que\s+viene|pr[oó]ximo\s+finde)\b', 'dates_weekends'),
        
        # Referencias de meses
        (r'\b(este\s+mes|mes\s+que\s+viene|mes\s+pr[oó]ximo|mes\s+pasado|pr[oó]ximo\s+mes|el\s+mes\s+que\s+viene)\b', 'dates_months'),
        
        # Referencias de años
        (r'\b(este\s+año|año\s+que\s+viene|pr[oó]ximo\s+año|año\s+pasado|el\s+año\s+pasado|el\s+año\s+que\s+viene)\b', 'dates_years'),
        
        # Meses especificos
        (r'\b(en\s+)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\b', 'dates_months_specific'),
        
        # Dias de la semana
        (r'\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b', 'dates_weekdays'),
        
        # Estaciones del año
        (r'\b(primavera|verano|otoño|invierno)\b', 'dates_seasons'),
        
        # Festivos
        (r'\b(navidad|año nuevo|reyes|semana santa|pascua|carnaval)\b', 'dates_holidays'),
        
        # Patrones temporales adicionales
        (r'\b(la\s+semana\s+entrante|la\s+semana\s+siguiente|la\s+que\s+viene|dentro\s+de\s+un\s+rato|más\s+tarde|esta\s+tarde|esta\s+noche)\b', 'dates_additional'),
        (r'\b(al\s+día\s+siguiente|al\s+siguiente\s+día|al\s+otro\s+día|al\s+dia\s+siguiente)\b', 'dates_additional'),
        (r'\b(ultimamente|últimamente|recientemente|hace\s+poco|hace\s+un\s+tiempo)\b', 'dates_additional')
    ]
    
    # Procesar todos los patrones de fecha
    for pattern, category in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if category in date_data:
                date_data[category].extend(matches)
    
    return date_data
def analyze_text_patterns(text: str) -> str:
    """
    Analiza el texto y lo enriquece con informacion sobre los patrones encontrados.
    Esta funcion es util para visualizar rapidamente que se ha detectado.
    """
    patterns = extract_regex_patterns(text)
    
    elementos_detectados = []
    
    # Resumen de patrones monetarios
    total_monetary = (
        len(patterns.get('monedas_explicitas', [])) +
        len(patterns.get('precios_implicitos', [])) +
        len(patterns.get('currency_ranges', []))
    )
    if total_monetary > 0:
        elementos_detectados.append(f"{total_monetary} referencias monetarias")
    
    # Resumen de patrones de fecha
    total_dates = sum(len(patterns.get(key, [])) for key in patterns if key.startswith('dates_'))
    if total_dates > 0:
        elementos_detectados.append(f"{total_dates} referencias de fecha")
    
    # Otros patrones importantes
    if patterns.get('emails'):
        elementos_detectados.append(f"{len(patterns['emails'])} emails")
    
    if patterns.get('phone_numbers'):
        valid_phones = [p for p in patterns['phone_numbers'] if p and re.search(r'\d', p)]
        if valid_phones:
            elementos_detectados.append(f"{len(valid_phones)} telefonos")
    
    if patterns.get('urls_raw'):
        elementos_detectados.append(f"{len(patterns['urls_raw'])} enlaces")
    
    if patterns.get('hashtags'):
        elementos_detectados.append(f"{len(patterns['hashtags'])} hashtags")
    
    if patterns.get('mentions'):
        elementos_detectados.append(f"{len(patterns['mentions'])} menciones")
    
    if elementos_detectados:
        return f"{text} [Patrones: {', '.join(elementos_detectados)}]"
    
    return text