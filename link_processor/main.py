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