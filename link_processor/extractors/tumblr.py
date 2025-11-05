# extractors/tumblr.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class TumblrExtractor(BaseExtractor):
    DOMAINS = ['tumblr.com', 'www.tumblr.com']
    SITE_NAME = 'Tumblr'

    # Patrones regex para Tumblr - REORDENADOS con los más específicos primero
    PATTERNS = [
        # Posts multimedia específicos (MÁS ESPECÍFICOS)
        ("post_photo", r'^/post/(\d+)/[^/]+/photo/(\d+)$'),
        ("post_video", r'^/post/(\d+)/[^/]+/video/(\d+)$'),
        ("post_audio", r'^/post/(\d+)/[^/]+/audio/(\d+)$'),
        
        # Post general (menos específico) - INCLUYE todos los tipos de posts
        ("post_general", r'^/post/(\d+)/[^/]+/?$'),
        ("post_simple", r'^/post/(\d+)/?$'),
        
        # Posts sin subdominio (nuevos patrones para URLs sin username en subdominio)
        ("post_no_subdomain_photo", r'^/([^/]+)/post/(\d+)/[^/]+/photo/(\d+)$'),
        ("post_no_subdomain_video", r'^/([^/]+)/post/(\d+)/[^/]+/video/(\d+)$'),
        ("post_no_subdomain_audio", r'^/([^/]+)/post/(\d+)/[^/]+/audio/(\d+)$'),
        ("post_no_subdomain_general", r'^/([^/]+)/post/(\d+)/[^/]+/?$'),
        ("post_no_subdomain_simple", r'^/([^/]+)/post/(\d+)/?$'),
        
        # Dashboard subsecciones (específicas)
        ("dashboard_queue", r'^/dashboard/queue/?$'),
        ("dashboard_drafts", r'^/dashboard/drafts/?$'),
        ("dashboard_activity", r'^/dashboard/activity/?$'),
        
        # Mensajes subsecciones (específicas)
        ("messages_inbox", r'^/messages/inbox/?$'),
        ("messages_sent", r'^/messages/sent/?$'),
        
        # Configuración subsecciones (específicas)
        ("settings_account", r'^/settings/account/?$'),
        ("settings_blog", r'^/settings/blog/?$'),
        ("settings_appearance", r'^/settings/appearance/?$'),
        
        # Políticas específicas
        ("privacy_policy", r'^/privacy/?$'),
        ("terms_of_service", r'^/terms/?$'),
        
        # Blog posts específicos
        ("blog_post", r'^/blog/([^/]+)/?$'),
        
        # Explore categorías
        ("explore_category", r'^/explore/([^/]+)/?$'),
        
        # Help artículos
        ("help_article", r'^/help/([^/]+)/?$'),
        
        # API docs
        ("api_docs", r'^/developers/api/?$'),
        
        # Secciones generales
        ("tagged", r'^/tagged/([^/]+)/?$'),
        ("archive", r'^/archive/?$'),
        ("likes", r'^/likes/?$'),
        ("dashboard", r'^/dashboard/?$'),
        ("followers", r'^/followers/?$'),
        ("following", r'^/following/?$'),
        ("search", r'^/search/?$'),
        ("messages", r'^/messages/?$'),
        ("settings", r'^/settings/?$'),
        ("blog", r'^/blog/?$'),
        ("explore", r'^/explore/?$'),
        ("trending", r'^/trending/?$'),
        ("staff", r'^/staff/?$'),
        ("policy", r'^/policy/?$'),
        ("help", r'^/help/?$'),
        ("developers", r'^/developers/?$'),
        ("app", r'^/app/?$'),
        ("about", r'^/about/?$'),
        ("theme", r'^/theme/?$'),
        ("avatar", r'^/avatar/?$'),
        
        # Página principal de blog
        ("blog_home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, additional_info = self._extract_tumblr_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['tumblr'].get(content_type, '📝'),
            'content_id': content_id,
            'additional_info': additional_info,
            'content_type': content_type,
        }

    def _extract_tumblr_info(self, parsed_url) -> Tuple[str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "tumblr_home"
        content_id = ""
        additional_info = {}
        
        # Extraer username del subdominio (para URLs con subdominio)
        domain_parts = parsed_url.netloc.split('.')
        if len(domain_parts) > 2 and domain_parts[0] not in ['www', 'tumblr']:
            additional_info["username"] = domain_parts[0]
            content_type = "blog_home"

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            # Procesar posts sin subdominio primero (extraen username de la ruta)
            if pattern_type.startswith("post_no_subdomain_"):
                if len(groups) >= 2:
                    additional_info["username"] = groups[0]
                    post_id = groups[1]
                    
                    if pattern_type == "post_no_subdomain_photo":
                        content_type, content_id = "photo", post_id
                    elif pattern_type == "post_no_subdomain_video":
                        content_type, content_id = "video", post_id
                    elif pattern_type == "post_no_subdomain_audio":
                        content_type, content_id = "audio", post_id
                    elif pattern_type == "post_no_subdomain_general":
                        content_type, content_id = "post", post_id
                    elif pattern_type == "post_no_subdomain_simple":
                        content_type, content_id = "post", post_id
            
            # Procesar posts con subdominio
            elif pattern_type.startswith("post_"):
                if pattern_type == "post_photo":
                    content_type, content_id = "photo", groups[0]
                elif pattern_type == "post_video":
                    content_type, content_id = "video", groups[0]
                elif pattern_type == "post_audio":
                    content_type, content_id = "audio", groups[0]
                elif pattern_type == "post_general":
                    content_type, content_id = "post", groups[0]
                elif pattern_type == "post_simple":
                    content_type, content_id = "post", groups[0]
            elif pattern_type == "tagged":
                content_type, content_id = "tag", groups[0]
            elif pattern_type == "archive":
                content_type = "archive"
            elif pattern_type == "likes":
                content_type = "likes"
            elif pattern_type.startswith("dashboard"):
                content_type = pattern_type
            elif pattern_type.startswith("messages"):
                content_type = pattern_type
            elif pattern_type.startswith("settings"):
                content_type = pattern_type
            elif pattern_type == "privacy_policy":
                content_type = "privacy_policy"
            elif pattern_type == "terms_of_service":
                content_type = "terms_of_service"
            elif pattern_type == "blog_post":
                content_type, content_id = "blog", groups[0]
            elif pattern_type == "explore_category":
                content_type, content_id = "explore", groups[0]
            elif pattern_type == "help_article":
                content_type, content_id = "help", groups[0]
            elif pattern_type == "api_docs":
                content_type = "api_docs"
            elif pattern_type in ["search", "blog", "explore", "trending", "staff", 
                                "policy", "help", "developers", "app", "about", 
                                "theme", "avatar", "followers", "following"]:
                content_type = pattern_type
            elif pattern_type == "blog_home":
                # Ya establecido por defecto para blogs de usuario
                pass

            break

        # Manejar búsquedas con parámetros de consulta
        if content_type == "search" and "q" in query_params:
            content_id = query_params["q"][0]

        return content_type, content_id, additional_info

    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '📝')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        info = data.get('additional_info', {})
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "post": "Post", "photo": "Foto", "video": "Video", "audio": "Audio",
            "tag": "Etiqueta", "archive": "Archivo",
            "likes": "Likes", "dashboard": "Dashboard", "dashboard_queue": "Cola",
            "dashboard_drafts": "Borradores", "dashboard_activity": "Actividad",
            "followers": "Seguidores", "following": "Siguiendo", "search": "Búsqueda",
            "messages": "Mensajes", "messages_inbox": "Bandeja de entrada", 
            "messages_sent": "Mensajes enviados", "settings": "Configuración", 
            "settings_account": "Configuración de cuenta", "settings_blog": "Configuración de blog", 
            "settings_appearance": "Apariencia", "blog": "Blog", "explore": "Explorar", 
            "trending": "Trending", "staff": "Staff", "policy": "Política", 
            "privacy_policy": "Política de privacidad", "terms_of_service": "Términos de servicio", 
            "help": "Ayuda", "developers": "Desarrolladores", "api_docs": "Documentación API", 
            "app": "App", "blog_home": "Blog principal", "tumblr_home": "Tumblr principal", 
            "about": "Acerca de", "theme": "Tema", "avatar": "Avatar"
        }
        
        type_display = type_names.get(content_type, "Contenido")

        # Casos especiales con formato específico
        if content_type == "search" and content_id:
            search_term = content_id
            short_term = search_term[:20] + "..." if len(search_term) > 20 else search_term
            return f"[{emoji} {type_display}: {short_term}]"

        # Construir partes del display
        parts = []
        
        if "username" in info:
            parts.append(f"de {info['username']}")
        
        if content_id and content_type not in ["search", "blog_home", "tumblr_home"]:
            if content_type == "tag":
                parts.append(f"#{content_id}")
            elif content_type == "explore":
                parts.append(f"Categoría: {content_id}")
            elif content_type == "help":
                parts.append(f"Artículo: {content_id}")
            elif content_type == "blog":
                parts.append(f"Post: {content_id}")
            else:
                parts.append(f"ID: {content_id}")

        parts_display = " - " + ", ".join(parts) if parts else ""

        return f"[{emoji} {type_display} de {self.SITE_NAME}{parts_display}]"