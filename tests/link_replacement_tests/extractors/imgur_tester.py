from tests.base_tester import Tester, LinkProcessor

class ImgurTester(Tester):
    """Tester específico para enlaces de Imgur"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Imgur"""
        print("🧪 Ejecutando tests de Imgur...")
        
        test_cases = [
            # Imágenes individuales
            ("https://imgur.com/a1b2c3d4", "Imagen individual", "[🖼️ Imagen - ID: a1b2c3d4]"),
            ("https://imgur.com/gallery/abc123", "Galería de imagen", "[🖼️ Galería - ID: abc123]"),
            ("https://imgur.com/a1b2c3d4.jpg", "Imagen con extensión", "[🖼️ Imagen - ID: a1b2c3d4]"),
            ("https://imgur.com/a1b2c3d4.png", "Imagen PNG", "[🖼️ Imagen - ID: a1b2c3d4]"),
            ("https://imgur.com/a1b2c3d4.gif", "GIF", "[🖼️ Imagen - ID: a1b2c3d4]"),
            
            # Álbumes
            ("https://imgur.com/a/album123", "Álbum completo", "[📚 Álbum - ID: album123]"),
            ("https://imgur.com/a/album456/", "Álbum con barra final", "[📚 Álbum - ID: album456]"),
            ("https://imgur.com/a/def789", "Álbum corto", "[📚 Álbum - ID: def789]"),
            
            # Galerías
            ("https://imgur.com/gallery/longalbumid123", "Galería larga", "[🖼️ Galería - ID: longalbum...]"),
            ("https://imgur.com/gallery/shortid", "Galería corta", "[🖼️ Galería - ID: shortid]"),
            ("https://imgur.com/gallery/xyz789/", "Galería con barra final", "[🖼️ Galería - ID: xyz789]"),
            
            # Temas/topics
            ("https://imgur.com/topic/funny", "Tema Funny", "[🏷️ Tema - ID: funny]"),
            ("https://imgur.com/topic/gaming", "Tema Gaming", "[🏷️ Tema - ID: gaming]"),
            ("https://imgur.com/topic/aww", "Tema Aww", "[🏷️ Tema - ID: aww]"),
            ("https://imgur.com/topic/memes", "Tema Memes", "[🏷️ Tema - ID: memes]"),
            ("https://imgur.com/topic/art", "Tema Art", "[🏷️ Tema - ID: art]"),
            ("https://imgur.com/topic/tech", "Tema Tech", "[🏷️ Tema - ID: tech]"),
            
            # Página principal y secciones
            ("https://imgur.com/", "Página principal", "[🏠 Inicio]"),
            ("https://imgur.com/popular", "Popular", "[🔥 Popular]"),
            ("https://imgur.com/t", "Tendencias", "[📈 Tendencias]"),
            ("https://imgur.com/new", "Nuevo", "[🆕 Nuevo]"),
            ("https://imgur.com/hot", "Hot", "[🌶️ Hot]"),
            ("https://imgur.com/rising", "Rising", "[⬆️ Rising]"),
            
            # Usuarios
            ("https://imgur.com/user/johndoe", "Perfil de usuario", "[👤 Usuario - ID: johndoe]"),
            ("https://imgur.com/user/janesmith/posts", "Posts de usuario", "[📝 Posts de Usuario - ID: janesmith]"),
            ("https://imgur.com/user/bobross/comments", "Comentarios de usuario", "[💬 Comentarios de Usuario - ID: bobross]"),
            ("https://imgur.com/user/artlover/favorites", "Favoritos de usuario", "[⭐ Favoritos de Usuario - ID: artlover]"),
            
            # Búsquedas
            ("https://imgur.com/search?q=cats", "Búsqueda de gatos", "[🔍 Búsqueda: cats]"),
            ("https://imgur.com/search?q=funny+meme", "Búsqueda con espacios", "[🔍 Búsqueda: funny meme]"),
            
            # Meme Generator
            ("https://imgur.com/memegen", "Meme Generator", "[😂 Meme Generator]"),
            ("https://imgur.com/memegen/top-text/bottom-text", "Meme con texto", "[😂 Meme Generator: top-text/bottom-text]"),
            
            # Subir
            ("https://imgur.com/upload", "Subir imagen", "[📤 Subir]"),
            
            # Imágenes en posts
            ("https://imgur.com/a1b2c3d4?r", "Imagen con parámetro", "[🖼️ Imagen - ID: a1b2c3d4]"),
            ("https://imgur.com/gallery/abc123?c=1", "Galería con comentarios", "[🖼️ Galería - ID: abc123]"),
            
            # URLs con formato antiguo
            ("https://i.imgur.com/a1b2c3d4.jpg", "Subdominio i.imgur.com", "[🖼️ Imagen - ID: a1b2c3d4]"),
            ("https://i.imgur.com/abc123.gifv", "GIFV format", "[🖼️ Imagen - ID: abc123]"),
            ("https://i.imgur.com/def456.mp4", "Video MP4", "[🖼️ Imagen - ID: def456]"),
            ("https://i.imgur.com/xyz789", "Directo sin extensión", "[🖼️ Imagen - ID: xyz789]"),
            
            # Posts de comentarios
            ("https://imgur.com/r/funny/a1b2c3d4", "Post en subreddit", "[🔗 Post en Subreddit en r/funny - ID: a1b2c3d4]"),
            ("https://imgur.com/t/memes/xyz789", "Post en tema específico", "[🖼️ Imagen - ID: xyz789]"),
            
            # Colecciones
            ("https://imgur.com/collection/12345", "Colección", "[📂 Colección - ID: 12345]"),
            
            # Notificaciones
            ("https://imgur.com/notifications", "Notificaciones", "[🔔 Notificaciones]"),
            
            # Mensajes
            ("https://imgur.com/messages", "Mensajes", "[✉️ Mensajes]"),
            
            # Configuración
            ("https://imgur.com/account/settings", "Configuración de cuenta", "[⚙️ Configuración]"),
            
            # Ayuda
            ("https://imgur.com/help", "Ayuda", "[❓ Ayuda]"),
            
            # Términos y políticas
            ("https://imgur.com/tos", "Términos de servicio", "[📜 Términos de Servicio]"),
            ("https://imgur.com/privacy", "Política de privacidad", "[🔒 Privacidad]"),
            
            # App móvil
            ("https://imgur.com/app", "App móvil", "[📱 App Móvil]"),
            
            # Tienda
            ("https://imgur.com/store", "Tienda de Imgur", "[🛍️ Tienda]"),
        ]
        
        for url, description, expected in test_cases:
            try:
                result = self.processor.process_url(url)
                success = result.strip() == expected.strip()
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected,
                    'Coincide': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Imgur - {description}", success, details)
                self.print_test_result(f"Imgur - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Imgur - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Imgur - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = ImgurTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()