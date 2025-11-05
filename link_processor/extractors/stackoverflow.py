# extractors/stackoverflow.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class StackOverflowExtractor(BaseExtractor):
    DOMAINS = ['stackoverflow.com', 'stackexchange.com', 'es.stackoverflow.com', 'www.stackoverflow.com']
    SITE_NAME = 'Stack Overflow'

    # Patrones regex para Stack Overflow - REORDENADOS y CORREGIDOS
    PATTERNS = [
        # Respuesta específica: /questions/123456/title-slug/789012
        ("answer_specific", r'^/questions/(\d+)/[^/]+/(\d+)/?$'),
        
        # Pregunta con slug: /questions/123456/title-slug
        ("question_with_slug", r'^/questions/(\d+)/[^/]+/?$'),
        
        # Pregunta corta: /questions/123456
        ("question_short", r'^/questions/(\d+)/?$'),
        
        # Usuarios con secciones específicas - MOVIDOS ANTES del patrón general de usuarios
        ("user_edit", r'^/users/(\d+)/[^/]+/edit/?$'),
        ("user_profile", r'^/users/(\d+)/[^/]+/profile/?$'),
        ("user_top_questions", r'^/users/(\d+)/[^/]+/top-questions/?$'),
        ("user_top_answers", r'^/users/(\d+)/[^/]+/top-answers/?$'),
        
        # Usuario con nombre: /users/123456/username
        ("user_with_name", r'^/users/(\d+)/[^/]+/?$'),
        
        # Etiquetas con subsecciones - MOVIDOS ANTES del patrón general de etiquetas
        ("tag_info", r'^/tags/([^/]+)/info/?$'),
        ("tag_unanswered", r'^/tags/([^/]+)/unanswered/?$'),
        
        # Revisión específica: /review/task-type/123456
        ("review_specific", r'^/review/[^/]+/(\d+)/?$'),
        
        # Empleos específicos: /jobs/123456/title - AGREGADO
        ("job_specific", r'^/jobs/(\d+)/[^/]+/?$'),
        
        # Insignias específicas: /badges/123/title - AGREGADO
        ("badge_specific", r'^/badges/(\d+)/[^/]+/?$'),
        
        # Elementos con ID numérico
        ("collection", r'^/collection/(\d+)/?$'),
        ("post", r'^/posts/(\d+)/?$'),
        ("job", r'^/jobs/(\d+)/?$'),  # Este patrón ya no es necesario para URLs con slug
        ("election", r'^/election/(\d+)/?$'),
        
        # Secciones específicas
        ("jobs_companies", r'^/jobs/companies/?$'),
        ("jobs_developer", r'^/jobs/developer/?$'),
        
        # Elementos con slug/nombre
        ("tag", r'^/tags/([^/]+)/?$'),
        ("company", r'^/company/([^/]+)/?$'),
        ("documentation", r'^/documentation/([^/]+)/?$'),
        ("teams", r'^/teams/([^/]+)/?$'),
        ("blog", r'^/blog/([^/]+)/?$'),
        ("help", r'^/help/([^/]+)/?$'),
        ("badges", r'^/badges/([^/]+)/?$'),
        
        # Secciones generales
        ("search", r'^/search/?$'),
        ("users", r'^/users/?$'),
        ("questions", r'^/questions/?$'),
        ("tags", r'^/tags/?$'),
        ("jobs", r'^/jobs/?$'),
        ("review", r'^/review/?$'),
        
        # Página principal
        ("home", r'^/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, question_id, answer_id, user_id, additional_info = self._extract_stackoverflow_info(parsed_url)
        
        # Obtener el emoji correcto del mapa
        emoji_key = content_type
        emoji = EMOJI_MAPS['stackoverflow'].get(emoji_key, '❓')
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': emoji,
            'question_id': question_id,
            'answer_id': answer_id,
            'user_id': user_id,
            'content_type': content_type,
            'additional_info': additional_info
        }
    
    def _extract_stackoverflow_info(self, parsed_url) -> Tuple[str, str, str, str, Dict[str, Any]]:
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "home"
        question_id = ""
        answer_id = ""
        user_id = ""
        additional_info = {}

        # Detectar sitio específico por subdominio
        domain_parts = parsed_url.netloc.split('.')
        if len(domain_parts) > 2 and domain_parts[0] not in ['www', 'stackoverflow']:
            additional_info["language_site"] = domain_parts[0]

        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue

            groups = match.groups()

            if pattern_type == "answer_specific":
                content_type, question_id, answer_id = "answer", groups[0], groups[1]
            elif pattern_type in ["question_with_slug", "question_short"]:
                content_type, question_id = "question", groups[0]
            elif pattern_type in ["user_edit", "user_profile", "user_top_questions", "user_top_answers"]:
                content_type, user_id = pattern_type, groups[0]
            elif pattern_type == "user_with_name":
                content_type, user_id = "user", groups[0]
            elif pattern_type in ["tag_info", "tag_unanswered"]:
                content_type, question_id = pattern_type, groups[0]
            elif pattern_type == "review_specific":
                content_type, question_id = "review", groups[0]
            elif pattern_type == "job_specific":  # NUEVO
                content_type, question_id = "job", groups[0]
            elif pattern_type == "badge_specific":  # NUEVO
                content_type, question_id = "badges", groups[0]
            elif pattern_type in ["collection", "post", "job", "election"]:
                content_type, question_id = pattern_type, groups[0]
            elif pattern_type in ["jobs_companies", "jobs_developer"]:
                content_type = pattern_type
            elif pattern_type in ["tag", "company", "documentation", "teams", "blog", "help", "badges"]:
                content_type, question_id = pattern_type, groups[0]
            elif pattern_type in ["search", "users", "questions", "tags", "jobs", "review"]:
                content_type = pattern_type
                if pattern_type == "search" and "q" in query_params:
                    additional_info["query"] = query_params["q"][0].replace("+", " ")
            elif pattern_type == "home":
                content_type = "home"

            break

        return content_type, question_id, answer_id, user_id, additional_info
    
    def format_output(self, data: Dict[str, Any]) -> str:
        emoji = data.get('emoji', '❓')
        question_id = data.get('question_id', '')
        answer_id = data.get('answer_id', '')
        user_id = data.get('user_id', '')
        content_type = data.get('content_type', '')
        info = data.get('additional_info', {})
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "question": "Pregunta", "answer": "Respuesta", "user": "Usuario",
            "user_edit": "Editar perfil", "user_profile": "Perfil de usuario",
            "user_top_questions": "Mejores preguntas", "user_top_answers": "Mejores respuestas",
            "tag": "Etiqueta", "tag_info": "Info de etiqueta", "tag_unanswered": "Etiqueta sin respuesta",
            "search": "Búsqueda", "collection": "Colección", "post": "Post",
            "company": "Empresa", "job": "Empleo", "jobs_companies": "Empresas con empleos",
            "jobs_developer": "Empleos para desarrolladores", "documentation": "Documentación",
            "teams": "Teams", "blog": "Blog", "help": "Ayuda",
            "review": "Revisión", "election": "Elección", "badges": "Insignias",
            "users": "Usuarios", "questions": "Preguntas", "tags": "Etiquetas", "jobs": "Empleos",
            "home": "Inicio"
        }

        type_display = type_names.get(content_type, "Contenido")
        
        # Manejar sitios de idiomas específicos
        if "language_site" in info:
            lang = info["language_site"]
            if lang == "es":
                type_display = f"Stack Overflow en español - {type_display}"
            else:
                type_display = f"Stack Overflow {lang} - {type_display}"

        # Casos especiales con formato específico
        if content_type == "search" and "query" in info:
            query = info["query"]
            short_query = query[:20] + "..." if len(query) > 20 else query
            return f"[{emoji} {type_display}: {short_query}]"

        # Construir display de IDs - CORREGIDO para mostrar solo el valor en casos específicos
        id_parts = []
        if question_id:
            if content_type in ["tag", "company", "documentation", "teams", "blog", "help", "badges", 
                              "tag_info", "tag_unanswered"]:
                # Para estos tipos, mostrar solo el valor sin "ID:"
                id_parts.append(f"{question_id}")
            else:
                id_parts.append(f"ID: {question_id}")
        
        if answer_id:
            id_parts.append(f"Respuesta: {answer_id}")
        
        if user_id:
            id_parts.append(f"Usuario: {user_id}")

        id_display = " - " + ", ".join(id_parts) if id_parts else ""

        return f"[{emoji} {type_display}{id_display}]"