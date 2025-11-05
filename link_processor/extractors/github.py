# extractors/github.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class GitHubExtractor(BaseExtractor):
    DOMAINS = ['github.com', 'gist.github.com', 'raw.githubusercontent.com']
    SITE_NAME = 'GitHub'

    # Patrones regex actualizados - agregando los patrones faltantes
    PATTERNS = [
        # raw.githubusercontent.com (raw files)
        ("raw", r'^/([^/]+)/([^/]+)/([^/]+)/(.+)$'),

        # Gist (dominio gist.github.com)
        ("gist", r'^/([^/]+)/([0-9a-fA-F]+)$'),
        ("gist_user", r'^/([^/]+)/?$'),

        # Archivo específico (blob)
        ("file", r'^/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$'),

        # Directorio (tree)
        ("directory", r'^/([^/]+)/([^/]+)/tree/([^/]+)/(.+)$'),

        # Compare (comparación de ramas)
        ("compare", r'^/([^/]+)/([^/]+)/compare/(.+)$'),

        # Tags
        ("tags", r'^/([^/]+)/([^/]+)/tags/?$'),

        # Branches
        ("branches", r'^/([^/]+)/([^/]+)/branches/?$'),

        # Commit
        ("commit", r'^/([^/]+)/([^/]+)/commit/([0-9a-f]+)$'),

        # Issues
        ("issue", r'^/([^/]+)/([^/]+)/issues/(\d+)$'),
        ("issues_list", r'^/([^/]+)/([^/]+)/issues/?$'),

        # Pull Requests
        ("pull_request", r'^/([^/]+)/([^/]+)/pull/(\d+)$'),
        ("pulls_list", r'^/([^/]+)/([^/]+)/pulls/?$'),

        # Releases
        ("release_tag", r'^/([^/]+)/([^/]+)/releases/tag/([^/]+)$'),
        ("releases_list", r'^/([^/]+)/([^/]+)/releases/?$'),

        # Wiki
        ("wiki_page", r'^/([^/]+)/([^/]+)/wiki/(.+)$'),
        ("wiki", r'^/([^/]+)/([^/]+)/wiki/?$'),

        # Projects
        ("project", r'^/([^/]+)/([^/]+)/projects/(\d+)$'),
        ("projects", r'^/([^/]+)/([^/]+)/projects/?$'),

        # Actions
        ("actions", r'^/([^/]+)/([^/]+)/actions/?$'),

        # Security
        ("security", r'^/([^/]+)/([^/]+)/security/?$'),

        # Repositorio general - DEBE IR AL FINAL
        ("repo", r'^/([^/]+)/([^/]+)/?$'),

        # Perfil de usuario
        ("profile", r'^/([^/]+)/?$'),
    ]

    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, username, repo, filename = self._extract_github_info(parsed_url)
        
        # Obtener emoji del mapeo
        emoji = EMOJI_MAPS['github'].get(content_type, '💻')
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': emoji,
            'username': username,
            'repo': repo,
            'filename': filename,
            'content_type': content_type
        }

    def _extract_github_info(self, parsed_url) -> Tuple[str, str, str, str]:
        """Extrae metadata de GitHub/Gist usando expresiones regulares"""
        path = parsed_url.path
        netloc = parsed_url.netloc
        content_type = ""
        username = ""
        repo = ""
        filename = ""

        # Determinar el tipo de dominio
        is_gist = 'gist.github.com' in netloc
        is_raw = 'raw.githubusercontent.com' in netloc

        # Verificar todos los patrones en orden
        for pattern_type, pattern in self.PATTERNS:
            # Saltar patrones que no corresponden al dominio actual
            if pattern_type.startswith('gist') and not is_gist:
                continue
            if pattern_type == 'raw' and not is_raw:
                continue
                
            match = re.match(pattern, path)
            if match:
                groups = match.groups()
                
                # Procesar según el tipo de patrón
                if pattern_type == 'raw':
                    username, repo, ref, filepath = groups
                    content_type = 'file'
                    filename = f"{ref}/{filepath}"
                    
                elif pattern_type == 'gist':
                    username, gist_id = groups
                    content_type = 'gist'
                    filename = gist_id
                    
                elif pattern_type == 'gist_user':
                    username = groups[0]
                    content_type = 'gist_list'
                    
                elif pattern_type == 'file':
                    username, repo, branch, filepath = groups
                    content_type = 'file'
                    filename = f"{branch}/{filepath}"
                    
                elif pattern_type == 'directory':
                    username, repo, branch, dirpath = groups
                    content_type = 'directory'
                    filename = f"{branch}/{dirpath}"
                    
                elif pattern_type in ('compare', 'tags', 'branches'):
                    username, repo = groups[0], groups[1]
                    content_type = 'repo'   
                    filename = ''
                    
                elif pattern_type == 'commit':
                    username, repo, commit_hash = groups
                    content_type = 'commit'
                    filename = commit_hash
                    
                elif pattern_type == 'issue':
                    username, repo, issue_num = groups
                    content_type = 'issue'
                    filename = issue_num
                    
                elif pattern_type == 'issues_list':
                    username, repo = groups
                    content_type = 'issue'
                    
                elif pattern_type == 'pull_request':
                    username, repo, pr_num = groups
                    content_type = 'pull_request'
                    filename = pr_num
                    
                elif pattern_type == 'pulls_list':
                    username, repo = groups
                    content_type = 'pull_request'
                    
                elif pattern_type == 'release_tag':
                    username, repo, tag = groups
                    content_type = 'release'
                    filename = f"tag/{tag}"
                    
                elif pattern_type == 'releases_list':
                    username, repo = groups
                    content_type = 'release'
                    
                elif pattern_type == 'wiki_page':
                    username, repo, page = groups
                    content_type = 'wiki'
                    filename = page
                    
                elif pattern_type == 'wiki':
                    username, repo = groups
                    content_type = 'wiki'
                    
                elif pattern_type == 'project':
                    username, repo, project_id = groups
                    content_type = 'project'
                    filename = project_id
                    
                elif pattern_type == 'projects':
                    username, repo = groups
                    content_type = 'project'
                    
                elif pattern_type == 'actions':
                    username, repo = groups
                    content_type = 'actions'
                    
                elif pattern_type == 'security':
                    username, repo = groups
                    content_type = 'security'
                    
                elif pattern_type == 'repo':
                    username, repo = groups
                    content_type = 'repo'
                    
                elif pattern_type == 'profile':
                    username = groups[0]
                    content_type = 'profile'
                    
                break

        return content_type, username, repo, filename

    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato de salida para GitHub"""
        emoji = data.get('emoji', '💻')
        username = data.get('username', '')
        repo = data.get('repo', '')
        filename = data.get('filename', '')
        content_type = data.get('content_type', '')

        # Construir la cadena de visualización
        username_display = f" de {username}" if username else ""
        repo_display = f"/{repo}" if repo else ""
        
        # Para tipos específicos, mostrar "Archivo: ...", para otros no mostrar nada
        if content_type in ['file', 'directory', 'commit', 'issue', 'pull_request', 
                          'release', 'wiki', 'project', 'gist', 'compare']:
            file_display = f" - Archivo: {filename}" if filename else ""
        else:
            file_display = ""

        # Mapear content_type a nombre legible
        type_names = {
            "file": "Archivo", "issue": "Issue", "pull_request": "Pull Request",
            "repo": "Repositorio", "profile": "Perfil", "directory": "Directorio",
            "commit": "Commit", "release": "Release", "wiki": "Wiki",
            "project": "Proyecto", "gist": "Gist", "gist_list": "Gists",
            "actions": "Actions", "security": "Security",
            "compare": "Comparación", "tags": "Tags", "branches": "Ramas"
        }

        type_display = type_names.get(content_type, "Contenido")

        return f"[{emoji} {type_display} de {self.SITE_NAME}{username_display}{repo_display}{file_display}]"