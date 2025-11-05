# extractors/linkedin.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class LinkedInExtractor(BaseExtractor):
    DOMAINS = ['linkedin.com', 'www.linkedin.com']
    SITE_NAME = 'LinkedIn'

    # Patrones regex para LinkedIn - MÁS ESPECÍFICOS Y COMPLETOS
    PATTERNS = [
        # Perfiles con subsecciones específicas (más específico primero)
        ("profile_experience", r'^/in/([^/]+)/details/experience/?$'),
        ("profile_edit", r'^/in/([^/]+)/edit/?$'),
        
        # Perfiles personales
        ("profile", r'^/in/([^/]+)/?$'),
        
        # Empresas con subsecciones
        ("company_about", r'^/company/([^/]+)/about/?$'),
        ("company_people", r'^/company/([^/]+)/people/?$'),
        ("company_jobs", r'^/company/([^/]+)/jobs/?$'),
        ("company", r'^/company/([^/]+)/?$'),
        
        # Publicaciones
        ("post", r'^/posts/([^/]+)/?$'),
        ("feed_post", r'^/feed/update/([^/]+)/?$'),
        
        # Empleos específicos
        ("job_view", r'^/jobs/view/([^/]+)/?$'),
        ("job_collections_id", r'^/jobs/collections/([^/]+)/?$'),
        ("job_collections", r'^/jobs/collections/?$'),
        ("job_search", r'^/jobs/search/?$'),
        ("jobs", r'^/jobs/?$'),
        
        # Aprendizaje - patrones más específicos
        ("learning_path", r'^/learning/path/([^/]+)/?$'),
        ("learning_exam", r'^/learning/exam/([^/]+)/?$'),
        ("learning_course", r'^/learning/course/([^/]+)/?$'),
        ("learning_topic", r'^/learning/([^/]+)/?$'),  # Para /learning/data-science
        ("learning", r'^/learning/?$'),
        
        # Mensajes
        ("messaging_thread", r'^/messaging/thread/([^/]+)/?$'),
        ("messaging", r'^/messaging/?$'),
        
        # Búsqueda - patrones más específicos
        ("search_results_people", r'^/search/results/people/?$'),
        ("search_results_content", r'^/search/results/content/?$'),
        ("search_results", r'^/search/results/?$'),
        ("search", r'^/search/?$'),
        
        # Grupos - patrones más específicos
        ("group_discussion_id", r'^/groups/([^/]+)/discussion/([^/]+)/?$'),
        ("group_discussion", r'^/groups/([^/]+)/discussion/?$'),
        ("group_members", r'^/groups/([^/]+)/members/?$'),
        ("group", r'^/groups/([^/]+)/?$'),
        
        # Eventos - patrones más específicos
        ("event_attendees", r'^/events/([^/]+)/attendees/?$'),
        ("event", r'^/events/([^/]+)/?$'),
        
        # Pulse (noticias) - patrones más específicos
        ("pulse_article", r'^/pulse/([^/]+)/?$'),
        ("pulse", r'^/pulse/?$'),
        
        # Sales Navigator
        ("sales_lead", r'^/sales/lead/([^/]+)/?$'),
        ("sales_account", r'^/sales/account/([^/]+)/?$'),
        ("sales", r'^/sales/?$'),
        
        # Feed/Actividad
        ("feed", r'^/feed/?$'),
        ("activity", r'^/activity/?$'),
        
        # Notificaciones y Red
        ("notifications", r'^/notifications/?$'),
        ("mynetwork_invite", r'^/mynetwork/invite-connect/?$'),
        ("mynetwork", r'^/mynetwork/?$'),
        
        # Learning Path alternativo
        ("learning_path_alt", r'^/learning-path/([^/]+)/?$'),
        
        # Página principal (más general)
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, content_id, sub_type, additional_info = self._extract_linkedin_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['linkedin'].get(content_type, '💼'),
            'content_id': content_id,
            'content_type': content_type,
            'sub_type': sub_type,
            'additional_info': additional_info
        }
    
    def _extract_linkedin_info(self, parsed_url) -> Tuple[str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type, content_id, sub_type, additional_info = "home", "", "", {}

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "profile_experience":
                content_type, content_id, sub_type = "profile", groups[0], "experience"
            elif pattern_type == "profile_edit":
                content_type, content_id, sub_type = "profile", groups[0], "edit"
            elif pattern_type == "profile":
                content_type, content_id = "profile", groups[0]
                
            elif pattern_type == "company_about":
                content_type, content_id, sub_type = "company", groups[0], "about"
            elif pattern_type == "company_people":
                content_type, content_id, sub_type = "company", groups[0], "people"
            elif pattern_type == "company_jobs":
                content_type, content_id, sub_type = "company", groups[0], "jobs"
            elif pattern_type == "company":
                content_type, content_id = "company", groups[0]
                
            elif pattern_type in ["post", "feed_post"]:
                content_type, content_id = "post", groups[0]
                
            elif pattern_type == "job_view":
                content_type, content_id = "job", groups[0]
            elif pattern_type == "job_collections_id":
                content_type, content_id, sub_type = "job", groups[0], "collections"
            elif pattern_type == "job_collections":
                content_type, sub_type = "job", "collections"
            elif pattern_type == "job_search":
                content_type, sub_type = "job", "search"
            elif pattern_type == "jobs":
                content_type = "job"
                
            elif pattern_type == "learning_path":
                content_type, content_id = "learning_path", groups[0]
            elif pattern_type == "learning_exam":
                content_type, content_id, sub_type = "learning", groups[0], "exam"
            elif pattern_type == "learning_course":
                content_type, content_id, sub_type = "learning", groups[0], "course"
            elif pattern_type == "learning_topic":
                content_type, content_id = "learning", groups[0]
            elif pattern_type == "learning":
                content_type = "learning"
                
            elif pattern_type == "messaging_thread":
                content_type, content_id, sub_type = "messaging", groups[0], "thread"
            elif pattern_type == "messaging":
                content_type = "messaging"
                
            elif pattern_type == "search_results_people":
                content_type, sub_type = "search", "people"
            elif pattern_type == "search_results_content":
                content_type, sub_type = "search", "content"
            elif pattern_type == "search_results":
                content_type, sub_type = "search", "results"
            elif pattern_type == "search":
                content_type = "search"
                if "keywords" in query_params:
                    additional_info["query"] = query_params["keywords"][0]
                elif "q" in query_params:
                    additional_info["query"] = query_params["q"][0]
                
            elif pattern_type == "group_discussion_id":
                content_type, content_id, sub_type = "group", groups[0], "discussion"
                additional_info["discussion_id"] = groups[1]
            elif pattern_type == "group_discussion":
                content_type, content_id, sub_type = "group", groups[0], "discussion"
            elif pattern_type == "group_members":
                content_type, content_id, sub_type = "group", groups[0], "members"
            elif pattern_type == "group":
                content_type, content_id = "group", groups[0]
                
            elif pattern_type == "event_attendees":
                content_type, content_id, sub_type = "event", groups[0], "attendees"
            elif pattern_type == "event":
                content_type, content_id = "event", groups[0]
                
            elif pattern_type == "pulse_article":
                content_type, content_id = "pulse", groups[0]
            elif pattern_type == "pulse":
                content_type = "pulse"
                
            elif pattern_type == "sales_lead":
                content_type, content_id, sub_type = "sales", groups[0], "lead"
            elif pattern_type == "sales_account":
                content_type, content_id, sub_type = "sales", groups[0], "account"
            elif pattern_type == "sales":
                content_type = "sales"
                
            elif pattern_type == "feed":
                content_type = "feed"
            elif pattern_type == "activity":
                content_type = "activity"
                
            elif pattern_type == "notifications":
                content_type = "notifications"
            elif pattern_type == "mynetwork_invite":
                content_type, sub_type = "network", "invite"
            elif pattern_type == "mynetwork":
                content_type = "network"
                
            elif pattern_type == "learning_path_alt":
                content_type, content_id = "learning_path", groups[0]
                
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, content_id, sub_type, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '💼')
        content_id = data.get('content_id', '')
        content_type = data.get('content_type', '')
        sub_type = data.get('sub_type', '')
        additional_info = data.get('additional_info', {})
        
        type_names = {
            "profile": "Perfil", "company": "Empresa", 
            "post": "Publicación", "activity": "Actividad", "feed": "Feed",
            "job": "Empleo", "learning": "Curso", "learning_path": "Ruta de aprendizaje",
            "messaging": "Mensajes", "search": "Búsqueda", "group": "Grupo",
            "event": "Evento", "pulse": "Noticias", "sales": "Ventas",
            "notifications": "Notificaciones", "network": "Red",
            "home": "Inicio"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        if content_type == "search" and "query" in additional_info:
            query = additional_info["query"]
            short_query = query[:15] + "..." if len(query) > 15 else query
            return f"[{emoji} {type_display}: {short_query}]"
        
        # No acortar IDs de perfiles y empresas (son nombres)
        if content_type in ["profile", "company"]:
            short_id = content_id
        else:
            short_id = content_id[:8] + "..." if len(content_id) > 8 else content_id
        
        if content_id and sub_type:
            return f"[{emoji} {type_display} de {self.SITE_NAME} - ID: {short_id} ({sub_type})]"
        elif content_id:
            return f"[{emoji} {type_display} de {self.SITE_NAME} - ID: {short_id}]"
        elif sub_type:
            return f"[{emoji} {type_display} de {self.SITE_NAME} ({sub_type})]"
        else:
            return f"[{emoji} {type_display} de {self.SITE_NAME}]"