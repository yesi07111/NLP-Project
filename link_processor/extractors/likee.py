# extractors/likee.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class LikeeExtractor(BaseExtractor):
    DOMAINS = ['likee.com', 'www.likee.com']
    SITE_NAME = 'Likee'

    # Patrones regex para Likee - ORDENADOS de más específico a más general
    PATTERNS = [
        # Videos individuales con ID específico (más específico primero)
        ("video_detail", r'^/video/([0-9]+)/?$'),
        
        # Secciones específicas de perfil (videos, likes, followers, following)
        ("profile_videos", r'^/@([^/]+)/video/?$'),
        ("profile_likes", r'^/@([^/]+)/like/?$'),
        ("profile_followers", r'^/@([^/]+)/follower/?$'),
        ("profile_following", r'^/@([^/]+)/following/?$'),
        
        # Perfiles de usuario
        ("profile", r'^/@([^/]+)/?$'),
        
        # Hashtags
        ("hashtag", r'^/hashtag/([^/]+)/?$'),
        
        # Live streams
        ("live", r'^/live/([^/]+)/?$'),
        
        # Trending con categorías
        ("trending_category", r'^/trending/([^/]+)/?$'),
        ("trending", r'^/trending/?$'),
        
        # Efectos
        ("effect", r'^/effect/([^/]+)/?$'),
        
        # Música
        ("music", r'^/music/([^/]+)/?$'),
        
        # Descubrir/Explore con categorías
        ("discover_category", r'^/(?:discover|explore)/([^/]+)/?$'),
        ("discover", r'^/(?:discover|explore)/?$'),
        
        # Búsqueda
        ("search", r'^/search/?$'),
        
        # Notificaciones
        ("notifications", r'^/notification/?$'),
        
        # Mensajes
        ("messages", r'^/message/?$'),
        
        # Configuración
        ("settings", r'^/setting/?$'),
        
        # Página principal (más general)
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, username, additional_info = self._extract_likee_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['likee'].get(content_type, '🎬'),
            'username': username,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_likee_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, content_id, username, additional_info = "home", "", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "video_detail":
                content_type, content_id = "video", groups[0]
                
            elif pattern_type in ["profile_videos", "profile_likes", "profile_followers", "profile_following"]:
                content_type, username = pattern_type, groups[0]
                
            elif pattern_type == "profile":
                content_type, username = "profile", groups[0]
                
            elif pattern_type == "hashtag":
                content_type, content_id = "hashtag", groups[0]
                
            elif pattern_type == "live":
                content_type, username = "live", groups[0]
                
            elif pattern_type == "trending_category":
                content_type, content_id = "trending", groups[0]
            elif pattern_type == "trending":
                content_type = "trending"
                
            elif pattern_type == "effect":
                content_type, content_id = "effect", groups[0]
                
            elif pattern_type == "music":
                content_type, content_id = "music", groups[0]
                
            elif pattern_type == "discover_category":
                content_type, content_id = "discover", groups[0]
            elif pattern_type == "discover":
                content_type = "discover"
                
            elif pattern_type == "search":
                content_type = "search"
                if "keyword" in query_params:
                    additional_info["query"] = query_params["keyword"][0]
                elif "q" in query_params:
                    additional_info["query"] = query_params["q"][0]
                    
            elif pattern_type == "notifications":
                content_type = "notifications"
                
            elif pattern_type == "messages":
                content_type = "messages"
                
            elif pattern_type == "settings":
                content_type = "settings"
                
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, username, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '🎬')
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        additional_info = data.get('additional_info', {})
        
        type_names = {
            "video": "Video", "profile": "Perfil", 
            "hashtag": "Hashtag", "live": "Transmisión en vivo",
            "trending": "Trending", "effect": "Efecto", "music": "Música",
            "discover": "Descubrir", "notifications": "Notificaciones",
            "messages": "Mensajes", "settings": "Configuración",
            "search": "Búsqueda", "profile_videos": "Perfil - Videos",
            "profile_likes": "Perfil - Me gusta", "profile_followers": "Perfil - Seguidores",
            "profile_following": "Perfil - Siguiendo", "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        if content_type == "search" and "query" in additional_info:
            query = additional_info["query"]
            short_query = query[:15] + "..." if len(query) > 15 else query
            return f"[{emoji} {type_display}: {short_query}]"
        
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