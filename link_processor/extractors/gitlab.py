# extractors/gitlab.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class GitLabExtractor(BaseExtractor):
    DOMAINS = ['gitlab.com']
    SITE_NAME = 'GitLab'

    # Patrones regex para GitLab - CORREGIDOS
    PATTERNS = [
        # Snippet global
        ("snippet_global", r'^/snippets/(\d+)$'),
        
        # Archivos raw
        ("raw", r'^/([^/]+)/([^/]+)/-/raw/([^/]+)/(.+)$'),
        
        # Archivos blob
        ("file", r'^/([^/]+)/([^/]+)/-/blob/([^/]+)/(.+)$'),
        
        # Directorios tree
        ("directory", r'^/([^/]+)/([^/]+)/-/tree/([^/]+)/(.+)$'),
        
        # Issues específicos
        ("issue", r'^/([^/]+)/([^/]+)/-/issues/(\d+)$'),
        ("issues_list", r'^/([^/]+)/([^/]+)/-/issues/?$'),
        
        # Merge Requests específicos
        ("merge_request", r'^/([^/]+)/([^/]+)/-/merge_requests/(\d+)$'),
        ("merge_requests_list", r'^/([^/]+)/([^/]+)/-/merge_requests/?$'),
        
        # Commits
        ("commit", r'^/([^/]+)/([^/]+)/-/commit/([0-9a-f]+)$'),
        
        # Tags específicos
        ("tag", r'^/([^/]+)/([^/]+)/-/tags/([^/]+)$'),
        ("tags_list", r'^/([^/]+)/([^/]+)/-/tags/?$'),
        
        # Releases
        ("releases_list", r'^/([^/]+)/([^/]+)/-/releases/?$'),
        
        # Wiki páginas
        ("wiki_page", r'^/([^/]+)/([^/]+)/-/wikis/(.+)$'),
        ("wiki", r'^/([^/]+)/([^/]+)/-/wikis/?$'),
        
        # Snippets del proyecto
        ("snippet", r'^/([^/]+)/([^/]+)/-/snippets/(\d+)$'),
        ("snippets_list", r'^/([^/]+)/([^/]+)/-/snippets/?$'),
        
        # Pipelines específicos
        ("pipeline", r'^/([^/]+)/([^/]+)/-/pipelines/(\d+)$'),
        ("pipelines_list", r'^/([^/]+)/([^/]+)/-/pipelines/?$'),
        
        # Jobs específicos
        ("job", r'^/([^/]+)/([^/]+)/-/jobs/(\d+)$'),
        ("jobs_list", r'^/([^/]+)/([^/]+)/-/jobs/?$'),
        
        # Settings sections (DEBE IR ANTES de settings general)
        ("settings_section", r'^/([^/]+)/([^/]+)/-/settings/([^/]+)$'),
        ("settings", r'^/([^/]+)/([^/]+)/-/settings/?$'),
        
        # Activity
        ("activity", r'^/([^/]+)/([^/]+)/-/activity/?$'),
        
        # Graphs (DEBE capturar la rama)
        ("graphs", r'^/([^/]+)/([^/]+)/-/graphs/([^/]+)$'),
        
        # Network (DEBE capturar la rama)
        ("network", r'^/([^/]+)/([^/]+)/-/network/([^/]+)$'),
        
        # Compare
        ("compare", r'^/([^/]+)/([^/]+)/-/compare/?$'),
        
        # Badges (DEBE capturar ref y archivo)
        ("badge", r'^/([^/]+)/([^/]+)/-/badges/([^/]+)/(.+)$'),
        
        # Miembros
        ("project_members", r'^/([^/]+)/([^/]+)/-/project_members/?$'),
        
        # Milestones específicos
        ("milestone", r'^/([^/]+)/([^/]+)/-/milestones/(\d+)$'),
        ("milestones_list", r'^/([^/]+)/([^/]+)/-/milestones/?$'),
        
        # Labels
        ("labels", r'^/([^/]+)/([^/]+)/-/labels/?$'),
        
        # Boards
        ("boards", r'^/([^/]+)/([^/]+)/-/boards/?$'),
        
        # Servicios
        ("services", r'^/([^/]+)/([^/]+)/-/services/?$'),
        
        # Deploy keys
        ("deploy_keys", r'^/([^/]+)/([^/]+)/-/deploy_keys/?$'),
        
        # Protected branches
        ("protected_branches", r'^/([^/]+)/([^/]+)/-/protected_branches/?$'),
        
        # Webhooks
        ("hooks", r'^/([^/]+)/([^/]+)/-/hooks/?$'),
        
        # Import
        ("import", r'^/([^/]+)/([^/]+)/-/import/?$'),
        
        # Analytics
        ("analytics", r'^/([^/]+)/([^/]+)/-/analytics/?$'),
        
        # CI lint
        ("ci_lint", r'^/([^/]+)/([^/]+)/-/ci/lint/?$'),
        
        # Runners
        ("runners", r'^/([^/]+)/([^/]+)/-/runners/?$'),
        
        # Packages
        ("packages", r'^/([^/]+)/([^/]+)/-/packages/?$'),
        
        # Container Registry
        ("container_registry", r'^/([^/]+)/([^/]+)/container_registry/?$'),
        
        # Grupos
        ("group", r'^/groups/([^/]+)/?$'),
        
        # Proyecto principal
        ("project", r'^/([^/]+)/([^/]+)/?$'),
        
        # Perfil de usuario/grupo
        ("profile", r'^/([^/]+)/?$'),
    ]
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, username, project, file_path = self._extract_gitlab_info(parsed_url)
        
        # Obtener emoji del mapeo
        emoji = EMOJI_MAPS['gitlab'].get(content_type, '💻')
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': emoji,
            'username': username,
            'project': project,
            'file_path': file_path,
            'content_type': content_type
        }
    
    def _extract_gitlab_info(self, parsed_url) -> Tuple[str, str, str, str]:
        """Extrae metadata de GitLab usando expresiones regulares"""
        path = parsed_url.path
        content_type = ""
        username = ""
        project = ""
        file_path = ""

        # Verificar todos los patrones en orden
        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, path)
            if match:
                groups = match.groups()
                
                # Procesar según el tipo de patrón
                if pattern_type == 'snippet_global':
                    snippet_id = groups[0]
                    content_type = 'snippet'
                    file_path = snippet_id
                    
                elif pattern_type == 'raw':
                    username, project, ref, filepath = groups
                    content_type = 'file'
                    file_path = f"{ref}/{filepath}"
                    
                elif pattern_type == 'file':
                    username, project, ref, filepath = groups
                    content_type = 'file'
                    file_path = f"{ref}/{filepath}"
                    
                elif pattern_type == 'directory':
                    username, project, ref, dirpath = groups
                    content_type = 'directory'
                    file_path = f"{ref}/{dirpath}"
                    
                elif pattern_type == 'issue':
                    username, project, issue_num = groups
                    content_type = 'issue'
                    file_path = issue_num
                    
                elif pattern_type == 'issues_list':
                    username, project = groups
                    content_type = 'issue'
                    
                elif pattern_type == 'merge_request':
                    username, project, mr_num = groups
                    content_type = 'merge_request'
                    file_path = mr_num
                    
                elif pattern_type == 'merge_requests_list':
                    username, project = groups
                    content_type = 'merge_request'
                    
                elif pattern_type == 'commit':
                    username, project, commit_hash = groups
                    content_type = 'commit'
                    file_path = commit_hash
                    
                elif pattern_type == 'tag':
                    username, project, tag = groups
                    content_type = 'tag'  # Cambiado de 'tags' a 'tag' para específico
                    file_path = tag
                    
                elif pattern_type == 'tags_list':
                    username, project = groups
                    content_type = 'tags'
                    
                elif pattern_type == 'releases_list':
                    username, project = groups
                    content_type = 'releases'
                    
                elif pattern_type == 'wiki_page':
                    username, project, page = groups
                    content_type = 'wiki'
                    file_path = page
                    
                elif pattern_type == 'wiki':
                    username, project = groups
                    content_type = 'wiki'
                    
                elif pattern_type == 'snippet':
                    username, project, snippet_id = groups
                    content_type = 'snippet'
                    file_path = snippet_id
                    
                elif pattern_type == 'snippets_list':
                    username, project = groups
                    content_type = 'snippet'
                    
                elif pattern_type == 'pipeline':
                    username, project, pipeline_id = groups
                    content_type = 'pipeline'
                    file_path = pipeline_id
                    
                elif pattern_type == 'pipelines_list':
                    username, project = groups
                    content_type = 'pipeline'
                    
                elif pattern_type == 'job':
                    username, project, job_id = groups
                    content_type = 'job'
                    file_path = job_id
                    
                elif pattern_type == 'jobs_list':
                    username, project = groups
                    content_type = 'job'
                    
                elif pattern_type == 'settings_section':  # IMPORTANTE: Este debe ir antes de 'settings'
                    username, project, section = groups
                    content_type = 'settings'
                    file_path = section
                    
                elif pattern_type == 'settings':
                    username, project = groups
                    content_type = 'settings'
                    
                elif pattern_type == 'activity':
                    username, project = groups
                    content_type = 'activity'
                    
                elif pattern_type == 'graphs':
                    username, project, ref = groups
                    content_type = 'graphs'
                    file_path = ref
                    
                elif pattern_type == 'network':
                    username, project, ref = groups
                    content_type = 'network'
                    file_path = ref
                    
                elif pattern_type == 'compare':
                    username, project = groups
                    content_type = 'compare'
                    
                elif pattern_type == 'badge':
                    username, project, ref, badge_file = groups
                    content_type = 'badge'
                    file_path = f"{ref}/{badge_file}"
                    
                elif pattern_type == 'project_members':
                    username, project = groups
                    content_type = 'project_members'
                    
                elif pattern_type == 'milestone':
                    username, project, milestone_id = groups
                    content_type = 'milestone'
                    file_path = milestone_id
                    
                elif pattern_type == 'milestones_list':
                    username, project = groups
                    content_type = 'milestone'
                    
                elif pattern_type == 'labels':
                    username, project = groups
                    content_type = 'labels'
                    
                elif pattern_type == 'boards':
                    username, project = groups
                    content_type = 'boards'
                    
                elif pattern_type == 'services':
                    username, project = groups
                    content_type = 'services'
                    
                elif pattern_type == 'deploy_keys':
                    username, project = groups
                    content_type = 'deploy_keys'
                    
                elif pattern_type == 'protected_branches':
                    username, project = groups
                    content_type = 'protected_branches'
                    
                elif pattern_type == 'hooks':
                    username, project = groups
                    content_type = 'hooks'
                    
                elif pattern_type == 'import':
                    username, project = groups
                    content_type = 'import'
                    
                elif pattern_type == 'analytics':
                    username, project = groups
                    content_type = 'analytics'
                    
                elif pattern_type == 'ci_lint':
                    username, project = groups
                    content_type = 'ci_lint'
                    
                elif pattern_type == 'runners':
                    username, project = groups
                    content_type = 'runners'
                    
                elif pattern_type == 'packages':
                    username, project = groups
                    content_type = 'packages'
                    
                elif pattern_type == 'container_registry':
                    username, project = groups
                    content_type = 'container_registry'
                    
                elif pattern_type == 'group':
                    group_name = groups[0]
                    content_type = 'group'
                    username = group_name
                    
                elif pattern_type == 'project':
                    username, project = groups
                    content_type = 'project'
                    
                elif pattern_type == 'profile':
                    username = groups[0]
                    content_type = 'profile'
                    
                break

        return content_type, username, project, file_path
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para GitLab - CORREGIDO"""
        emoji = data.get('emoji', '💻')
        username = data.get('username', '')
        project = data.get('project', '')
        file_path = data.get('file_path', '')
        content_type = data.get('content_type', '')
        
        # Construir la cadena de visualización
        username_display = f" de {username}" if username else ""
        project_display = f"/{project}" if project else ""
        
        # Para tipos específicos, mostrar "Archivo: ...", para otros no mostrar nada
        # EXPANDIR la lista de tipos que muestran file_path
        if content_type in ['file', 'directory', 'commit', 'issue', 'merge_request', 
                          'tag', 'wiki', 'snippet', 'pipeline', 'job', 'milestone',
                          'settings', 'graphs', 'network', 'badge']:
            file_display = f" - Archivo: {file_path}" if file_path else ""
        else:
            file_display = ""

        # Mapear content_type a nombre legible - CORREGIDO
        type_names = {
            "file": "Archivo", "issue": "Issue", "merge_request": "Merge Request",
            "project": "Proyecto", "profile": "Perfil", "directory": "Directorio",
            "commit": "Commit", "snippet": "Snippet", "pipeline": "Pipeline",
            "job": "Job", "wiki": "Wiki", "tag": "Tag", "tags": "Tags", 
            "releases": "Releases", "settings": "Settings", "activity": "Actividad", 
            "graphs": "Gráficos", "network": "Network", "compare": "Comparar", 
            "badge": "Badge", "project_members": "Miembros", "milestone": "Milestone", 
            "labels": "Labels", "boards": "Boards", "services": "Servicios",
            "deploy_keys": "Deploy Keys", "protected_branches": "Ramas Protegidas",
            "hooks": "Webhooks", "import": "Importar", "analytics": "Analíticas",
            "ci_lint": "CI Lint", "runners": "Runners", "packages": "Packages",
            "container_registry": "Container Registry", "group": "Grupo"
        }

        type_display = type_names.get(content_type, "Contenido")

        return f"[{emoji} {type_display} de {self.SITE_NAME}{username_display}{project_display}{file_display}]"