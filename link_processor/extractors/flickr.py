# extractors/flickr.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class FlickrExtractor(BaseExtractor):
    DOMAINS = ['flickr.com', 'flic.kr']
    SITE_NAME = 'Flickr'
    
    # Patrones regex para diferentes tipos de URLs de Flickr - CORREGIDOS
    PATTERNS = {
        # URLs cortas (prioridad máxima)
        'photo_short': [r'^/p/([a-zA-Z0-9]+)$'],
        'set_short': [r'^/ps/([a-zA-Z0-9]+)$'],

        # Fotos individuales
        'photo': [r'^/photos/([^/]+)/(\d+)/?'],

        # Álbumes
        'album': [
            r'^/photos/([^/]+)/albums/([^/?]+)',
            r'^/photos/([^/]+)/albums/?$'
        ],

        # Sets
        'set': [
            r'^/photos/([^/]+)/sets/([^/?]+)',
            r'^/photos/([^/]+)/sets/?$'
        ],

        # Galerías
        'gallery': [
            r'^/photos/([^/]+)/galleries/([^/?]+)',
            r'^/photos/([^/]+)/galleries/?$'
        ],

        # Favoritos
        'favorites': [r'^/photos/([^/]+)/favorites/?$'],

        # Grupos
        'group': [r'^/groups/([^/?]+)'],

        # Perfiles de usuario
        'user': [r'^/people/([^/?]+)/?$'],

        # Stream de fotos de usuario
        'photo_stream': [r'^/photos/([^/?]+)/?$'],

        # Explore y búsquedas
        'explore': [
            r'^/explore',
            r'^/search',
            r'^/creativecommons',
            r'^/explore/interesting'
        ],

        # Mapas
        'map': [r'^/map'],

        # The Commons
        'commons': [r'^/commons']
    }
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, username, photo_id, album_id = self._extract_flickr_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['flickr'].get(content_type, '📷'),
            'username': username,
            'photo_id': photo_id,
            'album_id': album_id,
            'content_type': content_type
        }
    
    def _extract_flickr_info(self, parsed_url) -> Tuple[str, str, str, str]:
        """Extrae metadata completa de Flickr usando expresiones regulares - CORREGIDA"""
        path = parsed_url.path
        content_type = ""
        username = ""
        photo_id = ""
        album_id = ""

        # Verificar todos los patrones regex en orden de especificidad
        for content_type_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, path)
                if not match:
                    continue

                groups = match.groups()

                # Mapeo especial para URLs cortas
                if content_type_name == 'photo_short':
                    content_type = 'photo'
                    photo_id = groups[0]
                elif content_type_name == 'set_short':
                    content_type = 'set'
                    album_id = groups[0]
                elif content_type_name == 'photo':
                    content_type = 'photo'
                    username, photo_id = groups[0], groups[1]
                elif content_type_name in ['album', 'set', 'gallery']:
                    content_type = content_type_name
                    if len(groups) >= 2:
                        username, album_id = groups[0], groups[1]
                    elif len(groups) == 1:
                        # Caso especial: /photos/<nombre>/sets o /albums
                        if content_type_name == 'set':
                            album_id = groups[0]
                        else:
                            username = groups[0]

                elif content_type_name in ['favorites', 'group', 'user', 'photo_stream']:
                    content_type = content_type_name
                    if groups:
                        username = groups[0]
                elif content_type_name in ['explore', 'map', 'commons']:
                    content_type = content_type_name

                return content_type, username, photo_id, album_id

        return content_type, username, photo_id, album_id

    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para Flickr basado en la lógica original - VERSIÓN CORREGIDA"""
        emoji = data.get('emoji', '📷')
        username = data.get('username', '')
        photo_id = data.get('photo_id', '')
        album_id = data.get('album_id', '')
        content_type = data.get('content_type', '')
        
        # Lógica corregida para mostrar los IDs correctamente
        if content_type in ['group', 'user']:
            # Para grupos y usuarios, mostrar " - ID: username"
            username_display = f" - ID: {username}" if username else ""
            photo_id_display = ""
            album_id_display = ""
        elif content_type == 'photo_stream':
            # Para stream de fotos, mostrar "de username" sin ID
            username_display = f" de {username}" if username else ""
            photo_id_display = ""
            album_id_display = ""
        elif content_type == 'photo':
            # Para fotos, mostrar "de username - ID: photo_id" o solo " - ID: photo_id" para URLs cortas
            if username:
                username_display = f" de {username}"
                photo_id_display = f" - ID: {photo_id}" if photo_id else ""
            else:
                # URL corta: no tiene username
                username_display = ""
                photo_id_display = f" - ID: {photo_id}" if photo_id else ""
            album_id_display = ""
        elif content_type in ['album', 'set', 'gallery']:
            # Para álbumes, sets y galerías, mostrar "de username - ID: album_id" o solo "de username" si no hay album_id
            username_display = f" de {username}" if username else ""
            if album_id:
                album_id_display = f" - ID: {album_id}"
            else:
                album_id_display = ""
            photo_id_display = ""
        else:
            # Para otros tipos, mostrar username normal
            username_display = f" de {username}" if username else ""
            photo_id_display = f" - ID: {photo_id}" if photo_id else ""
            album_id_display = f" - ID: {album_id}" if album_id else ""
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "photo": "Foto", "album": "Álbum", 
            "user": "Usuario", "group": "Grupo",
            "set": "Set", "gallery": "Galería",
            "favorites": "Favoritos", "explore": "Explorar",
            "map": "Mapa", "commons": "Commons",
            "photo_stream": "Foto"  # Stream de fotos también se muestra como "Foto"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        return f"[{emoji} {type_display} de {self.SITE_NAME}{username_display}{photo_id_display}{album_id_display}]"