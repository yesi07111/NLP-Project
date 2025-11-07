# 🔗 Link Replacement System

Un sistema inteligente para reemplazar enlaces de redes sociales y archivos por representaciones legibles con emojis, diseñado para mejorar la legibilidad en chats y mensajes.

## 🎯 **¿Qué hace este proyecto?**

Convierte enlaces largos y complejos en representaciones visuales claras:

**Antes:**
```
https://www.instagram.com/p/Cxample123/?utm_source=ig_web_copy_link
https://amazon.com/dp/B08N5WRWNW?ref=ppx_yo2ov_dt_b_product_details
https://cdn.discordapp.com/attachments/123/456/image.png
```

**Después:**
```
[📸 Post de Instagram de @usuario]
[🛒 Producto de Amazon - ID: B08N5WRWNW]
[🖼️ Imagen: image.png]
```

## 🏗️ **Arquitectura del Sistema**

### 📁 **Estructura de Carpetas**

```
link_replacement/
├── main.py                 # 🎯 Procesador principal de enlaces
├── file_detector.py        # 📁 Detector de tipos de archivo
├── utils/
│   ├── constants.py        # 🎨 Emojis y configuraciones
│   └── parse_url.py        # 🔗 Utilidades para parseo de URLs
└── extractors/
    ├── base.py             # 🏗️ Clase base para extractores
    ├── amazon.py           # 🛒 Extractores de Amazon
    ├── instagram.py        # 📸 Extractores de Instagram
    ├── youtube.py          # 📹 Extractores de YouTube
    └── ... (+20 extractores más)
```

### 🔧 **Componentes Principales**

#### 1. **`LinkProcessor`** (main.py)
- **Función**: Coordina todo el proceso de reemplazo
- **Métodos clave**:
  - `replace_link()`: Para uso con `re.sub()`
  - `process_url()`: Para procesamiento directo

#### 2. **`FileTypeDetector`** (file_detector.py)
- **Función**: Detecta y clasifica archivos por extensión
- **Soporta**: Imágenes, videos, audio, documentos, comprimidos, ejecutables, código
- **Excluye**: Dominios específicos (Discord, GitHub, Google, etc.)

#### 3. **Sistema de Extractores** (extractors/)
- **Base**: `BaseExtractor` - Clase abstracta con registro global
- **Especializados**: +20 extractores para diferentes plataformas
- **Registro Automático**: Decorador `@register_extractor`

## 🚀 **Características Principales**

### 🔍 **Detección Inteligente**
- **+20 Plataformas** soportadas (Redes sociales, tiendas, herramientas)
- **Tipos de archivo** con detección por extensión
- **Exclusiones inteligentes** para dominios específicos

### 🎨 **Representación Visual**
- **Emojis específicos** por plataforma y tipo de contenido
- **Nombres en español** para mejor comprensión
- **Información contextual** (usuarios, IDs, categorías)

### ⚡ **Fácil Integración**
```python
processor = LinkProcessor()
texto_procesado = re.sub(r'https?://[^\s]+', processor.replace_link, texto_original)
```

## 📋 **Plataformas Soportadas**

### 🛒 **Comercio Electrónico**
- **Amazon**: Productos, búsquedas, ofertas, wishlists
- **eBay**: Subastas, productos, vendedores

### 📱 **Redes Sociales**
- **Instagram**: Posts, stories, reels, perfiles
- **Facebook**: Publicaciones, fotos, videos, grupos
- **Twitter/X**: Tweets, hilos, perfiles, momentos
- **TikTok**: Videos, perfiles, sonidos
- **LinkedIn**: Publicaciones, perfiles, empresas

### 🎵 **Entretenimiento**
- **YouTube**: Videos, canales, listas, shorts
- **Spotify**: Canciones, álbumes, playlists, artistas
- **Twitch**: Streams, clips, canales

### 💼 **Profesionales**
- **GitHub**: Repositorios, gists, perfiles, issues
- **GitLab**: Proyectos, merge requests, snippets
- **Stack Overflow**: Preguntas, respuestas, usuarios

### 📹 **Multimedia**
- **Imgur**: Imágenes, álbumes, galerías
- **Flickr**: Fotos, álbumes, grupos
- **Pinterest**: Pins, tableros, perfiles

### 💬 **Mensajería**
- **Discord**: Canales, servidores, mensajes
- **WhatsApp**: Chats, grupos, estados
- **Telegram**: Canales, grupos, stickers

## 🛠️ **Uso Rápido**

### 📦 **Instalación**
```python
# Clona el proyecto y usa los módulos directamente
from link_replacement.main import LinkProcessor
```

### 🔧 **Ejemplos de Uso**

```python
import re
from link_replacement.main import LinkProcessor

# Inicializar el procesador
processor = LinkProcessor()

# Ejemplo 1: Procesar texto con múltiples enlaces
texto = """
Mira este producto: https://amazon.com/dp/B08N5WRWNW
Y este video: https://youtube.com/watch?v=dQw4w9WgXcQ
También mi perfil: https://instagram.com/usuario
"""

texto_procesado = re.sub(r'https?://[^\s]+', processor.replace_link, texto)
print(texto_procesado)
```

**Salida:**
```
Mira este producto: [🛒 Producto de Amazon - ID: B08N5WRWNW]
Y este video: [📹 Video de YouTube - ID: dQw4w9WgXcQ]
También mi perfil: [👤 Perfil de Instagram de @usuario]
```

### 🎯 **Uso Avanzado**

```python
# Procesar una URL directamente
url = "https://github.com/usuario/repo/issues/123"
resultado = processor.process_url(url)
print(resultado)  # [🐙 Issue de GitHub - Repo: usuario/repo - #123]

# Integración con sistemas de chat
def procesar_mensaje_chat(mensaje):
    return re.sub(r'https?://[^\s]+', processor.replace_link, mensaje)
```

## 🔬 **Sistema de Extractores**

### 🏗️ **Estructura de un Extractor**

```python
@register_extractor
class MiPlataformaExtractor(BaseExtractor):
    DOMAINS = ['miplataforma.com', 'www.miplataforma.com']
    SITE_NAME = 'Mi Plataforma'
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict]:
        # Lógica de extracción específica
        return {
            'site_name': self.SITE_NAME,
            'emoji': '🎯',
            'content_type': 'contenido',
            'username': 'usuario',
            'content_id': '123'
        }
```

### 🔍 **Métodos Clave**

- `can_handle()`: Determina si el extractor puede procesar el dominio
- `extract()`: Extrae metadata de la URL (OBLIGATORIO)
- `format_output()`: Formatea la salida (opcional, tiene default)

## 🧪 **Testing Completo**

### ✅ **Sistema de Tests**
```python
from tests.link_replacement_tests import PlatformTester

# Ejecutar todos los tests
tester = PlatformTester(verbose=True)
tester.run_all_tests()
tester.print_summary()
```

### 📊 **Cobertura de Tests**
- **+20 testers específicos** por plataforma
- **Validación de patrones** regex
- **Verificación de emojis** y formatos
- **Manejo de edge cases**

## 🎨 **Personalización**

### 🔧 **Agregar Nuevas Plataformas**

1. **Crear extractor** en `extractors/nueva_plataforma.py`
2. **Registrar** con `@register_extractor`
3. **Definir** `DOMAINS` y `SITE_NAME`
4. **Implementar** método `extract()`

### 🎨 **Modificar Emojis**

Editar `utils/constants.py`:

```python
EMOJI_MAPS = {
    'nueva_plataforma': {
        'profile': '👤',
        'post': '📝',
        # ...
    }
}
```

## 📈 **Casos de Uso**

### 💬 **Aplicaciones de Chat**
- Mejorar legibilidad de mensajes
- Reducir espacio ocupado por URLs largas
- Proporcionar contexto inmediato

### 📊 **Análisis de Conversaciones**
- Clasificación automática de enlaces compartidos
- Métricas de engagement por tipo de contenido
- Detección de patrones de compartir

### 🛡️ **Seguridad**
- Ocultar URLs potencialmente maliciosas
- Proporcionar información sin hacer clic
- Prevenir phishing mostrando el destino real

## 🔧 **Configuración Avanzada**

### 📁 **Tipos de Archivo Soportados**

El `FileTypeDetector` soporta:

| Tipo | Extensiones | Emoji |
|------|-------------|--------|
| Imagen | .jpg, .png, .gif, .webp | 🖼️ |
| Video | .mp4, .avi, .mov, .webm | 🎥 |
| Audio | .mp3, .wav, .flac, .m4a | 🔊 |
| Documento | .pdf, .doc, .txt, .xlsx | 📄 |
| Comprimido | .zip, .rar, .7z | 📦 |
| Ejecutable | .exe, .msi, .dmg | ⚙️ |
| Código | .py, .js, .html, .java | 💻 |

### 🚫 **Dominios Excluidos**

Algunos dominios son excluidos automáticamente:
- **Discord** (cdn.discordapp.com, media.discordapp.net)
- **Google** (drive.google.com, docs.google.com, etc.)
- **GitHub** (github.com, gist.github.com)

## 🤝 **Contribuir**

### 🐛 **Reportar Issues**
- Especificar la URL que no se procesa correctamente
- Incluir el resultado esperado vs actual
- Plataforma y tipo de contenido

### 💡 **Agregar Plataformas**
1. Crear extractor en `extractors/`
2. Agregar tests en `tests/`
3. Actualizar emojis en `utils/constants.py`

---

**¿Listo para hacer tus enlaces más legibles?** 🚀