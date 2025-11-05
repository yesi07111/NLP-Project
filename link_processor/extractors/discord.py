# extractors/discord.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class DiscordExtractor(BaseExtractor):
    DOMAINS = ['discord.com', 'discord.gg', 'media.discordapp.net', 'cdn.discordapp.com']
    SITE_NAME = 'Discord'
    
    # Patrones regex para diferentes tipos de URLs de Discord - ORDEN CORREGIDO
    # Los patrones más específicos deben ir primero
    PATTERNS = {
        # CDN y Media - DEBEN IR PRIMERO porque son muy específicos
        'media': [
            r'/(attachments/\d+/\d+/[^/?]+)',
            r'/(emojis/\d+\.[a-z]+)',
            r'/(icons/\d+/[^/?]+)',
            r'/([^/?]+)$'  # Cualquier archivo en los dominios de CDN
        ],
        # Canales - específicos con IDs
        'channel': [
            r'/channels/(\d+)/(\d+)',
            r'/channels/(\d+)'
        ],
        # Invitaciones
        'invite': [
            r'/invite/([a-zA-Z0-9-]+)'
        ],
        # Tienda y sus variantes
        'store_skus': [
            r'/store/skus/(\d+)'
        ],
        'store_listings': [
            r'/store/published-listings'
        ],
        'store': [
            r'/store$',
            r'/store/$'
        ],
        # Aplicaciones
        'applications': [
            r'/application-directory/(\d+)',
            r'/application-directory$'
        ],
        # Blog con slugs
        'blog': [
            r'/blog/([a-zA-Z0-9-]+)',
            r'/blog$'
        ],
        # Soporte con categorías
        'support': [
            r'/support/([a-zA-Z0-9-]+)',
            r'/support$'
        ],
        # Actividad con tipos
        'activity': [
            r'/activity/([a-zA-Z0-9-]+)',
            r'/activity$'
        ],
        # Modal con tipos
        'modal': [
            r'/modal/([a-zA-Z0-9-]+)'
        ],
        # OAuth
        'oauth_authorize': [
            r'/oauth2/authorize'
        ],
        # Rutas simples - DEBEN IR AL FINAL
        'nitro': [r'/nitro'],
        'servers': [r'/servers'],
        'library': [r'/library'],
        'download': [r'/download'],
        'terms': [r'/terms'],
        'privacy': [r'/privacy'],
        'guidelines': [r'/guidelines'],
        'status': [r'/status'],
        'hypesquad': [r'/hypesquad'],
        'student_hub': [r'/student-hub']
    }
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, server_id, channel_id = self._extract_discord_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['discord'].get(content_type, '🎮'),
            'server_id': server_id,
            'channel_id': channel_id,
            'content_type': content_type
        }
    
    def _extract_discord_info(self, parsed_url) -> Tuple[str, str, str]:
        """Extrae metadata completa de Discord usando expresiones regulares - VERSIÓN CORREGIDA"""
        domain = parsed_url.netloc.lower()
        path = parsed_url.path
        content_type = ""
        server_id = ""
        channel_id = ""
        
        # Casos especiales por dominio primero - ESTOS DEBEN TENER LA MÁS ALTA PRIORIDAD
        if domain == 'discord.gg':
            content_type = "invite"
            server_id = path.strip('/') if path.strip('/') else ""
            return content_type, server_id, channel_id
        
        # Para CDN y media, usar la ruta completa como server_id - ALTA PRIORIDAD
        if 'media.discordapp.net' in domain or 'cdn.discordapp.com' in domain:
            content_type = "media"
            # Buscar patrones específicos primero
            for pattern in self.PATTERNS['media']:
                match = re.search(pattern, path)
                if match:
                    server_id = match.group(1) if match.groups() else path.strip('/')
                    return content_type, server_id, channel_id
            # Fallback: usar toda la ruta
            server_id = path.strip('/')
            return content_type, server_id, channel_id
        
        # Verificar todos los patrones regex en orden
        for content_type_name, patterns in self.PATTERNS.items():
            # Saltar patrones de media ya que los manejamos arriba
            if content_type_name == 'media':
                continue
                
            for pattern in patterns:
                match = re.search(pattern, path)
                if match:
                    content_type = content_type_name
                    
                    # Extraer server_id y channel_id según el patrón
                    if content_type_name == 'channel':
                        if len(match.groups()) >= 2:
                            server_id = match.group(1)
                            channel_id = match.group(2)
                        elif len(match.groups()) == 1:
                            server_id = match.group(1)
                    elif content_type_name in ['invite', 'store_skus', 'applications', 'blog', 'support', 'modal', 'activity']:
                        if match.groups():
                            server_id = match.group(1)
                    
                    return content_type, server_id, channel_id
        
        return content_type, server_id, channel_id
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para Discord basado en la lógica original"""
        emoji = data.get('emoji', '🎮')
        server_id = data.get('server_id', '')
        channel_id = data.get('channel_id', '')
        content_type = data.get('content_type', '')
        
        server_id_display = f" - Servidor: {server_id}" if server_id else ""
        channel_id_display = f" (Canal: {channel_id})" if channel_id else ""
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "invite": "Invitación", "channel": "Canal", "store": "Tienda",
            "store_skus": "SKUs de tienda", "store_listings": "Listados de tienda",
            "nitro": "Nitro", "servers": "Servidores", "applications": "Aplicaciones",
            "library": "Biblioteca", "download": "Descargar", "blog": "Blog",
            "support": "Soporte", "terms": "Términos", "privacy": "Privacidad",
            "guidelines": "Guías", "status": "Estado", "modal": "Modal",
            "oauth_authorize": "Autorización OAuth", "hypesquad": "Hypesquad",
            "student_hub": "Student Hub", "activity": "Actividad", "media": "Media"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        return f"[{emoji} {type_display} de {self.SITE_NAME}{server_id_display}{channel_id_display}]"