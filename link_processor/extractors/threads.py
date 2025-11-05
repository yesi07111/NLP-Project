# extractors/threads.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class ThreadsExtractor(BaseExtractor):
    DOMAINS = ['threads.net', 'www.threads.net']
    SITE_NAME = 'Threads'


    PATTERNS = [

        ("post_with_user_at", r'^/@([a-zA-Z0-9._-]+)/post/([0-9]+)/?$'),
        ("post_with_user", r'^/([a-zA-Z0-9._-]+)/post/([0-9]+)/?$'),
        
        ("post_direct", r'^/post/([0-9]+)/?$'),
        
        ("search_term", r'^/search/([a-zA-Z0-9%_-]+)/?$'),
    
        ("profile_replies_at", r'^/@([a-zA-Z0-9._-]+)/replies/?$'),
        ("profile_reposts_at", r'^/@([a-zA-Z0-9._-]+)/reposts/?$'),
        ("profile_likes_at", r'^/@([a-zA-Z0-9._-]+)/likes/?$'),
        
        ("profile_replies", r'^/([a-zA-Z0-9._-]+)/replies/?$'),
        ("profile_reposts", r'^/([a-zA-Z0-9._-]+)/reposts/?$'),
        ("profile_likes", r'^/([a-zA-Z0-9._-]+)/likes/?$'),
        
        ("search", r'^/search/?$'),
        ("explore", r'^/explore/?$'),
        ("notifications", r'^/notifications/?$'),
        
        ("profile_at", r'^/@([a-zA-Z0-9._-]+)/?$'),
        ("profile", r'^/([a-zA-Z0-9._-]+)/?$'),
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, additional_info = self._extract_threads_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['threads'].get(content_type, '🧵'),
            'content_id': content_id,
            'additional_info': additional_info,
            'content_type': content_type,
        }

    def _extract_threads_info(self, parsed_url) -> Tuple[str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "home"
        content_id = ""
        additional_info = {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "post_with_user_at":
                content_type, content_id = "post", groups[1]
                additional_info["username"] = groups[0]
            elif pattern_type == "post_with_user":
                content_type, content_id = "post", groups[1]
                additional_info["username"] = groups[0]
            elif pattern_type == "post_direct":
                content_type, content_id = "post", groups[0]
            elif pattern_type == "search_term":
                content_type, content_id = "search", groups[0].replace('%20', ' ')
            elif pattern_type == "profile_replies_at":
                content_type, content_id = "profile_replies", groups[0]
            elif pattern_type == "profile_reposts_at":
                content_type, content_id = "profile_reposts", groups[0]
            elif pattern_type == "profile_likes_at":
                content_type, content_id = "profile_likes", groups[0]
            elif pattern_type == "profile_replies":
                content_type, content_id = "profile_replies", groups[0]
            elif pattern_type == "profile_reposts":
                content_type, content_id = "profile_reposts", groups[0]
            elif pattern_type == "profile_likes":
                content_type, content_id = "profile_likes", groups[0]
            elif pattern_type == "search":
                content_type = "search"
            elif pattern_type == "explore":
                content_type = "explore"
            elif pattern_type == "notifications":
                content_type = "notifications"
            elif pattern_type == "profile_at":
                content_type, content_id = "profile", groups[0]
            elif pattern_type == "profile":

                reserved = {'search', 'explore', 'notifications', 'post'}
                if groups[0] not in reserved:
                    content_type, content_id = "profile", groups[0]
                else:
                    continue
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, additional_info

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '🧵')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        info = data.get('additional_info', {})
        
        type_names = {
            "post": "Thread",
            "profile": "Perfil",
            "search": "Búsqueda",
            "explore": "Explorar", 
            "notifications": "Notificaciones",
            "profile_replies": "Respuestas",
            "profile_reposts": "Reposts",
            "profile_likes": "Me gusta",
            "home": "Inicio"
        }

        name = type_names.get(content_type, "Contenido")


        if content_type == "search" and content_id:
            search_term = content_id
            short_term = search_term[:20] + "..." if len(search_term) > 20 else search_term
            return f"[{emoji} {name}: {short_term}]"


        parts = []
        
        if content_id and content_type == "post":
            parts.append(f"ID: {content_id}")
        

        if content_type in ["profile", "profile_replies", "profile_reposts", "profile_likes"]:
            parts.append(f"@{content_id}")
        elif "username" in info:
            parts.append(f"@{info['username']}")

        parts_display = " - " + ", ".join(parts) if parts else ""

        return f"[{emoji} {name} de {self.SITE_NAME}{parts_display}]"