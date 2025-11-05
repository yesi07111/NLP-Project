# extractors/google.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class GoogleExtractor(BaseExtractor):
    DOMAINS = [
        'google.com', 'google.es', 'google.com.mx', 'google.co.uk',
        'google.de', 'google.fr', 'google.it', 'google.com.br',
        'google.ca', 'google.com.au', 'google.co.jp', 'google.ru',
        'google.cn', 'google.in', 'google.com.ar', 'google.cl',
        'google.com.co', 'google.com.pe', 'google.com.ve',
        'gmail.com', 'drive.google.com', 'docs.google.com',
        'sheets.google.com', 'slides.google.com', 'forms.google.com',
        'calendar.google.com', 'photos.google.com', 'maps.google.com',
        'mail.google.com', 'meet.google.com', 'classroom.google.com',
        'sites.google.com', 'keep.google.com', 'earth.google.com',
        'scholar.google.com', 'books.google.com', 'patents.google.com',
        'news.google.com', 'play.google.com', 'podcasts.google.com',
        'artsandculture.google.com', 'lens.google.com', 'assistant.google.com',
        'myaccount.google.com', 'takeout.google.com', 'one.google.com',
        'fi.google.com', 'voice.google.com', 'duo.google.com',
        'goo.gl', 'g.co'
    ]
    SITE_NAME = 'Google'

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        host = parsed_url.netloc.lower()
        fragment = parsed_url.fragment
        
        # Determinar el servicio principal
        service = "search"
        content_type = "search"
        content_id = ""
        query = query_params.get('q', [''])[0]
        
        # Mapeo de servicios por host - MEJORADO para manejar subdominios
        service_map = {
            'drive.google.com': 'drive',
            'docs.google.com': 'docs', 
            'mail.google.com': 'gmail',
            'gmail.com': 'gmail',
            'maps.google.com': 'maps',
            'google.com/maps': 'maps',  # Para URLs como google.com/maps/...
            'photos.google.com': 'photos',
            'calendar.google.com': 'calendar',
            'meet.google.com': 'meet',
            'classroom.google.com': 'classroom',
            'sites.google.com': 'sites',
            'keep.google.com': 'keep',
            'scholar.google.com': 'scholar',
            'play.google.com': 'play',
            'news.google.com': 'news',
            'myaccount.google.com': 'myaccount',
            'translate.google.com': 'translate',
            'earth.google.com': 'earth',
            'takeout.google.com': 'takeout',
            'contacts.google.com': 'contacts',
            'goo.gl': 'short_url',
            'g.co': 'short_url'
        }
        
        # Determinar servicio - MEJORADO para manejar rutas específicas
        for key, value in service_map.items():
            if key in host or (key.startswith('google.com/') and key.replace('google.com/', '') in path):
                service = value
                break
        
        # Corrección especial para Maps en google.com
        if service == "search" and ('/maps' in path or 'maps.google.com' in host):
            service = "maps"
        
        # Procesar según el servicio
        if service == "drive":
            content_type, content_id = self._process_drive(path, query_params)
        elif service == "docs":
            content_type, content_id = self._process_docs(path)
        elif service == "gmail":
            content_type, content_id = self._process_gmail(path, fragment)
        elif service == "maps":
            content_type, content_id = self._process_maps(path, query_params, host)
        elif service == "photos":
            content_type, content_id = self._process_photos(path)
        elif service == "calendar":
            content_type, content_id = self._process_calendar(path, query_params)
        elif service == "meet":
            content_type, content_id = self._process_meet(path)
        elif service == "classroom":
            content_type, content_id = self._process_classroom(path)
        elif service == "sites":
            content_type, content_id = self._process_sites(path)
        elif service == "keep":
            content_type = "keep"
        elif service == "scholar":
            content_type, content_id = self._process_scholar(query_params)
        elif service == "play":
            content_type, content_id = self._process_play(path, query_params)
        elif service == "news":
            content_type, content_id = self._process_news(path)
        elif service == "myaccount":
            content_type, content_id = self._process_myaccount(path)
        elif service == "translate":
            content_type = "translate"
        elif service == "earth":
            content_type = "earth"
        elif service == "takeout":
            content_type = "takeout"
        elif service == "contacts":
            content_type = "contacts"
        elif service == "short_url":
            content_type = "short_url"
            content_id = path.strip('/')
        elif service == "search":
            content_type = self._process_search(query_params)
        
        # Obtener emoji - CORREGIDO para usar content_type correcto
        emoji = EMOJI_MAPS['google'].get(content_type, '🔍')
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': emoji,
            'service': service,
            'content_type': content_type,
            'content_id': content_id,
            'query': query
        }
    
    def _process_drive(self, path: str, query_params: dict) -> Tuple[str, str]:
        """Procesa URLs de Google Drive"""
        # drive.google.com/drive/folders/1ABC123def456
        if '/drive/folders/' in path:
            folder_id = path.split('/drive/folders/')[1].split('/')[0]
            return "drive_folder", folder_id
        
        # drive.google.com/drive/u/0/folders/1DEF456ghi789
        if '/drive/u/' in path and '/folders/' in path:
            parts = path.split('/folders/')
            if len(parts) > 1:
                folder_id = parts[1].split('/')[0]
                return "drive_folder", folder_id
        
        # drive.google.com/file/d/1XYZ789abc012/view
        if '/file/d/' in path:
            file_id = path.split('/file/d/')[1].split('/')[0]
            return "drive_file", file_id
        
        # drive.google.com/open?id=1GHI789jkl012
        if path == '/open' and 'id' in query_params:
            return "drive_file", query_params['id'][0]
        
        # Rutas específicas de Drive
        if path == '/drive/mobile':
            return "drive_mobile", ""
        elif path == '/drive/search':
            return "drive_search", ""
        elif path == '/drive/recent':
            return "drive_recent", ""
        elif path == '/drive/shared-with-me':
            return "drive_shared", ""
        elif path == '/drive/trash':
            return "drive_trash", ""
        
        return "drive", ""
    
    def _process_docs(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google Docs"""
        # docs.google.com/document/d/1DOC123edit/view
        if '/document/d/' in path:
            doc_id = path.split('/document/d/')[1].split('/')[0]
            return "docs_document", doc_id
        
        # docs.google.com/spreadsheets/d/1SHEET456/edit
        if '/spreadsheets/d/' in path:
            sheet_id = path.split('/spreadsheets/d/')[1].split('/')[0]
            return "docs_spreadsheet", sheet_id
        
        # docs.google.com/presentation/d/1SLIDE789/edit
        if '/presentation/d/' in path:
            pres_id = path.split('/presentation/d/')[1].split('/')[0]
            return "docs_presentation", pres_id
        
        # docs.google.com/forms/d/1FORM012/edit
        if '/forms/d/' in path:
            form_id = path.split('/forms/d/')[1].split('/')[0]
            return "docs_form", form_id
        
        # docs.google.com/drawings/d/1DRAW345/edit
        if '/drawings/d/' in path:
            drawing_id = path.split('/drawings/d/')[1].split('/')[0]
            return "docs_drawing", drawing_id
        
        return "docs", ""
    
    def _process_gmail(self, path: str, fragment: str) -> Tuple[str, str]:
        """Procesa URLs de Gmail"""
        if fragment:
            if fragment == 'inbox' or fragment.startswith('inbox/'):
                return "gmail_inbox", ""
            elif fragment == 'compose':
                return "gmail_compose", ""
            elif fragment == 'sent':
                return "gmail_sent", ""
            elif fragment == 'drafts':
                return "gmail_drafts", ""
            elif fragment == 'starred':
                return "gmail_starred", ""
            elif fragment == 'spam':
                return "gmail_spam", ""
            elif fragment == 'trash':
                return "gmail_trash", ""
            elif fragment.startswith('label/'):
                label = fragment.split('label/')[1]
                return "gmail_label", label
        
        return "gmail", ""
    
    def _process_maps(self, path: str, query_params: dict, host: str) -> Tuple[str, str]:
        """Procesa URLs de Google Maps - MEJORADO"""
        # maps.google.com/maps?q=New+York
        if 'q' in query_params:
            return "maps_search", query_params['q'][0]
        
        # google.com/maps/place/Eiffel+Tower
        if '/place/' in path:
            place = path.split('/place/')[1].split('/')[0]
            return "maps_place", place
        
        # maps.google.com/maps/dir/Paris/London
        if '/dir/' in path:
            # Capturar toda la ruta de direcciones
            route_match = re.search(r'/dir/(.+)$', path)
            if route_match:
                route = route_match.group(1)
                return "maps_directions", route
        
        # google.com/maps/search/restaurants+near+me
        if '/search/' in path:
            search_match = re.search(r'/search/(.+)$', path)
            if search_match:
                search = search_match.group(1)
                return "maps_search", search
        
        # Rutas específicas de Maps
        if path == '/maps/contributions' or path.endswith('/contributions'):
            return "maps_contributions", ""
        elif path == '/maps/reviews' or path.endswith('/reviews'):
            return "maps_reviews", ""
        
        return "maps", ""
    
    def _process_photos(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google Photos"""
        # photos.google.com/photo/1PHOTO123
        if '/photo/' in path:
            photo_id = path.split('/photo/')[1].split('/')[0]
            return "photos_photo", photo_id
        
        # photos.google.com/album/1ALBUM456
        if '/album/' in path:
            album_id = path.split('/album/')[1].split('/')[0]
            return "photos_album", album_id
        
        # photos.google.com/search/dogs
        if '/search/' in path:
            search = path.split('/search/')[1].split('/')[0]
            return "photos_search", search
        
        # Rutas específicas de Photos
        if path == '/memories':
            return "photos_memories", ""
        elif path == '/archive':
            return "photos_archive", ""
        
        return "photos", ""
    
    def _process_calendar(self, path: str, query_params: dict) -> Tuple[str, str]:
        """Procesa URLs de Google Calendar"""
        # calendar.google.com/calendar/r/eventedit?text=Meeting
        if '/r/eventedit' in path:
            return "calendar_event", ""
        
        return "calendar", ""
    
    def _process_meet(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google Meet"""
        # meet.google.com/abc-defg-hij
        if path != '/' and path != '/new':
            meeting_id = path.strip('/')
            return "meet_room", meeting_id
        
        # meet.google.com/new
        if path == '/new':
            return "meet_new", ""
        
        return "meet", ""
    
    def _process_classroom(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google Classroom"""
        # classroom.google.com/c/1COURSE123
        if '/c/' in path:
            course_id = path.split('/c/')[1].split('/')[0]
            return "classroom_course", course_id
        
        return "classroom", ""
    
    def _process_sites(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google Sites"""
        # sites.google.com/view/mysite
        if '/view/' in path:
            site_id = path.split('/view/')[1].split('/')[0]
            return "sites_site", site_id
        
        # sites.google.com/site/oldsite
        if '/site/' in path:
            site_id = path.split('/site/')[1].split('/')[0]
            return "sites_old", site_id
        
        return "sites", ""
    
    def _process_scholar(self, query_params: dict) -> Tuple[str, str]:
        """Procesa URLs de Google Scholar"""
        # scholar.google.com/scholar?q=AI
        if 'q' in query_params:
            return "scholar_search", query_params['q'][0]
        
        # scholar.google.com/citations?user=USER123
        if 'user' in query_params:
            return "scholar_profile", query_params['user'][0]
        
        return "scholar", ""
    
    def _process_play(self, path: str, query_params: dict) -> Tuple[str, str]:
        """Procesa URLs de Google Play - CORREGIDO para distinguir apps y libros"""
        # play.google.com/store/apps/details?id=com.whatsapp
        if '/apps/' in path and 'id' in query_params:
            app_id = query_params['id'][0]
            return "play_app", app_id
        
        # play.google.com/store/books/details?id=BOOK123
        if '/books/' in path and 'id' in query_params:
            book_id = query_params['id'][0]
            return "play_book", book_id
        
        return "play", ""
    
    def _process_news(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de Google News"""
        # news.google.com/topstories
        if path == '/topstories':
            return "news_top", ""
        
        return "news", ""
    
    def _process_myaccount(self, path: str) -> Tuple[str, str]:
        """Procesa URLs de My Account"""
        if path == '/personal-info':
            return "myaccount_personal", ""
        elif path == '/security':
            return "myaccount_security", ""
        
        return "myaccount", ""
    
    def _process_search(self, query_params: dict) -> str:
        """Procesa búsquedas de Google"""
        tbm = query_params.get('tbm', [''])[0]
        
        search_types = {
            'isch': 'search_images',
            'vid': 'search_videos', 
            'nws': 'search_news',
            'bks': 'search_books',
            'lcl': 'search_maps',
            'shop': 'search_shopping',
            'flm': 'search_flights',
            'fin': 'search_finance',
            'pts': 'search_patents'
        }
        
        return search_types.get(tbm, 'search')
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para Google - CORREGIDO"""
        emoji = data.get('emoji', '🔍')
        service = data.get('service', '')
        content_type = data.get('content_type', '')
        content_id = data.get('content_id', '')
        query = data.get('query', '')
        
        # Mapeo de nombres legibles
        type_names = {
            # Búsquedas
            "search": "Búsqueda", "search_images": "Búsqueda de imágenes",
            "search_videos": "Búsqueda de videos", "search_news": "Búsqueda de noticias",
            "search_books": "Búsqueda de libros", "search_maps": "Búsqueda en Maps",
            "search_shopping": "Shopping", "search_flights": "Vuelos",
            "search_finance": "Finanzas", "search_patents": "Patentes",
            
            # Drive
            "drive": "Drive", "drive_folder": "Carpeta", "drive_file": "Archivo",
            "drive_mobile": "Móvil", "drive_search": "Buscar", "drive_recent": "Reciente",
            "drive_shared": "Compartido", "drive_trash": "Papelera",
            
            # Docs
            "docs": "Docs", "docs_document": "Documento", "docs_spreadsheet": "Hoja de cálculo",
            "docs_presentation": "Presentación", "docs_form": "Formulario", "docs_drawing": "Dibujo",
            
            # Gmail
            "gmail": "Gmail", "gmail_inbox": "Bandeja de entrada", "gmail_compose": "Redactar",
            "gmail_sent": "Enviados", "gmail_drafts": "Borradores", "gmail_starred": "Destacados",
            "gmail_spam": "Spam", "gmail_trash": "Papelera", "gmail_label": "Etiqueta",
            
            # Maps
            "maps": "Maps", "maps_place": "Lugar", "maps_directions": "Direcciones",
            "maps_search": "Buscar", "maps_contributions": "Contribuciones", "maps_reviews": "Reseñas",
            
            # Photos
            "photos": "Fotos", "photos_photo": "Foto", "photos_album": "Álbum",
            "photos_search": "Buscar", "photos_memories": "Recuerdos", "photos_archive": "Archivo",
            
            # Calendar
            "calendar": "Calendar", "calendar_event": "Evento",
            
            # Meet
            "meet": "Meet", "meet_room": "Reunión", "meet_new": "Nueva reunión",
            
            # Classroom
            "classroom": "Classroom", "classroom_course": "Curso",
            
            # Sites
            "sites": "Sites", "sites_site": "Sitio", "sites_old": "Sitio antiguo",
            
            # Keep
            "keep": "Keep",
            
            # Scholar
            "scholar": "Académico", "scholar_search": "Búsqueda académica", "scholar_profile": "Perfil académico",
            
            # Play
            "play": "Play", "play_app": "App", "play_book": "Libro",
            
            # News
            "news": "Noticias", "news_top": "Noticias principales",
            
            # My Account
            "myaccount": "Mi Cuenta", "myaccount_personal": "Información personal", "myaccount_security": "Seguridad",
            
            # Otros
            "translate": "Traductor", "earth": "Earth", "takeout": "Takeout",
            "contacts": "Contactos", "short_url": "Enlace corto"
        }
        
        type_display = type_names.get(content_type, service.capitalize())
        
        # Construir la salida - CORREGIDO para casos específicos
        if 'search' in content_type and query:
            short_query = query[:25] + "..." if len(query) > 25 else query
            return f"[{emoji} {type_display}: {short_query}]"
        elif content_type in ['photos_search', 'maps_search'] and content_id:
            # Para búsquedas en Photos y Maps, mostrar como "Buscar: contenido"
            short_content = content_id[:25] + "..." if len(content_id) > 25 else content_id
            return f"[{emoji} {type_display}: {short_content}]"
        elif content_id and content_type not in ['search', 'google', 'gmail']:
            short_id = content_id[:15] + "..." if len(content_id) > 15 else content_id
            return f"[{emoji} {type_display} - ID: {short_id}]"
        else:
            return f"[{emoji} {type_display}]"