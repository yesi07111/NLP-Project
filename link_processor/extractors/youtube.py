# extractors/youtube.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class YouTubeExtractor(BaseExtractor):
    DOMAINS = ['youtube.com', 'youtu.be', 'music.youtube.com', 'youtubekids.com', 'studio.youtube.com', 'www.youtube.com']
    SITE_NAME = 'YouTube'

    # Patrones regex para YouTube - ORDENADOS de más específico a más general
    PATTERNS = [
        # Shorts (muy específico)
        ("shorts", r'^/shorts/([a-zA-Z0-9_-]+)$'),
        
        # Live (específico)
        ("live", r'^/live/([a-zA-Z0-9_-]+)$'),
        
        # Embed (específico)
        ("embed", r'^/embed/([a-zA-Z0-9_-]+)$'),
        
        # V con parámetros (específico)
        ("v_parameter", r'^/v/([a-zA-Z0-9_-]+)$'),
        
        # Canales con @ (específico)
        ("channel_handle", r'^/@([a-zA-Z0-9_.-]+)/?$'),
        ("channel_handle_section", r'^/@([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_-]+)/?$'),
        
        # Canales por nombre (específico)
        ("channel_c", r'^/c/([a-zA-Z0-9_-]+)/?$'),
        ("channel_c_section", r'^/c/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/?$'),
        
        # Canales por ID (específico)
        ("channel_id", r'^/channel/([a-zA-Z0-9_-]+)/?$'),
        ("channel_id_section", r'^/channel/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/?$'),
        
        # Canales por usuario (específico)
        ("channel_user", r'^/user/([a-zA-Z0-9_-]+)/?$'),
        ("channel_user_section", r'^/user/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/?$'),
        
        # Secciones específicas
        ("feed_section", r'^/feed/([a-zA-Z0-9_-]+)/?$'),
        ("hashtag", r'^/hashtag/([a-zA-Z0-9_-]+)/?$'),
        
        # Playlist (ruta específica)
        ("playlist", r'^/playlist/?$'),
        
        # Watch (ruta específica)
        ("watch", r'^/watch/?$'),
        
        # Páginas específicas
        ("gaming", r'^/gaming/?$'),
        ("movies", r'^/movies/?$'),
        ("tv", r'^/tv/?$'),
        ("creators", r'^/creators/?$'),
        ("ads", r'^/ads/?$'),
        ("account", r'^/account/?$'),
        ("premium", r'^/premium/?$'),
        ("originals", r'^/originals/?$'),
        ("kids", r'^/kids/?$'),
        ("education", r'^/education/?$'),
        ("new", r'^/new/?$'),
        ("upload", r'^/upload/?$'),
        ("live_dashboard", r'^/live_dashboard/?$'),
        ("analytics", r'^/analytics/?$'),
        ("comment", r'^/comment/?$'),
        ("subscribe", r'^/subscribe/?$'),
        ("share", r'^/share/?$'),
        ("redirect", r'^/redirect/?$'),
        
        # Búsqueda
        ("results", r'^/results/?$'),
        
        # YouTu.be (dominio específico)
        ("youtu_be", r'^/([a-zA-Z0-9_-]+)$'),
        
        # Página principal de canal
        ("channel_home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, additional_info = self._extract_youtube_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['youtube'].get(content_type, '🎥'),
            'content_id': content_id,
            'additional_info': additional_info,
            'content_type': content_type,
        }

    def _extract_youtube_info(self, parsed_url) -> Tuple[str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "video"
        content_id = ""
        additional_info = {}

        # Detectar subdominios especiales
        if 'music.youtube.com' in parsed_url.netloc:
            additional_info['subdomain'] = 'music'
        elif 'youtubekids.com' in parsed_url.netloc:
            additional_info['subdomain'] = 'kids'
        elif 'studio.youtube.com' in parsed_url.netloc:
            additional_info['subdomain'] = 'studio'
            # Para YouTube Studio, no capturamos IDs de canal
            content_type = "studio"
            return content_type, content_id, additional_info

        # Si el dominio es youtu.be, manejamos de manera especial
        if 'youtu.be' in parsed_url.netloc:
            match = re.match(r'^/([a-zA-Z0-9_-]+)$', clean_path)
            if match:
                content_type = "video"
                content_id = match.group(1)
                # Verificar si hay parámetros de tiempo
                if 't' in query_params:
                    additional_info['timestamp'] = query_params['t'][0]
                return content_type, content_id, additional_info

        # Para los demás dominios, aplicamos los patrones
        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "shorts":
                content_type, content_id = "short", groups[0]
            elif pattern_type == "live":
                content_type, content_id = "live", groups[0]
            elif pattern_type == "embed":
                content_type, content_id = "embedded", groups[0]
                # Verificar parámetros de tiempo para embed
                if "start" in query_params:
                    additional_info["timestamp"] = query_params["start"][0]
                elif "t" in query_params:
                    additional_info["timestamp"] = query_params["t"][0]
            elif pattern_type == "v_parameter":
                content_type, content_id = "video", groups[0]
            elif pattern_type == "channel_handle":
                content_type = "channel"
                additional_info["channel_handle"] = groups[0]
            elif pattern_type == "channel_handle_section":
                content_type = "channel"
                additional_info["channel_handle"] = groups[0]
                additional_info["section"] = groups[1]
            elif pattern_type == "channel_c":
                content_type = "channel"
                additional_info["channel_name"] = groups[0]
            elif pattern_type == "channel_c_section":
                content_type = "channel"
                additional_info["channel_name"] = groups[0]
                additional_info["section"] = groups[1]
            elif pattern_type == "channel_id":
                content_type = "channel"
                additional_info["channel_id"] = groups[0]
            elif pattern_type == "channel_id_section":
                content_type = "channel"
                additional_info["channel_id"] = groups[0]
                additional_info["section"] = groups[1]
            elif pattern_type == "channel_user":
                content_type = "channel"
                additional_info["channel_name"] = groups[0]
            elif pattern_type == "channel_user_section":
                content_type = "channel"
                additional_info["channel_name"] = groups[0]
                additional_info["section"] = groups[1]
            elif pattern_type == "feed_section":
                content_type = "feed"
                additional_info["feed_type"] = groups[0]
            elif pattern_type == "hashtag":
                content_type = "hashtag"
                content_id = groups[0]
            elif pattern_type == "playlist":
                content_type = "playlist"
                if "list" in query_params:
                    content_id = query_params["list"][0]
            elif pattern_type == "watch":
                if "v" in query_params:
                    content_type, content_id = "video", query_params["v"][0]
                if "list" in query_params:
                    additional_info["playlist"] = query_params["list"][0]
                # Verificar parámetros de tiempo
                if "t" in query_params:
                    additional_info["timestamp"] = query_params["t"][0]
                elif "start" in query_params:
                    additional_info["timestamp"] = query_params["start"][0]
            elif pattern_type in ["gaming", "movies", "tv", "creators", "ads", "account", 
                                "premium", "originals", "kids", "education", "new", "upload",
                                "live_dashboard", "analytics", "comment", "subscribe", "share", "redirect"]:
                content_type = pattern_type
            elif pattern_type == "results":
                content_type = "search"
                if "search_query" in query_params:
                    additional_info["query"] = query_params["search_query"][0]
            elif pattern_type == "youtu_be":
                content_type, content_id = "video", groups[0]
            elif pattern_type == "channel_home":
                content_type = "channel_home"

            break

        # Aplicar subdominios al tipo de contenido
        if additional_info.get('subdomain') == 'music':
            if content_type in ["video", "short", "live", "embedded", "playlist"]:
                content_type = f"music_{content_type}"
            elif content_type == "channel_home":
                content_type = "music"
        elif additional_info.get('subdomain') == 'kids':
            if content_type in ["video", "short", "live", "embedded", "playlist"]:
                content_type = f"kids_{content_type}"
            elif content_type == "channel_home":
                content_type = "kids"

        return content_type, content_id, additional_info

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '🎥')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        info = data.get('additional_info', {})
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "video": "Video", "short": "Short", 
            "live": "Transmisión en vivo", "embedded": "Video incrustado",
            "channel": "Canal", "playlist": "Lista de reproducción",
            "channel_home": "Inicio", "music": "YouTube Music",
            "music_video": "Video en YouTube Music", "music_short": "Short en YouTube Music",
            "music_live": "Transmisión en vivo en YouTube Music", "music_embedded": "Video incrustado en YouTube Music",
            "music_playlist": "Lista en YouTube Music", "kids": "YouTube Kids",
            "kids_video": "Video en YouTube Kids", "kids_short": "Short en YouTube Kids", 
            "kids_live": "Transmisión en vivo en YouTube Kids", "kids_embedded": "Video incrustado en YouTube Kids",
            "kids_playlist": "Lista en YouTube Kids", "studio": "YouTube Studio",
            "feed": "Feed", "hashtag": "Hashtag", "search": "Búsqueda",
            "gaming": "Gaming", "movies": "Películas", "tv": "TV",
            "creators": "Creadores", "ads": "Anuncios", "account": "Cuenta",
            "premium": "Premium", "originals": "Originals", "education": "Educación",
            "new": "Subir video", "upload": "Upload", "live_dashboard": "Dashboard en vivo",
            "analytics": "Analytics", "comment": "Comentarios", "subscribe": "Suscribirse",
            "share": "Compartir", "redirect": "Redirect"
        }

        name = type_names.get(content_type, "Contenido")

        # Construir partes del display
        parts = []
        
        # Para canales, no mostrar content_id ya que se muestra en la información del canal
        if content_id and content_type != "channel" and content_type != "hashtag":
            parts.append(f"ID: {content_id}")
        elif content_type == "hashtag":
            parts.append(f"#{content_id}")
        
        if "channel_name" in info:
            parts.append(f"Canal: {info['channel_name']}")
        elif "channel_handle" in info:
            parts.append(f"Canal: @{info['channel_handle']}")
        elif "channel_id" in info:
            parts.append(f"Canal ID: {info['channel_id']}")
        
        if "playlist" in info:
            parts.append(f"Playlist: {info['playlist']}")
            
        if "section" in info:
            section_names = {
                "videos": "Videos", "playlists": "Playlists", 
                "community": "Comunidad", "about": "Acerca de"
            }
            section_display = section_names.get(info["section"], info["section"])
            parts.append(f"Sección: {section_display}")
            
        if "feed_type" in info:
            feed_names = {
                "subscriptions": "Suscripciones", "trending": "Trending",
                "history": "Historial", "library": "Biblioteca"
            }
            feed_display = feed_names.get(info["feed_type"], info["feed_type"])
            parts.append(f"Feed: {feed_display}")
            
        if "query" in info:
            parts.append(f"Búsqueda: {info['query']}")
            
        if "timestamp" in info:
            parts.append(f"Tiempo: {info['timestamp']}")

        parts_display = " - " + " - ".join(parts) if parts else ""

        return f"[{emoji} {name} de {self.SITE_NAME}{parts_display}]"