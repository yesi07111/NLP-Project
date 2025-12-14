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
    Devuelve 'monedas_explicitas' como lista de tuplas (cantidad, moneda) en orden de aparición,
    además de otros buckets (ranges, decimals, implícitos) para compatibilidad.
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

    # tokens alternativos (sin grupos internos)
    tokens_alt = r'mlc|mn|usd|clásica|clasica|dólares|dolares|pesos|eur|euros|cup|clp|mxn|moneda nacional|dinero cubano'

    # Patrones: ordenados para evitar solapamientos (rango -> rango extendido -> "en" -> sin "en")
    combined_re = re.compile(
        rf'(?P<range>\b\d+(?:\s*-\s*\d+)+)\s*(?P<cur1>{tokens_alt})\b'
        rf'|(?P<range_ext>\b(?:de|entre)\s+(?P<re_a>\d+)\s*(?:a|y)\s+(?P<re_b>\d+)\s*(?P<cur2>{tokens_alt})\b)'
        rf'|(?P<num_en>\b\d+(?:[.,]?\d+)?)\s+en\s+(?P<cur3>{tokens_alt})\b'
        rf'|(?P<num_plain>\b\d+(?:[.,]?\d+)?)\s+(?P<cur4>{tokens_alt})\b',
        re.IGNORECASE
    )

    found_entries = []  # lista de (start_pos, (cantidad, moneda))

    # Recolectar matches por aparición
    for m in combined_re.finditer(text):
        if m.group('range'):
            amount = m.group('range').strip()
            currency = m.group('cur1').strip()
            found_entries.append((m.start(), (amount, currency)))
            # También añadimos a currency_ranges para compatibilidad
            monetary_data['currency_ranges'].append((amount, currency))

        elif m.group('range_ext'):
            a = m.group('re_a').strip()
            b = m.group('re_b').strip()
            amount = f"{a}-{b}"
            currency = m.group('cur2').strip()
            found_entries.append((m.start(), (amount, currency)))
            monetary_data['currency_ranges_extended'].append((a, b, currency))

        elif m.group('num_en'):
            amount = m.group('num_en').strip()
            currency = m.group('cur3').strip()
            found_entries.append((m.start(), (amount, currency)))
            monetary_data['currency_in_format'].append((amount, currency))

        elif m.group('num_plain'):
            amount = m.group('num_plain').strip()
            currency = m.group('cur4').strip()
            found_entries.append((m.start(), (amount, currency)))
            monetary_data['currency_without_en'].append((amount, currency))

    # Ordenar por posición (por si finditer devolvió en otro orden por alternancia)
    found_entries.sort(key=lambda x: x[0])
    monedas_explicitas = [entry for _, entry in found_entries]

    # Rellenar currency_decimal y currency_with_symbols por patrones separados (compatibilidad)
    # decimales: "75.50 usd" o "200,00 mn"
    dec_re = re.compile(rf'\b(\d+(?:[.,]\d+)?)\s+({tokens_alt})\b', re.IGNORECASE)
    monetary_data['currency_decimal'] = [(m.group(1).strip(), m.group(2).strip()) for m in dec_re.finditer(text)]

    # símbolos: "$20 usd" o "$20 mlc"
    sym_re = re.compile(rf'(?:\$|€|¥|£)\s*(\d+(?:[.,]\d+)?)\s+({tokens_alt})\b', re.IGNORECASE)
    monetary_data['currency_with_symbols'] = [(m.group(1).strip(), m.group(2).strip()) for m in sym_re.finditer(text)]

    # Patrones implícitos (sin moneda explícita)
    implicit_patterns = {
        'precios_implicitos': re.compile(r'\b(?:sale\s+en|son|cuesta|vale|esta\s+en|está\s+en)\s+(\d+(?:[.,]\d+)?)', re.IGNORECASE),
        'price_changes': re.compile(r'\b(subió|subio|bajó|bajo)\s+(?:a\s+)?(\d+(?:[.,]\d+)?)', re.IGNORECASE),
        'labeled_prices': re.compile(r'\b(?:precio|valor|costo|costó)\s*:?\s*(\d+(?:[.,]\d+)?)', re.IGNORECASE),
        'preposition_prices': re.compile(r'\b(?:por|a|desde|hasta)\s+(\d+(?:[.,]\d+)?)', re.IGNORECASE),
        'discounts_percent': re.compile(r'(\d+)%\s*(?:off|de\s+descuento|descuento)', re.IGNORECASE),
        'discounts_absolute': re.compile(r'\brebajado\s+(?:a\s+)?(\d+(?:[.,]\d+)?)', re.IGNORECASE),
    }

    for key, regex in implicit_patterns.items():
        monetary_data[key] = [g if isinstance(g := (m.group(1) if m.groups() else m.group(0)), str) else g
                              for m in regex.finditer(text)]

    # Finalmente, asignar monedas_explicitas (lista de tuplas) — así el tester podrá hacer match[1]
    monetary_data['monedas_explicitas'] = monedas_explicitas

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
    Analiza el texto y lo enriquece con información sobre los patrones encontrados.
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
            elementos_detectados.append(f"{len(valid_phones)} teléfonos")
    
    if patterns.get('urls_raw'):
        elementos_detectados.append(f"{len(patterns['urls_raw'])} enlaces")
    
    if patterns.get('hashtags'):
        elementos_detectados.append(f"{len(patterns['hashtags'])} hashtags")
    
    if patterns.get('mentions'):
        elementos_detectados.append(f"{len(patterns['mentions'])} menciones")
    
    if elementos_detectados:
        return f"{text} [Patrones: {', '.join(elementos_detectados)}]"
    
    return text
