# extractors/facebook.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class FacebookExtractor(BaseExtractor):
    DOMAINS = ['facebook.com', 'fb.com']
    SITE_NAME = 'Facebook'
    
    # Patrones regex para diferentes tipos de URLs de Facebook
    # REORDENADO: rutas específicas primero, perfiles al final
    PATTERNS = {
        # Rutas específicas de Facebook - ALTA PRIORIDAD
        'watch': [
            r'^/watch$'
        ],
        'marketplace': [
            r'^/marketplace$',
            r'/marketplace/item/([^/?]+)',
            r'/marketplace/search/'
        ],
        # Contenido específico
        'group': [
            r'/groups/([^/?]+)/permalink/(\d+)',
            r'/groups/([^/?]+)'
        ],
        'event': [
            r'/events/([^/?]+)'
        ],
        'page': [
            r'/pages/[^/]+/(\d+)',
            r'/pg/([^/?]+)'
        ],
        'video': [
            r'/watch/\?v=(\d+)',
            r'/video\.php\?v=(\d+)',
            r'/reel/([^/?]+)'
        ],
        'game': [
            r'/games/([^/?]+)'
        ],
        'photo': [
            r'/photo\.php\?fbid=(\d+)',
            r'/photo/([^/?]+)'
        ],
        'story': [
            r'/story\.php\?story_fbid=(\d+)'
        ],
        'post': [
            r'/posts/([^/?]+)'
        ],
        'live': [
            r'/live/([^/?]+)'
        ],
        'stories': [
            r'/stories/([^/?]+)'
        ],
        'gaming': [
            r'/gaming/([^/?]+)'
        ],
        'note': [
            r'/notes/[^/]+/([^/?]+)'
        ],
        # Perfiles - BAJA PRIORIDAD (debe ir al final)
        'profile': [
            r'/profile\.php\?id=(\d+)'
        ]
    }
    
    # Rutas reservadas que NO son perfiles
    RESERVED_PATHS = {
        'watch', 'marketplace', 'games', 'live', 'stories', 'gaming', 'notes',
        'groups', 'events', 'pages', 'pg', 'video', 'photo', 'story', 'posts',
        'reel'
    }
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        page_type, content_id, sub_type = self._extract_facebook_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['facebook'].get(page_type, '📘'),
            'content_id': content_id,
            'page_type': page_type,
            'sub_type': sub_type
        }
    
    def _extract_facebook_info(self, parsed_url) -> Tuple[str, str, str]:
        """Extrae metadata completa de Facebook usando expresiones regulares"""
        path = parsed_url.path
        query = parsed_url.query
        full_path = path + ('?' + query if query else '')
        page_type = ""
        content_id = ""
        sub_type = ""
        
        # Verificar todos los patrones regex en orden de especificidad
        for page_type_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                # Para patrones que incluyen query parameters, buscar en full_path
                # Para otros, buscar solo en path
                search_text = full_path if '?' in pattern else path
                match = re.search(pattern, search_text)
                if match:
                    page_type = page_type_name
                    
                    # Extraer content_id según el patrón
                    if match.groups():
                        content_id = match.group(1)
                    
                    # Casos especiales para subtipos
                    if page_type_name == 'group' and 'permalink' in path:
                        sub_type = "permalink"
                    elif page_type_name == 'video' and 'reel' in path:
                        sub_type = "reel"
                    elif page_type_name == 'marketplace' and 'search' in path:
                        sub_type = "search"
                    
                    return page_type, content_id, sub_type
        
        # Caso especial: perfiles por username (debe ser el último recurso)
        # Solo si no hemos encontrado ningún otro tipo y el path es simple
        if not page_type and path.strip('/') and '/' not in path.strip('/'):
            current_path = path.strip('/')
            # Verificar que NO sea una ruta reservada
            if current_path not in self.RESERVED_PATHS:
                page_type = "profile"
                content_id = current_path
                return page_type, content_id, sub_type
        
        return page_type, content_id, sub_type
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para Facebook basado en la lógica original"""
        emoji = data.get('emoji', '📘')
        content_id = data.get('content_id', '')
        page_type = data.get('page_type', '')
        sub_type = data.get('sub_type', '')
        
        content_id_display = f" - ID: {content_id}" if content_id else ""
        sub_display = f" ({sub_type})" if sub_type else ""
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "profile": "Perfil", "group": "Grupo", "event": "Evento", 
            "page": "Página", "video": "Video", "marketplace": "Marketplace", 
            "game": "Juego", "photo": "Foto", "story": "Historia",
            "post": "Publicación", "watch": "Watch", "live": "Live",
            "stories": "Stories", "gaming": "Gaming", "note": "Nota"
        }
        
        type_display = type_names.get(page_type, "Contenido")
        
        return f"[{emoji} {type_display} de {self.SITE_NAME}{sub_display}{content_id_display}]"