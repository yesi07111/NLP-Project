# extractors/snapchat.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class SnapchatExtractor(BaseExtractor):
    DOMAINS = ['snapchat.com', 'www.snapchat.com']
    SITE_NAME = 'Snapchat'

    # Patrones regex para Snapchat - REORDENADOS Y EXPANDIDOS
    PATTERNS = [
        # Lentes con acciones específicas (MÁS ESPECÍFICOS PRIMERO)
        ("lens_try", r'^/lenses/([^/]+)/try/?$'),
        ("lens_direct", r'^/lenses/([^/]+)/?$'),
        
        # Discover con subsecciones específicas
        ("discover_edition", r'^/discover/([^/]+)/edition/?$'),
        ("discover_show", r'^/discover/([^/]+)/show/?$'),
        ("discover_topic", r'^/discover/([^/]+)/?$'),
        
        # Secciones de usuario específicas
        ("add_user", r'^/add/([^/]+)/?$'),
        ("stories_user", r'^/stories/([^/]+)/?$'),
        ("chat_user", r'^/chat/([^/]+)/?$'),
        ("snapcode_user", r'^/snapcode/([^/]+)/?$'),
        
        # Contenido específico con IDs
        ("spotlight", r'^/spotlight/([^/]+)/?$'),
        ("filter", r'^/filters/([^/]+)/?$'),
        ("bitmoji", r'^/bitmoji/([^/]+)/?$'),
        
        # Mapa con ubicaciones
        ("map_location", r'^/map/([^/]+)/?$'),
        
        # Business con secciones específicas
        ("business_section", r'^/business/([^/]+)/?$'),
        
        # Store con productos específicos
        ("store_product", r'^/store/([^/]+)/?$'),
        
        # Games específicos
        ("games_game", r'^/games/([^/]+)/?$'),
        
        # Minis específicos
        ("minis_app", r'^/minis/([^/]+)/?$'),
        
        # Originals específicos
        ("originals_show", r'^/originals/([^/]+)/?$'),
        
        # Ads con campañas específicas
        ("ads_campaign", r'^/ads/([^/]+)/?$'),
        
        # Secciones principales SIN parámetros (antes de las con parámetros)
        ("add_main", r'^/add/?$'),
        ("stories_main", r'^/stories/?$'),
        ("discover_main", r'^/discover/?$'),
        ("map_main", r'^/map/?$'),
        ("memories_main", r'^/memories/?$'),
        ("scan_main", r'^/scan/?$'),
        ("ads_main", r'^/ads/?$'),
        ("business_main", r'^/business/?$'),
        ("store_main", r'^/store/?$'),
        ("games_main", r'^/games/?$'),
        ("minis_main", r'^/minis/?$'),
        ("cameos_main", r'^/cameos/?$'),
        ("originals_main", r'^/originals/?$'),
        
        # Perfil de usuario (ÚLTIMO - más general)
        ("profile", r'^/([^/?]+)/?$'),
        
        # Página principal (MÁS GENERAL)
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, username, additional_info = self._extract_snapchat_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['snapchat'].get(content_type, '👻'),
            'username': username,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_snapchat_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, content_id, username, additional_info = "home", "", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "lens_try":
                content_type, content_id = "lens_try", groups[0]
            elif pattern_type == "lens_direct":
                content_type, content_id = "lens", groups[0]
                
            elif pattern_type == "discover_edition":
                content_type, content_id = "discover_edition", groups[0]
            elif pattern_type == "discover_show":
                content_type, content_id = "discover_show", groups[0]
            elif pattern_type == "discover_topic":
                content_type, content_id = "discover", groups[0]
                
            elif pattern_type == "add_user":
                content_type, username = "add", groups[0]
            elif pattern_type == "add_main":
                content_type = "add"
                
            elif pattern_type == "stories_user":
                content_type, username = "stories", groups[0]
            elif pattern_type == "stories_main":
                content_type = "stories"
                
            elif pattern_type == "chat_user":
                content_type, username = "chat", groups[0]
                
            elif pattern_type == "snapcode_user":
                content_type, username = "snapcode", groups[0]
                
            elif pattern_type == "spotlight":
                content_type, content_id = "spotlight", groups[0]
                
            elif pattern_type == "map_location":
                content_type, content_id = "map", groups[0]
            elif pattern_type == "map_main":
                content_type = "map"
                
            elif pattern_type == "filter":
                content_type, content_id = "filter", groups[0]
                
            elif pattern_type == "bitmoji":
                content_type, content_id = "bitmoji", groups[0]
                
            elif pattern_type == "ads_campaign":
                content_type, content_id = "ads", groups[0]
            elif pattern_type == "ads_main":
                content_type = "ads"
                
            elif pattern_type == "business_section":
                content_type, content_id = "business", groups[0]
            elif pattern_type == "business_main":
                content_type = "business"
                
            elif pattern_type == "store_product":
                content_type, content_id = "store", groups[0]
            elif pattern_type == "store_main":
                content_type = "store"
                
            elif pattern_type == "games_game":
                content_type, content_id = "games", groups[0]
            elif pattern_type == "games_main":
                content_type = "games"
                
            elif pattern_type == "minis_app":
                content_type, content_id = "minis", groups[0]
            elif pattern_type == "minis_main":
                content_type = "minis"
                
            elif pattern_type == "originals_show":
                content_type, content_id = "originals", groups[0]
            elif pattern_type == "originals_main":
                content_type = "originals"
                
            elif pattern_type == "memories_main":
                content_type = "memories"
            elif pattern_type == "scan_main":
                content_type = "scan"
            elif pattern_type == "cameos_main":
                content_type = "cameos"
            elif pattern_type == "discover_main":
                content_type = "discover"
                
            elif pattern_type == "profile":
                # Verificar que no sea una ruta reservada
                reserved = {
                    'add', 'discover', 'stories', 'spotlight', 'map', 'memories',
                    'scan', 'chat', 'lenses', 'filters', 'bitmoji', 'snapcode',
                    'ads', 'business', 'store', 'games', 'minis', 'cameos', 'originals'
                }
                if groups[0] not in reserved:
                    content_type, username = "profile", groups[0]
                else:
                    continue
                    
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, username, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '👻')
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        additional_info = data.get('additional_info', {})
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "add": "Agregar", "discover": "Discover", "discover_edition": "Discover Edition",
            "discover_show": "Discover Show", "stories": "Historia", "spotlight": "Spotlight",
            "map": "Mapa", "memories": "Memories", "scan": "Scan",
            "chat": "Chat", "lens": "Lens", "lens_try": "Probar Lens",
            "filter": "Filter", "bitmoji": "Bitmoji", "snapcode": "Snapcode",
            "ads": "Anuncios", "business": "Negocios", "store": "Tienda",
            "games": "Juegos", "minis": "Minis", "cameos": "Cameos",
            "originals": "Originals", "profile": "Perfil", "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        # Construir la cadena de salida
        parts = [f"{emoji} {type_display} de {self.SITE_NAME}"]
        
        if username:
            parts.append(f"de {username}")
        
        if content_id:
            # NUNCA acortar content_id - mostrar completo
            parts.append(f"- {content_id}")
        
        return f"[{' '.join(parts)}]"