# extractors/imgur.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class ImgurExtractor(BaseExtractor):
    DOMAINS = ['imgur.com', 'i.imgur.com']
    SITE_NAME = 'Imgur'

    # Patrones regex para Imgur - REORDENADOS Y MEJORADOS
    # Patrones regex para Imgur - ORDENADOS y con secciones explícitas
    PATTERNS = [
        # Subdominio directo (i.imgur.com)
        ("image_direct_ext", r'^/([a-zA-Z0-9]+)\.(jpg|jpeg|png|gif|gifv|mp4)$'),

        # Página principal
        ("home", r'^/?$'),

        # Secciones estáticas / institucionales
        ("popular", r'^/popular/?$'),
        ("trending", r'^/t/?$'),
        ("new", r'^/new/?$'),
        ("hot", r'^/hot/?$'),
        ("rising", r'^/rising/?$'),
        ("upload", r'^/upload/?$'),
        ("notifications", r'^/notifications/?$'),
        ("messages", r'^/messages/?$'),
        ("help", r'^/help/?$'),
        ("tos", r'^/tos/?$'),
        ("privacy", r'^/privacy/?$'),
        ("app", r'^/app/?$'),
        ("store", r'^/store/?$'),
        ("account_settings", r'^/account/settings/?$'),

        # Búsquedas
        ("search", r'^/search(?:/)?$'),

        # Meme generator
        ("memegen_text", r'^/memegen/([^/]+)/([^/]+)/?$'),
        ("memegen_base", r'^/memegen/?$'),

        # Galerías / álbumes / colecciones
        ("gallery", r'^/gallery/([a-zA-Z0-9]+)/?$'),
        ("album", r'^/a/([a-zA-Z0-9]+)/?$'),
        ("collection", r'^/collection/([a-zA-Z0-9]+)/?$'),

        # Temas
        ("topic_post", r'^/t/([a-zA-Z0-9_-]+)/([a-zA-Z0-9]+)/?$'),
        ("topic", r'^/topic/([a-zA-Z0-9_-]+)/?$'),

        # Usuarios
        ("user_posts", r'^/user/([a-zA-Z0-9_-]+)/posts/?$'),
        ("user_comments", r'^/user/([a-zA-Z0-9_-]+)/comments/?$'),
        ("user_favorites", r'^/user/([a-zA-Z0-9_-]+)/favorites/?$'),
        ("user", r'^/user/([a-zA-Z0-9_-]+)/?$'),

        # Subreddit
        ("subreddit", r'^/r/([a-zA-Z0-9_-]+)/([a-zA-Z0-9]+)/?$'),

        # Imágenes
        ("image_with_ext", r'^/([a-zA-Z0-9]+)\.(jpg|jpeg|png|gif|mp4)$'),
        ("image", r'^/([a-zA-Z0-9]+)/?$'),
        ("image_direct_no_ext", r'^/([a-zA-Z0-9]+)$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, additional_info = self._extract_imgur_info(parsed_url)
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['imgur'].get(content_type, '🖼️'),
            'content_id': content_id,
            'additional_info': additional_info,
            'content_type': content_type,
        }

    def _extract_imgur_info(self, parsed_url) -> Tuple[str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, content_id, additional_info = "home", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type in {"image_direct_ext", "image_direct_no_ext", "image_with_ext"}:
                content_type = "image"
                content_id = groups[0]
                if "direct" in pattern_type:
                    additional_info["direct"] = True

            elif pattern_type in {"gallery", "album", "collection"}:
                content_type = pattern_type
                content_id = groups[0]

            elif pattern_type in {"popular", "trending", "new", "hot", "rising",
                                "upload", "notifications", "messages",
                                "help", "tos", "privacy", "app", "store",
                                "account_settings", "home"}:
                content_type = pattern_type

            elif pattern_type == "memegen_text":
                content_type = "memegen"
                additional_info["top_text"] = groups[0]
                additional_info["bottom_text"] = groups[1]
            elif pattern_type == "memegen_base":
                content_type = "memegen"

            elif pattern_type == "topic_post":
                content_type, content_id = "image", groups[1]
            elif pattern_type == "topic":
                content_type, content_id = "topic", groups[0]

            elif pattern_type.startswith("user_"):
                content_type, content_id = pattern_type, groups[0]
            elif pattern_type == "user":
                content_type, content_id = "user", groups[0]

            elif pattern_type == "subreddit":
                content_type, content_id = "subreddit", groups[1]
                additional_info["subreddit"] = groups[0]

            elif pattern_type == "search":
                content_type = "search"
                if "q" in query_params:
                    additional_info["query"] = query_params["q"][0].replace("+", " ")

            elif pattern_type == "image":
                reserved = {
                    "popular", "t", "new", "hot", "rising", "upload", "memegen", "search",
                    "help", "tos", "privacy", "app", "store", "messages", "notifications",
                    "account", "gallery", "a", "topic", "user", "r", "collection"
                }
                if groups[0] not in reserved:
                    content_type, content_id = "image", groups[0]
                else:
                    continue

            break

        return content_type, content_id, additional_info

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get("emoji", "🖼️")
        content_id = data.get("content_id", "")
        content_type = data.get("content_type", "")
        info = data.get("additional_info", {})

        type_names = {
            "image": "Imagen", "gallery": "Galería", "album": "Álbum",
            "topic": "Tema", "user": "Usuario", "user_posts": "Posts de Usuario",
            "user_comments": "Comentarios de Usuario", "user_favorites": "Favoritos de Usuario",
            "subreddit": "Post en Subreddit", "collection": "Colección",
            "memegen": "Meme Generator", "search": "Búsqueda", "popular": "Popular",
            "trending": "Tendencias", "new": "Nuevo", "hot": "Hot", "rising": "Rising",
            "upload": "Subir", "messages": "Mensajes", "notifications": "Notificaciones",
            "account_settings": "Configuración", "help": "Ayuda",
            "tos": "Términos de Servicio", "privacy": "Privacidad",
            "app": "App Móvil", "store": "Tienda", "home": "Inicio",
        }

        name = type_names.get(content_type, "Contenido")

        if content_type == "search" and "query" in info:
            q = info["query"]
            return f"[{emoji} {name}: {q[:20] + '...' if len(q) > 20 else q}]"

        if content_type == "memegen" and "top_text" in info:
            return f"[{emoji} {name}: {info['top_text']}/{info['bottom_text']}]"

        if content_type == "subreddit" and "subreddit" in info:
            return f"[{emoji} {name} en r/{info['subreddit']} - ID: {content_id}]"

        if content_id:
            short_id = content_id[:9] + "..." if (content_type == "gallery" and len(content_id) > 10) else \
                    (content_id[:10] + "..." if len(content_id) > 10 else content_id)
            return f"[{emoji} {name} - ID: {short_id}]"

        return f"[{emoji} {name}]"
