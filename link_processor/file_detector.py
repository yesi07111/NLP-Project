import re
from typing import Dict

class FileTypeDetector:
    def __init__(self):
        self.file_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.webm'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.xlsx'],
            'compressed': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'executable': ['.exe', '.msi', '.dmg', '.pkg', '.deb'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp']
        }
        
        self.spanish_names = {
            'image': '🖼️ Imagen', 'video': '🎥 Video', 'audio': '🔊 Audio',
            'document': '📄 Documento', 'compressed': '📦 Archivo comprimido',
            'executable': '⚙️ Ejecutable', 'code': '💻 Código fuente'
        }
        
        # Patrones regex para exclusiones específicas
        self.excluded_domains = [
            r'media\.discordapp\.net',
            r'cdn\.discordapp\.com', 
            r'discord\.gg',
            r'discord\.com',
            r'github\.com',
            r'gist\.github\.com',
            r'raw\.githubusercontent\.com',
            r'gitlab\.com',
            r'google\.com',
            r'gmail\.com',
            r'drive\.google\.com',
            r'docs\.google\.com',
            r'maps\.google\.com',
            r'photos\.google\.com',
            r'calendar\.google\.com',
            r'meet\.google\.com',
            r'classroom\.google\.com',
            r'sites\.google\.com',
            r'keep\.google\.com',
            r'scholar\.google\.com',
            r'play\.google\.com',
            r'news\.google\.com',
            r'myaccount\.google\.com',
            r'translate\.google\.com',
            r'earth\.google\.com',
            r'takeout\.google\.com',
            r'contacts\.google\.com',
            r'goo\.gl',
            r'g\.co',
            r'imgur\.com',
            r'i\.imgur\.com'
        ]
        
        # Patrón regex para detectar extensiones de archivo
        self.extension_pattern = re.compile(r'\.([a-zA-Z0-9]+)(?:\?.*)?$')
    
    def should_ignore_domain(self, url: str) -> bool:
        """Verifica si la URL pertenece a un dominio que debe ser ignorado"""
        for pattern in self.excluded_domains:
            if re.search(pattern, url):
                return True
        return False
    
    def get_file_type(self, url: str) -> Dict[str, str]:
        """Detecta el tipo de archivo usando regex y retorna información"""
        
        # Ignorar dominios específicos como Discord
        if self.should_ignore_domain(url):
            return {'type': 'unknown'}
        
        # Extraer el nombre del archivo de la URL
        filename = url.split('/')[-1] if '/' in url else 'sin_nombre'
        
        # Buscar extensión usando regex
        match = self.extension_pattern.search(url)
        if not match:
            return {'type': 'unknown'}
        
        file_extension = '.' + match.group(1).lower()
        
        # Verificar el tipo de archivo
        for file_type, extensions in self.file_extensions.items():
            if file_extension in extensions:
                return {
                    'type': file_type,
                    'display_name': self.spanish_names.get(file_type, '📎 Archivo'),
                    'filename': filename
                }
        
        return {'type': 'unknown'}
    
    def format_file_output(self, file_info: Dict[str, str]) -> str:
        """Formatea la salida para archivos"""
        if file_info['type'] == 'unknown':
            return ""
        return f"[{file_info['display_name']}: {file_info['filename']}]"