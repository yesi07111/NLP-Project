from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class BaseExtractor(ABC):
    """Clase base para todos los extractores de redes sociales"""
    
    DOMAINS: List[str] = []
    SITE_NAME: str = "Sitio"
    
    @abstractmethod
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        """Extrae información de la URL - DEBE SER IMPLEMENTADO"""
        pass
    
    def can_handle(self, domain: str) -> bool:
        """Determina si este extractor puede manejar el dominio"""
        # Coincidencia exacta para la mayoría de casos
        if domain in self.DOMAINS:
            return True
        
        # Manejo para subdominios www
        if domain.startswith('www.') and domain[4:] in self.DOMAINS:
            return True
        
        # Manejo especial para Tumblr - subdominios dinámicos
        if 'tumblr.com' in self.DOMAINS:
            # Cualquier subdominio que termine con .tumblr.com
            if domain.endswith('.tumblr.com'):
                return True
        
        return False
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """
        Formatea la salida final
        Puede ser sobrescrito por extractores específicos
        """
        emoji = data.get('emoji', '🔗')
        site_name = data.get('site_name', self.SITE_NAME)
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        
        # Formato genérico que funciona para la mayoría de casos
        username_display = f" de @{username}" if username else ""
        id_display = f" - ID: {content_id}" if content_id else ""
        type_display = f" - {content_type}" if content_type and content_type != "profile" else ""
        
        return f"[{emoji} {site_name}{username_display}{type_display}{id_display}]"

# Registro global de extractores
_EXTRACTORS_REGISTRY: List[BaseExtractor] = []

def register_extractor(extractor_class):
    """Decorador para registrar extractores"""
    instance = extractor_class()
    _EXTRACTORS_REGISTRY.append(instance)
    return extractor_class

def get_extractor(domain: str) -> Optional[BaseExtractor]:
    """Obtiene el extractor apropiado para el dominio"""
    for extractor in _EXTRACTORS_REGISTRY:
        if extractor.can_handle(domain):
            return extractor
    return None