from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Tuple
import re

def parse_url_components(url: str) -> Dict:
    """Parse una URL y retorna todos sus componentes"""
    parsed = urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': parse_qs(parsed.query),
        'fragment': parsed.fragment,
        'domain': parsed.netloc.lower(),
        'path_parts': [p for p in parsed.path.strip('/').split('/') if p]
    }

def extract_query_param(query_params: Dict, key: str, default: str = '') -> str:
    """Extrae un parámetro de consulta de forma segura"""
    return query_params.get(key, [default])[0]

def normalize_domain(domain: str) -> str:
    """Normaliza el dominio removiendo www y protocolos"""
    domain = re.sub(r'^www\.', '', domain)
    domain = re.sub(r'^https?://', '', domain)
    return domain.split('/')[0]  # Remover paths del dominio