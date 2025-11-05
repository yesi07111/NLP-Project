# extractors/twitter.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class TwitterExtractor(BaseExtractor):
    DOMAINS = ['twitter.com', 'x.com', 't.co', 'www.twitter.com', 'www.x.com']
    SITE_NAME = 'Twitter/X'

    PATTERNS = [
        ("tweet_photo", r'^/?([^/]+)/status/(\d+)/photo/(\d+)/?$'),
        ("tweet_video", r'^/?([^/]+)/status/(\d+)/video/(\d+)/?$'),
        ("tweet_retweets", r'^/?([^/]+)/status/(\d+)/retweets/?$'),
        ("tweet_likes", r'^/?([^/]+)/status/(\d+)/likes/?$'),
        ("tweet", r'^/?([^/]+)/status/(\d+)/?$'),
        ("profile_with_replies", r'^/?([^/]+)/with_replies/?$'),
        ("profile_media", r'^/?([^/]+)/media/?$'),
        ("profile_likes", r'^/?([^/]+)/likes/?$'),
        ("profile_following", r'^/?([^/]+)/following/?$'),
        ("profile_followers", r'^/?([^/]+)/followers/?$'),
        ("list_specific", r'^/?([^/]+)/lists/([^/]+)/?$'),
        ("list_general", r'^/?([^/]+)/lists/?$'),
        ("community_specific", r'^/?i/communities/(\d+)/?$'),
        ("moment_specific", r'^/?i/moments/(\d+)/?$'),
        ("event_specific", r'^/?i/events/(\d+)/?$'),
        ("space_specific", r'^/?i/spaces/(\d+)/?$'),
        ("conversation_specific", r'^/?messages/(\d+)/?$'),
        ("search_query", r'^/?i/search/?$'),
        ("explore_topic", r'^/?explore/tabs/([^/]+)/?$'),
        ("hashtag", r'^/?hashtag/([^/]+)/?$'),
        ("settings_account", r'^/?settings/account/?$'),
        ("settings_privacy", r'^/?settings/privacy/?$'),
        ("settings_display", r'^/?settings/display/?$'),
        ("flow_login", r'^/?i/flow/login/?$'),
        ("flow_signup", r'^/?i/flow/signup/?$'),
        ("compose_tweet", r'^/?compose/tweet/?$'),
        ("bookmarks", r'^/?i/bookmarks/?$'),
        ("trends", r'^/?i/trends/?$'),
        ("communities", r'^/?i/communities/?$'),
        ("moments", r'^/?i/moments/?$'),
        ("grok", r'^/?i/grok/?$'),
        ("premium", r'^/?i/premium/?$'),
        ("search", r'^/?search/?$'),
        ("explore", r'^/?explore/?$'),
        ("messages", r'^/?messages/?$'),
        ("notifications", r'^/?notifications/?$'),
        ("settings", r'^/?settings/?$'),
        ("about", r'^/?about/?$'),
        ("tos", r'^/?tos/?$'),
        ("privacy", r'^/?privacy/?$'),
        ("help", r'^/?help/?$'),
        ("logout", r'^/?logout/?$'),
        ("profile", r'^/?([^/]+)/?$'),
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        username, content_id, content_type = self._extract_twitter_info(parsed_url)
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS.get('twitter', {}).get(content_type, '🐦'),
            'username': username,
            'content_id': content_id,
            'content_type': content_type
        }

    def _extract_twitter_info(self, parsed_url) -> Tuple[str, str, str]:
        path = parsed_url.path or ""
        query_params = parse_qs(parsed_url.query or "")
        clean_path = path.rstrip('/')
        username = ""
        content_id = ""
        content_type = "home"

        # Short links t.co
        if "t.co" in (parsed_url.netloc or ""):
            return "", "", "short_link"

        for pattern_type, pattern in self.PATTERNS:
            try:
                match = re.match(pattern, clean_path)
            except re.error:
                match = None

            if not match:
                continue

            groups = match.groups()

            # tweet variants
            if pattern_type in ["tweet_photo", "tweet_video", "tweet_retweets", "tweet_likes"]:
                username, content_id = groups[0], groups[1]
                content_type = pattern_type.replace("tweet_", "")
            elif pattern_type == "tweet":
                username, content_id = groups[0], groups[1]
                content_type = "tweet"

            # profile sections
            elif pattern_type.startswith("profile_"):
                username = groups[0] if groups else ""
                content_type = pattern_type

            # lists
            elif pattern_type.startswith("list_"):
                username = groups[0] if groups else ""
                if pattern_type == "list_specific" and len(groups) > 1:
                    content_id = groups[1]
                    content_type = "list"
                else:
                    content_type = "list"

            elif pattern_type == "community_specific":
                content_id = groups[0] if groups else ""
                content_type = "communities"

            elif pattern_type == "moment_specific":
                content_id = groups[0] if groups else ""
                content_type = "moments"

            elif pattern_type in ["event_specific", "space_specific"]:
                content_id = groups[0] if groups else ""
                content_type = pattern_type.replace("_specific", "")

            elif pattern_type == "conversation_specific":
                content_id = groups[0] if groups else ""
                content_type = "messages"

            elif pattern_type in ["search_query", "explore_topic"]:
                if pattern_type == "explore_topic" and groups:
                    content_id = groups[0]
                content_type = "search" if pattern_type == "search_query" else "explore"

            elif pattern_type == "hashtag":
                content_id = groups[0] if groups else ""
                content_type = "hashtag"

            elif pattern_type.startswith("settings_"):
                content_type = pattern_type

            elif pattern_type.startswith("flow_"):
                content_type = pattern_type.replace("flow_", "")

            elif pattern_type in ["compose_tweet", "bookmarks", "trends", "communities",
                                  "moments", "grok", "premium", "search", "explore",
                                  "messages", "notifications", "settings", "about",
                                  "tos", "privacy", "help", "logout"]:
                content_type = pattern_type

            elif pattern_type == "profile":
                username = groups[0] if groups else ""
                content_type = "profile"

            elif pattern_type == "home":
                content_type = "home"

            # first matching pattern wins
            break

        # handle query params for searches/hashtags
        if content_type == "search" and "q" in query_params:
            content_id = query_params["q"][0]
        elif content_type == "hashtag" and "q" in query_params:
            content_id = query_params["q"][0]

        return username, content_id, content_type

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '🐦')
        username = data.get('username', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')

        type_names = {
            "tweet": "Tweet", "photo": "Tweet con foto", "video": "Tweet con video",
            "retweets": "Retweets", "likes": "Likes", "profile": "Perfil",
            "profile_with_replies": "Perfil con respuestas", "profile_media": "Perfil con medios",
            "profile_likes": "Perfil con likes", "profile_following": "Siguiendo",
            "profile_followers": "Seguidores", "list": "Lista", "search": "Búsqueda",
            "explore": "Explorar", "messages": "Mensajes", "notifications": "Notificaciones",
            "communities": "Comunidades", "moments": "Moments", "short_link": "Enlace corto",
            "bookmarks": "Marcadores", "trends": "Tendencias", "grok": "Grok",
            "premium": "Premium", "compose_tweet": "Componer tweet", "login": "Inicio de sesión",
            "signup": "Registro", "settings": "Configuración", "settings_account": "Configuración de cuenta",
            "settings_privacy": "Configuración de privacidad", "settings_display": "Configuración de pantalla",
            "about": "Acerca de", "tos": "Términos de servicio", "privacy": "Privacidad",
            "help": "Ayuda", "logout": "Cerrar sesión", "home": "Inicio", "hashtag": "Hashtag",
            "event": "Evento", "space": "Space"
        }

        type_display = type_names.get(content_type, "Contenido")

        if content_type == "search" and content_id:
            search_term = content_id
            short_term = search_term[:20] + "..." if len(search_term) > 20 else search_term
            return f"[{emoji} {type_display} de {self.SITE_NAME}: {short_term}]"

        parts = []
        if username:
            parts.append(f"de @{username}")

        if content_id:
            if content_type == "hashtag":
                parts.append(f"#{content_id}")
            elif content_type in ["tweet", "photo", "video", "retweets", "likes", "list",
                                  "communities", "moments", "messages", "event", "space"]:
                parts.append(f"- ID: {content_id}")
            elif content_type == "explore":
                parts.append(f"- ID: {content_id}")

        parts_display = " " + " ".join(parts) if parts else ""
        return f"[{emoji} {type_display} de {self.SITE_NAME}{parts_display}]"
