# extractors/instagram.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class InstagramExtractor(BaseExtractor):
    DOMAINS = ['instagram.com', 'www.instagram.com']
    SITE_NAME = 'Instagram'

    # Patrones regex para Instagram - ORDENADOS de más específico a más general
    PATTERNS = [
        # Stories highlights (más específico primero)
        ("stories_highlights", r'^/stories/highlights/([^/]+)/?$'),
        
        # Stories individuales
        ("stories", r'^/stories/([^/]+)/([^/]+)/?$'),
        
        # Guides en perfiles
        ("profile_guide", r'^/([^/]+)/guide/([^/]+)/?$'),
        
        # Secciones específicas de perfil (tagged, reels, etc.)
        ("profile_section", r'^/([^/]+)/(tagged|reels|guides|channel|saved|shop)/?$'),
        
        # Posts, Reels, TV (contenido multimedia)
        ("media_post", r'^/p/([^/]+)/?$'),
        ("media_reel", r'^/reel/([^/]+)/?$'),
        ("media_tv", r'^/tv/([^/]+)/?$'),
        
        # Explore con subsecciones
        ("explore_people", r'^/explore/people/?$'),
        ("explore_places", r'^/explore/places/?$'),
        ("explore_locations", r'^/explore/locations/([^/]+)/?$'),
        ("explore_tags", r'^/explore/tags/([^/]+)/?$'),
        ("explore_tags_direct", r'^/tags/([^/]+)/?$'),
        
        # Direct messages
        ("direct_thread", r'^/direct/t/([^/]+)/?$'),
        ("direct_inbox", r'^/direct/(?:inbox)?/?$'),
        
        # Shop
        ("shop_product", r'^/shop/product/([^/]+)/?$'),
        ("profile_shop_only", r'^/shop/?$'),
        
        # Live
        ("live", r'^/([^/]+)/live/?$'),
        
        # Threads
        ("thread", r'^/threads/([^/]+)/?$'),
        
        # Perfil con formato _u
        ("profile_u", r'^/_u/([^/]+)/?$'),
        
        # Explore general (debe ir después de las subsecciones)
        ("explore", r'^/explore/?$'),
        
        # Perfil básico (más general - debe ir al final)
        ("profile", r'^/([^/]+)/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, username, content_id, additional_info = self._extract_instagram_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['instagram'].get(content_type, '📷'),
            'username': username,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_instagram_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, username, content_id, additional_info = "home", "", "", {}

        # Lista de rutas reservadas que NO son perfiles
        reserved_paths = {
            'explore', 'direct', 'shop', 'p', 'reel', 'stories', 'tv', 'threads',
            'accounts', 'about', 'blog', 'press', 'legal', 'download', 'creators',
            'business', '_u', 'reels', 'guides', 'channel', 'saved', 'tagged'
        }

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "stories_highlights":
                content_type, content_id = "highlight", groups[0]
                
            elif pattern_type == "stories":
                content_type, username, content_id = "story", groups[0], groups[1]
                
            elif pattern_type == "profile_guide":
                content_type, username, content_id = "guide", groups[0], groups[1]
                
            elif pattern_type == "profile_section":
                content_type, username = f"profile_{groups[1]}", groups[0]
                
            elif pattern_type in ["media_post", "media_reel", "media_tv"]:
                content_type = pattern_type.split('_')[1]  # "post", "reel", "tv"
                if content_type == "tv":
                    content_type = "igtv"  # Mapear a "igtv" 
                content_id = groups[0]
                
            elif pattern_type in ["explore_people", "explore_places"]:
                content_type = pattern_type
                
            elif pattern_type == "explore_locations":
                content_type, content_id = "location", groups[0]
                
            elif pattern_type in ["explore_tags", "explore_tags_direct"]:
                content_type, content_id = "hashtag", groups[0]
                
            elif pattern_type == "direct_thread":
                content_type, content_id = "direct_message", groups[0]
                
            elif pattern_type == "direct_inbox":
                content_type = "direct_inbox"
                
            elif pattern_type == "shop_product":
                content_type, content_id = "shop_product", groups[0]
                
            elif pattern_type == "profile_shop_only":
                content_type = "shop"
                
            elif pattern_type == "live":
                content_type, username = "live", groups[0]
                
            elif pattern_type == "thread":
                content_type, content_id = "thread", groups[0]
                
            elif pattern_type == "profile_u":
                content_type, username = "profile", groups[0]
                
            elif pattern_type == "explore":
                content_type = "explore"
                
            elif pattern_type == "profile":
                # Verificar que no sea una ruta reservada
                if groups[0] not in reserved_paths:
                    content_type, username = "profile", groups[0]
                else:
                    continue

            break

        return content_type, username, content_id, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '📷')
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        
        type_names = {
            "profile": "Perfil", "post": "Publicación", "reel": "Reel", 
            "story": "Historia", "highlight": "Highlight", "live": "Transmisión en vivo",
            "guide": "Guía", "igtv": "IG TV", "thread": "Thread",
            "location": "Ubicación", "hashtag": "Hashtag", "explore": "Explorar",
            "explore_people": "Explorar Personas", "explore_places": "Explorar Lugares",
            "direct_message": "Mensaje directo", "direct_inbox": "Bandeja directa",
            "profile_tagged": "Perfil - Etiquetado", "profile_reels": "Perfil - Reels",
            "profile_guides": "Perfil - Guías", "profile_channel": "Perfil - Canal",
            "profile_saved": "Perfil - Guardado", "profile_shop": "Perfil - Tienda",
            "shop": "Tienda", "shop_product": "Producto", "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        if username and content_id:
            short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
            return f"[{emoji} {type_display} de @{username} - ID: {short_id}]"
        elif username:
            return f"[{emoji} {type_display} de @{username}]"
        elif content_id:
            short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
            return f"[{emoji} {type_display} - ID: {short_id}]"
        else:
            return f"[{emoji} {type_display} de {self.SITE_NAME}]"