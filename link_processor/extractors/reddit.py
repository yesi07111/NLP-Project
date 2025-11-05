# extractors/reddit.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class RedditExtractor(BaseExtractor):
    DOMAINS = ['reddit.com', 'www.reddit.com', 'old.reddit.com']
    SITE_NAME = 'Reddit'

    # Patrones regex para Reddit - ORDENADOS de más específico a más general
    PATTERNS = [
        # Comentarios específicos
        ("comment", r'^/r/([^/]+)/comments/([^/]+)/[^/]+/comment/([^/]+)/?$'),
        
        # Posts con títulos largos
        ("post_with_title", r'^/r/([^/]+)/comments/([^/]+)/[^/]+/?$'),
        
        # Posts directos (solo ID)
        ("post_direct", r'^/r/([^/]+)/comments/([^/]+)/?$'),
        
        # Secciones específicas de subreddit
        ("subreddit_wiki_page", r'^/r/([^/]+)/wiki/([^/]+)/?$'),
        ("subreddit_wiki", r'^/r/([^/]+)/wiki/?$'),
        ("subreddit_about", r'^/r/([^/]+)/about/?$'),
        ("subreddit_search", r'^/r/([^/]+)/search/?$'),
        ("subreddit_submit", r'^/r/([^/]+)/submit/?$'),
        
        # Listados de subreddit (hot, new, top, rising)
        ("subreddit_listing", r'^/r/([^/]+)/(hot|new|top|rising|controversial)/?$'),
        
        # Subreddit principal
        ("subreddit", r'^/r/([^/]+)/?$'),
        
        # Perfiles de usuario con secciones
        ("user_posts", r'^/u/([^/]+)/posts/?$'),
        ("user_comments", r'^/u/([^/]+)/comments/?$'),
        ("user_saved", r'^/u/([^/]+)/saved/?$'),
        ("user_upvoted", r'^/u/([^/]+)/upvoted/?$'),
        ("user_downvoted", r'^/u/([^/]+)/downvoted/?$'),
        ("user_gilded", r'^/u/([^/]+)/gilded/?$'),
        
        # Perfil de usuario (formato u/)
        ("user_profile", r'^/u/([^/]+)/?$'),
        
        # Perfil de usuario (formato user/)
        ("user_profile_alt", r'^/user/([^/]+)/?$'),
        
        # Mensajes
        ("messages_inbox", r'^/message/inbox/?$'),
        ("messages_unread", r'^/message/unread/?$'),
        ("messages_sent", r'^/message/sent/?$'),
        ("messages", r'^/message/?$'),
        
        # Chat
        ("chat", r'^/chat/?$'),
        
        # Listados globales
        ("listing_popular", r'^/popular/?$'),
        ("listing_all", r'^/all/?$'),
        ("listing_random", r'^/random/?$'),
        ("listing_friends", r'^/friends/?$'),
        
        # Página principal con sección
        ("home_listing", r'^/(hot|new|top|rising)/?$'),
        
        # Página principal
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, subreddit, content_id, additional_info = self._extract_reddit_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['reddit'].get(content_type, '📰'),
            'subreddit': subreddit,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_reddit_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, subreddit, content_id, additional_info = "home", "", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "comment":
                content_type, subreddit, content_id = "comment", groups[0], groups[2]
                additional_info["post_id"] = groups[1]
                
            elif pattern_type == "post_with_title":
                content_type, subreddit, content_id = "post", groups[0], groups[1]
                
            elif pattern_type == "post_direct":
                content_type, subreddit, content_id = "post", groups[0], groups[1]
                
            elif pattern_type == "subreddit_wiki_page":
                content_type, subreddit, content_id = "wiki", groups[0], groups[1]
            elif pattern_type == "subreddit_wiki":
                content_type, subreddit = "wiki", groups[0]
                
            elif pattern_type == "subreddit_about":
                content_type, subreddit = "about", groups[0]
                
            elif pattern_type == "subreddit_search":
                content_type, subreddit = "search", groups[0]
                if "q" in query_params:
                    additional_info["query"] = query_params["q"][0]
                    
            elif pattern_type == "subreddit_submit":
                content_type, subreddit = "submit", groups[0]
                
            elif pattern_type == "subreddit_listing":
                content_type, subreddit = "listing", groups[0]
                additional_info["sort"] = groups[1]
                
            elif pattern_type == "subreddit":
                content_type, subreddit = "subreddit", groups[0]
                
            elif pattern_type.startswith("user_"):
                if pattern_type in ["user_posts", "user_comments", "user_saved", 
                                  "user_upvoted", "user_downvoted", "user_gilded"]:
                    content_type, subreddit = pattern_type, groups[0]
                else:
                    content_type, subreddit = "user", groups[0]
                    
            elif pattern_type == "user_profile":
                content_type, subreddit = "user", groups[0]
                
            elif pattern_type == "user_profile_alt":
                content_type, subreddit = "user", groups[0]
                
            elif pattern_type.startswith("messages_"):
                content_type = "messages"
                additional_info["folder"] = pattern_type.split("_")[1]
            elif pattern_type == "messages":
                content_type = "messages"
                
            elif pattern_type == "chat":
                content_type = "chat"
                
            elif pattern_type.startswith("listing_"):
                content_type = "listing"
                subreddit = pattern_type.split("_")[1]
                
            elif pattern_type == "home_listing":
                content_type = "home"
                additional_info["sort"] = groups[0]
                
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, subreddit, content_id, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '📰')
        subreddit = data.get('subreddit', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        additional_info = data.get('additional_info', {})
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "post": "Post", "subreddit": "Subreddit", 
            "user": "Usuario", "comment": "Comentario",
            "wiki": "Wiki", "about": "Acerca de",
            "search": "Búsqueda", "submit": "Crear post",
            "listing": "Listado", "home": "Inicio",
            "messages": "Mensajes", "chat": "Chat",
            "user_posts": "Posts de Usuario", "user_comments": "Comentarios de Usuario",
            "user_saved": "Guardados de Usuario", "user_upvoted": "Upvotes de Usuario",
            "user_downvoted": "Downvotes de Usuario", "user_gilded": "Dorados de Usuario"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        # Manejo especial para búsquedas
        if content_type == "search" and "query" in additional_info:
            query = additional_info["query"]
            short_query = query[:15] + "..." if len(query) > 15 else query
            if subreddit:
                return f"[{emoji} {type_display} en r/{subreddit}: {short_query}]"
            else:
                return f"[{emoji} {type_display} de {self.SITE_NAME}: {short_query}]"
        
        # Construir la cadena de salida
        parts = [f"{emoji} {type_display} de {self.SITE_NAME}"]
        
        if subreddit:
            if content_type == "user":
                parts.append(f"de u/{subreddit}")
            else:
                parts.append(f"en r/{subreddit}")
        
        if content_id:
            # Acortar IDs largos pero mantener nombres de páginas wiki completos
            if content_type in ["post", "comment"]:
                short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
                parts.append(f"- ID: {short_id}")
            elif content_type == "wiki":
                parts.append(f"- {content_id}")
        
        # Información adicional
        if "sort" in additional_info:
            parts.append(f"({additional_info['sort']})")
        if "folder" in additional_info:
            parts.append(f"({additional_info['folder']})")
        
        return f"[{' '.join(parts)}]"