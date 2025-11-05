# extractors/telegram.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class TelegramExtractor(BaseExtractor):
    DOMAINS = ['telegram.me', 't.me', 'telegram.dog', 'telesco.pe']
    SITE_NAME = 'Telegram'

    PATTERNS = [
        ("invite_joinchat", r'^/joinchat/([a-zA-Z0-9_-]+)$'),
        ("invite_plus", r'^/\+([a-zA-Z0-9_-]+)$'),
        ("specific_message", r'^/s/([a-zA-Z0-9_@+-]+)/(\d+)$'),
        ("channel_message_numeric", r'^/c/(\d+)/(\d+)$'),
        ("stickers", r'^/addstickers/([a-zA-Z0-9_-]+)$'),
        ("theme", r'^/addtheme/([a-zA-Z0-9_-]+)$'),
        ("emoji", r'^/addemoji/([a-zA-Z0-9_-]+)$'),
        ("login", r'^/login/([a-zA-Z0-9_-]+)$'),
        ("share_url", r'^/share/url$'),
        ("proxy", r'^/proxy/?$'),
        ("share", r'^/share/?$'),
        ("donate", r'^/donate/?$'),
        ("contact", r'^/contact/?$'),
        ("phone", r'^/phone/?$'),
        ("videochat", r'^/videochat/?$'),
        ("livestream", r'^/livestream/?$'),
        ("voicechat", r'^/voicechat/?$'),
        ("boost", r'^/boost/?$'),
        ("statistics", r'^/statistics/?$'),
        ("administrators", r'^/administrators/?$'),
        ("discussion", r'^/discussion/?$'),
        ("public_channel_message", r'^/([a-zA-Z0-9_@+-]+)/(\d+)$'),
        ("public_channel", r'^/([a-zA-Z0-9_@+-]+)$'),
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, username, message_id, additional_info = self._extract_telegram_info(parsed_url)
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['telegram'].get(content_type, '💬'),
            'content_id': content_id,
            'username': username,
            'message_id': message_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_telegram_info(self, parsed_url) -> Tuple[str, str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "home"
        content_id = ""
        username = ""
        message_id = ""
        additional_info = {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "invite_joinchat":
                content_type, content_id = "invite", groups[0]
            elif pattern_type == "invite_plus":
                content_type, content_id = "invite", groups[0]
            elif pattern_type == "specific_message":
                content_type, username, message_id = "message", groups[0], groups[1]
            elif pattern_type == "channel_message_numeric":
                content_type, content_id, message_id = "channel_message", groups[0], groups[1]
            elif pattern_type in ["stickers", "theme", "emoji"]:
                content_type, content_id = pattern_type, groups[0]
            elif pattern_type == "login":
                content_type, content_id = "login", groups[0]
            elif pattern_type == "share_url":
                content_type = "share"
                if "url" in query_params:
                    content_id = query_params["url"][0]
            elif pattern_type in ["proxy", "share", "donate", "contact", "phone", 
                                "videochat", "livestream", "voicechat", "boost", 
                                "statistics", "administrators", "discussion"]:
                content_type = pattern_type
                if pattern_type == "proxy" and "server" in query_params:
                    content_id = query_params["server"][0]
                elif pattern_type == "share" and "url" in query_params:
                    content_id = query_params["url"][0]
                elif pattern_type == "phone" and "phone" in query_params:
                    content_id = query_params["phone"][0]
            elif pattern_type == "public_channel_message":
                content_type, username, message_id = "channel_message", groups[0], groups[1]
            elif pattern_type == "public_channel":
                content_type, username = "channel", groups[0]
                if "start" in query_params:
                    content_type = "bot_start"
                    content_id = query_params["start"][0]
                elif "game" in query_params:
                    content_type = "bot_game" 
                    content_id = query_params["game"][0]
            elif pattern_type == "home":
                content_type = "home"

            if username and username.startswith('@'):
                username = username[1:]
            break

        # Manejar parámetros que cambian el tipo después del patrón base
        if query_params:
            if content_type == "channel" and "videochat" in query_params:
                content_type = "videochat"
            elif content_type == "channel" and "contact" in query_params:
                content_type = "contact"

        return content_type, content_id, username, message_id, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '💬')
        content_id = data.get('content_id', '')
        username = data.get('username', '')
        message_id = data.get('message_id', '')
        content_type = data.get('content_type', '')
        
        type_names = {
            "invite": "Invitación", "channel": "Canal", 
            "message": "Mensaje", "channel_message": "Mensaje en canal",
            "bot_start": "Bot - Inicio", "bot_game": "Bot - Juego",
            "stickers": "Stickers", "theme": "Tema", "emoji": "Emoji",
            "login": "Login", "proxy": "Proxy", "share": "Compartir",
            "donate": "Donación", "contact": "Contacto", "phone": "Teléfono",
            "videochat": "Videochat", "livestream": "Transmisión en vivo",
            "voicechat": "Chat de voz", "boost": "Boost", 
            "statistics": "Estadísticas", "administrators": "Administradores",
            "discussion": "Discusión", "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        parts = []
        if username:
            parts.append(f"de @{username}")
        if content_id and content_type == "channel_message":
            parts.append(f"ID: {content_id}")
        elif content_id and content_type not in ["channel", "message"]:
            parts.append(f"ID: {content_id}")
        if message_id:
            parts.append(f"Mensaje: {message_id}")
        
        parts_display = " - " + ", ".join(parts) if parts else ""
        return f"[{emoji} {type_display} de {self.SITE_NAME}{parts_display}]"