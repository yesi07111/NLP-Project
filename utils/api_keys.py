"""
Gestión de API Keys para servicios externos
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import dotenv

class APIKeyManager:
    """Gestor de API Keys para servicios externos"""
    
    def __init__(self):
        self.env_file = Path('.env')
        self.config_file = Path('config/api_keys.json')
        
        # Crear directorio config si no existe
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Cargar variables de entorno
        if self.env_file.exists():
            dotenv.load_dotenv(self.env_file)
    
    def save_google_ai_key(self, api_key: str) -> bool:
        """Guardar API key de Google AI"""
        try:
            # Guardar en .env
            lines = []
            key_found = False
            
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
            
            # Buscar y reemplazar GOOGLE_API_KEY
            for i, line in enumerate(lines):
                if line.strip().startswith('GOOGLE_API_KEY='):
                    lines[i] = f'GOOGLE_API_KEY={api_key}\n'
                    key_found = True
                    break
            
            # Si no se encontró, agregar
            if not key_found:
                lines.append(f'\nGOOGLE_API_KEY={api_key}\n')
            
            with open(self.env_file, 'w') as f:
                f.writelines(lines)
            
            # Actualizar variable de entorno
            os.environ['GOOGLE_API_KEY'] = api_key
            
            # Guardar también en archivo de configuración JSON
            self._save_to_config('google_ai', api_key)
            
            print(f"✅ API Key guardada en {self.env_file.absolute()}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando API key: {e}")
            return False
    
    def get_google_ai_key(self) -> Optional[str]:
        """Obtener API key de Google AI"""
        # Primero intentar variable de entorno
        key = os.getenv('GOOGLE_API_KEY')
        
        if key and key != 'your_google_api_key_here':
            return key
        
        # Intentar desde archivo de configuración
        config = self._load_config()
        return config.get('google_ai')
    
    def _save_to_config(self, service: str, api_key: str):
        """Guardar en archivo de configuración JSON"""
        try:
            config = self._load_config()
            config[service] = api_key
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error guardando en config.json: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración desde archivo JSON"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def test_google_ai_connection(self, api_key: Optional[str] = None) -> bool:
        """Probar conexión con Google AI"""
        try:
            import google.generativeai as genai
            
            key = api_key or self.get_google_ai_key()
            if not key:
                return False
            
            genai.configure(api_key=key)
            
            # Intentar listar modelos
            models = genai.list_models()
            
            # Verificar que hay modelos disponibles
            if len(list(models)) > 0:
                print("✅ Conexión con Google AI exitosa")
                return True
            else:
                print("⚠️ No se encontraron modelos disponibles")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión con Google AI: {e}")
            return False

# Instancia global
api_key_manager = APIKeyManager()