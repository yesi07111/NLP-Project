# tests/tumblr_tester.py
from tests.base_tester import Tester, LinkProcessor

class TumblrTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("📝 Ejecutando tests de Tumblr...")
        
        test_cases = [
            # Posts con subdominio
            ("https://username.tumblr.com/post/1234567890/title-slug", 
             "Post con subdominio",
             "[📝 Post de Tumblr - de username, ID: 1234567890]"),
            
            ("https://johndoe.tumblr.com/post/9876543210/another-title", 
             "Post otro usuario",
             "[📝 Post de Tumblr - de johndoe, ID: 9876543210]"),
            
            # Posts con tipos específicos
            ("https://blogname.tumblr.com/post/5555555555/photo-post/photo/1", 
             "Post foto",
             "[🖼️ Foto de Tumblr - de blogname, ID: 5555555555]"),
            
            ("https://username.tumblr.com/post/6666666666/video-post/video/1", 
             "Post video",
             "[🎥 Video de Tumblr - de username, ID: 6666666666]"),
            
            ("https://username.tumblr.com/post/7777777777/audio-post/audio/1", 
             "Post audio",
             "[🔊 Audio de Tumblr - de username, ID: 7777777777]"),
            
            # Todos los posts regulares (texto, cita, enlace, chat, respuesta) ahora son "Post"
            ("https://username.tumblr.com/post/8888888888/text-post", 
             "Post texto",
             "[📝 Post de Tumblr - de username, ID: 8888888888]"),
            
            ("https://username.tumblr.com/post/9999999999/quote-post", 
             "Post cita",
             "[📝 Post de Tumblr - de username, ID: 9999999999]"),
            
            ("https://username.tumblr.com/post/1111111111/link-post", 
             "Post enlace",
             "[📝 Post de Tumblr - de username, ID: 1111111111]"),
            
            ("https://username.tumblr.com/post/2222222222/chat-post", 
             "Post chat",
             "[📝 Post de Tumblr - de username, ID: 2222222222]"),
            
            ("https://username.tumblr.com/post/3333333333/answer-post", 
             "Post respuesta",
             "[📝 Post de Tumblr - de username, ID: 3333333333]"),
            
            # Etiquetas
            ("https://username.tumblr.com/tagged/python", 
             "Etiqueta Python",
             "[🏷️ Etiqueta de Tumblr - de username, #python]"),
            
            ("https://username.tumblr.com/tagged/art", 
             "Etiqueta arte",
             "[🏷️ Etiqueta de Tumblr - de username, #art]"),
            
            ("https://username.tumblr.com/tagged/photo", 
             "Etiqueta foto",
             "[🏷️ Etiqueta de Tumblr - de username, #photo]"),
            
            # Secciones de blog
            ("https://username.tumblr.com/archive", 
             "Archivo",
             "[📚 Archivo de Tumblr - de username]"),
            
            ("https://username.tumblr.com/likes", 
             "Likes",
             "[❤️ Likes de Tumblr - de username]"),
            
            ("https://username.tumblr.com/followers", 
             "Seguidores",
             "[👥 Seguidores de Tumblr - de username]"),
            
            ("https://username.tumblr.com/following", 
             "Siguiendo",
             "[👥 Siguiendo de Tumblr - de username]"),
            
            # Dashboard y subsecciones
            ("https://username.tumblr.com/dashboard", 
             "Dashboard",
             "[📊 Dashboard de Tumblr - de username]"),
            
            ("https://username.tumblr.com/dashboard/queue", 
             "Cola del dashboard",
             "[⏳ Cola de Tumblr - de username]"),
            
            ("https://username.tumblr.com/dashboard/drafts", 
             "Borradores",
             "[📝 Borradores de Tumblr - de username]"),
            
            ("https://username.tumblr.com/dashboard/activity", 
             "Actividad",
             "[📈 Actividad de Tumblr - de username]"),
            
            # Búsquedas
            ("https://tumblr.com/search?q=python", 
             "Búsqueda Python",
             "[🔍 Búsqueda: python]"),
            
            ("https://tumblr.com/search?q=art", 
             "Búsqueda arte",
             "[🔍 Búsqueda: art]"),
            
            # Mensajes
            ("https://username.tumblr.com/messages", 
             "Mensajes",
             "[💬 Mensajes de Tumblr - de username]"),
            
            ("https://username.tumblr.com/messages/inbox", 
             "Bandeja de entrada",
             "[📨 Bandeja de entrada de Tumblr - de username]"),
            
            ("https://username.tumblr.com/messages/sent", 
             "Mensajes enviados",
             "[📤 Mensajes enviados de Tumblr - de username]"),
            
            # Configuración
            ("https://username.tumblr.com/settings", 
             "Configuración",
             "[⚙️ Configuración de Tumblr - de username]"),
            
            ("https://username.tumblr.com/settings/account", 
             "Configuración cuenta",
             "[👤 Configuración de cuenta de Tumblr - de username]"),
            
            ("https://username.tumblr.com/settings/blog", 
             "Configuración blog",
             "[📝 Configuración de blog de Tumblr - de username]"),
            
            ("https://username.tumblr.com/settings/appearance", 
             "Apariencia",
             "[🎨 Apariencia de Tumblr - de username]"),
            
            # Blog oficial de Tumblr
            ("https://tumblr.com/blog", 
             "Blog de Tumblr",
             "[📰 Blog de Tumblr]"),
            
            ("https://tumblr.com/blog/announcement", 
             "Post del blog",
             "[📰 Blog de Tumblr - Post: announcement]"),
            
            # Explorar
            ("https://tumblr.com/explore", 
             "Explorar",
             "[🔍 Explorar de Tumblr]"),
            
            ("https://tumblr.com/explore/art", 
             "Explorar arte",
             "[🔍 Explorar de Tumblr - Categoría: art]"),
            
            ("https://tumblr.com/explore/photography", 
             "Explorar fotografía",
             "[🔍 Explorar de Tumblr - Categoría: photography]"),
            
            # Otras secciones
            ("https://tumblr.com/trending", 
             "Trending",
             "[📈 Trending de Tumblr]"),
            
            ("https://tumblr.com/staff", 
             "Staff",
             "[👥 Staff de Tumblr]"),
            
            ("https://tumblr.com/policy", 
             "Política",
             "[📄 Política de Tumblr]"),
            
            ("https://tumblr.com/privacy", 
             "Privacidad",
             "[🔒 Política de privacidad de Tumblr]"),
            
            ("https://tumblr.com/terms", 
             "Términos de servicio",
             "[📋 Términos de servicio de Tumblr]"),
            
            ("https://tumblr.com/help", 
             "Ayuda",
             "[🛟 Ayuda de Tumblr]"),
            
            ("https://tumblr.com/help/getting-started", 
             "Ayuda empezar",
             "[🛟 Ayuda de Tumblr - Artículo: getting-started]"),
            
            ("https://tumblr.com/developers", 
             "Desarrolladores",
             "[💻 Desarrolladores de Tumblr]"),
            
            ("https://tumblr.com/developers/api", 
             "API desarrolladores",
             "[📚 Documentación API de Tumblr]"),
            
            ("https://tumblr.com/app", 
             "App",
             "[📱 App de Tumblr]"),
            
            # Páginas principales
            ("https://username.tumblr.com", 
             "Blog principal",
             "[🏠 Blog principal de Tumblr - de username]"),
            
            ("https://username.tumblr.com/", 
             "Blog principal con barra",
             "[🏠 Blog principal de Tumblr - de username]"),
            
            ("https://tumblr.com", 
             "Tumblr principal",
             "[🏠 Tumblr principal de Tumblr]"),
            
            ("https://tumblr.com/", 
             "Tumblr principal con barra",
             "[🏠 Tumblr principal de Tumblr]"),
            
            # Secciones adicionales de blog
            ("https://username.tumblr.com/about", 
             "Acerca de",
             "[ℹ️ Acerca de de Tumblr - de username]"),
            
            ("https://username.tumblr.com/theme", 
             "Tema",
             "[🎨 Tema de Tumblr - de username]"),
            
            ("https://username.tumblr.com/avatar", 
             "Avatar",
             "[👤 Avatar de Tumblr - de username]"),
            
            # Posts con diferentes formatos de URL
            ("https://www.tumblr.com/username/post/1234567890", 
             "Post con www",
             "[📝 Post de Tumblr - de username, ID: 1234567890]"),
            
            ("https://tumblr.com/username/post/9876543210", 
             "Post sin subdominio",
             "[📝 Post de Tumblr - de username, ID: 9876543210]"),
        ]
        
        for url, description, expected in test_cases:
            try:
                result = self._process_url(url)
                success = result == expected
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Tumblr - {description}", success, details)
                self.print_test_result(f"Tumblr - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Tumblr - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Tumblr - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = TumblrTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()