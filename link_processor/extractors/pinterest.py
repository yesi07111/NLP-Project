# extractors/pinterest.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class PinterestExtractor(BaseExtractor):
    DOMAINS = ['pinterest.com', 'www.pinterest.com']
    SITE_NAME = 'Pinterest'

    PATTERNS = [
        # Crear pin (antes que los pins normales)
        ("create_pin", r'^/pin/create/?$'),

        # Pin individual (solo IDs numéricos)
        ("pin_with_params", r'^/pin/(\d+)/[^/?]+/?$'),
        ("pin_direct", r'^/pin/(\d+)/?$'),

        # Pin con slug no numérico (por ejemplo, /pin/create/button o /pin/something)
        ("pin_slug", r'^/pin/([^/?]+)(?:/[^/?]+)?/?$'),

        # Secciones específicas del perfil
        ("profile_following", r'^/@([^/?]+)/following/?$'),
        ("profile_followers", r'^/@([^/?]+)/followers/?$'),
        ("profile_likes", r'^/@([^/?]+)/likes/?$'),
        ("profile_tries", r'^/@([^/?]+)/tries/?$'),
        ("profile_boards", r'^/@([^/?]+)/boards/?$'),
        ("profile_pins", r'^/@([^/?]+)/pins/?$'),
        ("profile", r'^/@([^/?]+)/?$'),

        # Búsqueda (antes de board)
        ("search_pins", r'^/search/pins/?$'),
        ("search_query", r'^/search/([^/?]+)/?$'),
        ("search", r'^/search/?$'),

        # Ideas
        ("ideas_topic", r'^/ideas/([^/?]+)/[^/?]+/?$'),
        ("ideas", r'^/ideas/([^/?]+)/?$'),

        # Business
        ("business_section", r'^/business/([^/?]+)/?$'),
        ("business", r'^/business/?$'),

        # Analytics
        ("analytics", r'^/analytics/?$'),

        # Ads
        ("ads_section", r'^/ads/([^/?]+)/?$'),
        ("ads", r'^/ads/?$'),

        # Shop
        ("shop_category", r'^/shop/([^/?]+)/?$'),
        ("shop", r'^/shop/?$'),

        # Categorías
        ("category", r'^/categories/([^/?]+)/?$'),

        # Following
        ("following", r'^/following/?$'),

        # Tableros
        ("board_specific", r'^/([^/?]+)/([^/?]+)/?$'),

        # Página principal
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, username, additional_info = self._extract_pinterest_info(parsed_url)
        emoji_map = EMOJI_MAPS.get('pinterest', {})
        emoji = emoji_map.get(content_type, '📌')
        # Asegurar emoji correcto para inicio
        if content_type == 'home':
            emoji = '🏠'

        return {
            'site_name': self.SITE_NAME,
            'emoji': emoji,
            'username': username,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }

    def _extract_pinterest_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path.rstrip('/')
        query_params = parse_qs(parsed_url.query)
        content_type, content_id, username, additional_info = "home", "", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type in ["pin_with_params", "pin_direct"]:
                content_type, content_id = "pin", groups[0]
            
            elif pattern_type == "pin_slug":
                content_type, content_id = "pin", groups[0]

            elif pattern_type == "create_pin":
                content_type = "create_pin"

            elif pattern_type.startswith("profile_"):
                content_type, username = pattern_type, groups[0]
                content_id = pattern_type.split("_")[1]

            elif pattern_type == "profile":
                content_type, username = "profile", groups[0]

            elif pattern_type == "board_specific":
                reserved = {
                    'pin', 'search', 'ideas', 'business', 'analytics',
                    'ads', 'shop', 'following', 'categories'
                }
                if groups[0] not in reserved:
                    content_type, username, content_id = "board", groups[0], groups[1]
                else:
                    continue

            elif pattern_type in ["search", "search_query", "search_pins"]:
                content_type = "search"
                if "q" in query_params:
                    q = query_params["q"][0]
                    additional_info["query"] = q.strip()
                elif pattern_type == "search_query" and groups:
                    additional_info["query"] = groups[0]


            elif pattern_type.startswith("ideas"):
                content_type, content_id = "ideas", groups[0]

            elif pattern_type.startswith("business"):
                content_type = "business"
                if groups:
                    content_id = groups[0]

            elif pattern_type.startswith("analytics"):
                content_type = "analytics"

            elif pattern_type.startswith("ads"):
                content_type = "ads"
                if len(groups) > 0:
                    content_id = groups[0]

            elif pattern_type.startswith("shop"):
                content_type = "shop"
                if len(groups) > 0:
                    content_id = groups[0]

            elif pattern_type == "category":
                content_type, content_id = "category", groups[0]

            elif pattern_type == "following":
                content_type = "following"

            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, username, additional_info

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '📌')
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        additional_info = data.get('additional_info', {})

        type_names = {
            "pin": "Pin", "board": "Tablero",
            "profile": "Perfil", "ideas": "Ideas",
            "search": "Búsqueda", "create_pin": "Crear Pin",
            "business": "Negocios", "analytics": "Analytics",
            "ads": "Anuncios", "shop": "Tienda", "home": "Inicio",
            "following": "Siguiendo", "category": "Categoría",
            "profile_pins": "Pins", "profile_boards": "Tableros",
            "profile_tries": "Probados", "profile_likes": "Me gusta",
            "profile_followers": "Seguidores", "profile_following": "Siguiendo"
        }

        type_display = type_names.get(content_type, "Contenido")

        if content_type == "search" and "query" in additional_info:
            query = additional_info["query"]
            return f"[{emoji} {type_display} de {self.SITE_NAME}: {query}]"

        parts = [f"{emoji} {type_display} de {self.SITE_NAME}"]

        if username:
            if content_type.startswith("profile_"):
                parts.append(f"de @{username} - {type_names[content_type]}")
            else:
                parts.append(f"de @{username}")

        if content_id and not content_type.startswith("profile_"):
            if content_type == "pin":
                short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
                parts.append(f"- ID: {short_id}")
            else:
                parts.append(f"- {content_id}")

        return f"[{' '.join(parts)}]"
