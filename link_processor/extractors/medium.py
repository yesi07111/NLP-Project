# extractors/medium.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class MediumExtractor(BaseExtractor):
    DOMAINS = [
        'medium.com', 
        'www.medium.com',
        'towardsdatascience.com',
        'aws.medium.com', 
        'javascript.plainenglish.io',
        'blog.prototypr.io',
        'plainenglish.io',
        'prototypr.io'
    ]
    SITE_NAME = 'Medium'

    # Patrones regex para Medium - ORDEN CORREGIDO (más específico primero)
    PATTERNS = [
        # URLs móviles específicas
        ("mobile_identity", r'^/m/global-identity-2/?$'),
        ("mobile_signin", r'^/m/signin/?$'),
        
        # Páginas personales específicas (con subrutas)
        ("personal_stats", r'^/me/stats/?$'),
        ("personal_notifications", r'^/me/notifications/?$'),
        ("personal_readinglist", r'^/readinglist/?$'),
        ("personal_recommendations", r'^/recommendations/?$'),
        ("personal_you", r'^/you/?$'),
        ("personal_me", r'^/me/?$'),
        
        # Búsqueda específica
        ("search_posts", r'^/search/posts/?$'),
        ("search", r'^/search/?$'),
        
        # Tópicos/tags (debe ir antes de publicaciones)
        ("topic", r'^/tag/([^/]+)/?$'),
        
        # Artículos con formato específico
        ("article_p", r'^/p/([^/]+)/?$'),
        
        # Historias destacadas
        ("featured_story", r'^/s/story/([^/]+)/?$'),
        ("featured_notes", r'^/s/notes-on-([^/]+)/([^/]+)/?$'),
        
        # Series
        ("series", r'^/series/([^/]+)/?$'),
        
        # Listas
        ("list", r'^/list/([^/]+)/?$'),
        
        # Perfiles de usuario (debe ir antes de publicaciones)
        ("profile", r'^/@([^/]+)/?$'),
        
        # Publicaciones con subsecciones específicas
        ("publication_about", r'^/([^/@][^/]*)/about/?$'),
        ("publication_latest", r'^/([^/@][^/]*)/latest/?$'),
        ("publication_search", r'^/([^/@][^/]*)/search/?$'),
        ("publication_write", r'^/([^/@][^/]*)/write/?$'),
        
        # Artículos en publicaciones (debe ir ANTES de publicación general)
        ("publication_article", r'^/([^/@][^/]*)/([^/]+)/?$'),
        
        # Membresía y suscripción
        ("membership", r'^/membership/?$'),
        ("subscribe", r'^/subscribe/?$'),
        
        # Publicación principal (más general) - MOVIDO MÁS ABAJO
        ("publication", r'^/([^/@][^/]*)/?$'),
        
        # Página principal (más general)
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, username, publication, additional_info = self._extract_medium_info(parsed_url, domain)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['medium'].get(content_type, '📖'),
            'username': username,
            'publication': publication,
            'content_id': content_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_medium_info(self, parsed_url, domain: str) -> Tuple[str, str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, content_id, username, publication, additional_info = "home", "", "", "", {}
        
        # **LÓGICA CORREGIDA PARA SUBDOMINIOS**
        # Manejar subdominios personalizados PRIMERO, antes de los patrones
        domain_parts = parsed_url.netloc.split('.')
        
        # Detectar si es un subdominio personalizado de Medium
        is_custom_subdomain = False
        custom_publication = ""
        
        # Caso 1: subdominio like towardsdatascience.com
        if domain in ['towardsdatascience.com', 'plainenglish.io', 'prototypr.io']:
            is_custom_subdomain = True
            custom_publication = domain_parts[0]  # towardsdatascience, plainenglish, prototypr
        
        # Caso 2: subdominio like aws.medium.com, javascript.plainenglish.io, blog.prototypr.io
        # **CORRECCIÓN: Excluir 'www' como subdominio personalizado**
        elif len(domain_parts) > 2 and domain_parts[-2:] == ['medium', 'com'] and domain_parts[0] != 'www':
            is_custom_subdomain = True
            custom_publication = domain_parts[0]  # aws
        elif 'plainenglish.io' in domain and len(domain_parts) > 2 and domain_parts[0] != 'www':
            is_custom_subdomain = True
            custom_publication = domain_parts[0]  # javascript
        elif 'prototypr.io' in domain and len(domain_parts) > 2 and domain_parts[0] != 'www':
            is_custom_subdomain = True
            custom_publication = domain_parts[0]  # blog
        
        # **CORRECCIÓN ADICIONAL: Verificar que no sea un dominio principal de Medium**
        main_domains = ['medium.com', 'www.medium.com']
        if parsed_url.netloc in main_domains:
            is_custom_subdomain = False
        
        # Si es subdominio personalizado y tiene path, es un artículo
        if is_custom_subdomain and clean_path and clean_path != '/':
            content_type = "article"
            publication = custom_publication
            # Extraer el ID del artículo del path (última parte después de /)
            article_slug = clean_path.split('/')[-1]
            content_id = article_slug
            # **IMPORTANTE**: Retornar inmediatamente para evitar que otros patrones sobrescriban
            return content_type, content_id, username, publication, additional_info

        # **PATRONES REGULARES** (solo para medium.com/www.medium.com y cuando no es subdominio personalizado)
        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "mobile_identity":
                content_type, content_id = "mobile", "identity"
            elif pattern_type == "mobile_signin":
                content_type, content_id = "mobile", "signin"
                
            elif pattern_type == "personal_stats":
                content_type, content_id = "personal", "stats"
            elif pattern_type == "personal_notifications":
                content_type, content_id = "personal", "notifications"
            elif pattern_type == "personal_readinglist":
                content_type, content_id = "personal", "readinglist"
            elif pattern_type == "personal_recommendations":
                content_type, content_id = "personal", "recommendations"
            elif pattern_type == "personal_you":
                content_type, content_id = "personal", "you"
            elif pattern_type == "personal_me":
                content_type, content_id = "personal", "me"
                
            elif pattern_type == "search_posts":
                content_type, content_id = "search", "posts"
            elif pattern_type == "search":
                content_type = "search"
                if "q" in query_params:
                    additional_info["query"] = query_params["q"][0]
                    
            elif pattern_type == "topic":
                content_type, content_id = "topic", groups[0]
                
            elif pattern_type == "article_p":
                content_type, content_id = "article", groups[0]
                
            elif pattern_type == "featured_story":
                content_type, content_id = "article", groups[0]
                additional_info["featured"] = True
                
            elif pattern_type == "featured_notes":
                content_type, content_id = "article", groups[1]
                additional_info["publication"] = groups[0]
                additional_info["featured"] = True
                
            elif pattern_type == "series":
                content_type, content_id = "series", groups[0]
                
            elif pattern_type == "list":
                content_type, content_id = "list", groups[0]
                
            elif pattern_type == "profile":
                content_type, username = "profile", groups[0]
                
            elif pattern_type == "publication_about":
                content_type, publication, content_id = "publication", groups[0], "about"
            elif pattern_type == "publication_latest":
                content_type, publication, content_id = "publication", groups[0], "latest"
            elif pattern_type == "publication_search":
                content_type, publication, content_id = "publication", groups[0], "search"
            elif pattern_type == "publication_write":
                content_type, publication, content_id = "publication", groups[0], "write"
                
            elif pattern_type == "publication_article":
                content_type, publication, content_id = "article", groups[0], groups[1]
                
            elif pattern_type == "membership":
                content_type = "membership"
            elif pattern_type == "subscribe":
                content_type = "subscribe"
                
            elif pattern_type == "publication":
                # Verificar que no sea una ruta reservada
                reserved = {
                    'p', 'tag', 'search', 'me', 'you', 'recommendations', 
                    'readinglist', 'membership', 'subscribe', 'm', 's', 
                    'series', 'list'
                }
                if groups[0] not in reserved:
                    content_type, publication = "publication", groups[0]
                else:
                    continue
                    
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, username, publication, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '📖')
        username = data.get('username', '')
        publication = data.get('publication', '')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        additional_info = data.get('additional_info', {})
        
        type_names = {
            "profile": "Perfil", "article": "Artículo", 
            "topic": "Tema", "personal": "Personal",
            "search": "Búsqueda", "publication": "Publicación",
            "series": "Serie", "list": "Lista", "membership": "Membresía",
            "subscribe": "Suscripción", "mobile": "Móvil", "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        if content_type == "search" and "query" in additional_info:
            query = additional_info["query"]
            short_query = query[:15] + "..." if len(query) > 15 else query
            return f"[{emoji} {type_display}: {short_query}]"
        
        # Construir la cadena de salida
        parts = [f"{emoji} {type_display} de {self.SITE_NAME}"]
        
        if username:
            parts.append(f"de @{username}")
        
        if publication:
            parts.append(f"en {publication}")
        
        # NO ACORTAR IDs para tópicos y páginas personales
        if content_type in ["topic", "personal"]:
            if content_id:
                parts.append(f"- ID: {content_id}")
        elif content_id and content_id not in ["about", "latest", "search", "write"]:
            short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
            parts.append(f"- ID: {short_id}")
        
        if content_id in ["about", "latest", "search", "write"]:
            parts.append(f"({content_id})")
        
        if "featured" in additional_info:
            parts.append("(destacado)")
        
        return f"[{' '.join(parts)}]"