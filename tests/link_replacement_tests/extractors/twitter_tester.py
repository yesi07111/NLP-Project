# tests/twitter_tester.py
from tests.base_tester import Tester, LinkProcessor

class TwitterTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("🐦 Ejecutando tests de Twitter/X...")
        
        test_cases = [
            # Tweets
            ("https://twitter.com/username/status/1234567890", 
             "Tweet específico",
             "[🐦 Tweet de Twitter/X de @username - ID: 1234567890]"),
            
            ("https://www.twitter.com/johndoe/status/9876543210", 
             "Tweet con www",
             "[🐦 Tweet de Twitter/X de @johndoe - ID: 9876543210]"),
            
            ("https://x.com/username/status/5555555555", 
             "Tweet en x.com",
             "[🐦 Tweet de Twitter/X de @username - ID: 5555555555]"),
            
            ("https://www.x.com/janesmith/status/6666666666", 
             "Tweet x.com con www",
             "[🐦 Tweet de Twitter/X de @janesmith - ID: 6666666666]"),
            
            # Tweets con medios
            ("https://twitter.com/username/status/1234567890/photo/1", 
             "Tweet con foto",
             "[🖼️ Tweet con foto de Twitter/X de @username - ID: 1234567890]"),
            
            ("https://twitter.com/username/status/9876543210/video/1", 
             "Tweet con video",
             "[🎥 Tweet con video de Twitter/X de @username - ID: 9876543210]"),
            
            ("https://twitter.com/username/status/5555555555/retweets", 
             "Retweets del tweet",
             "[🔄 Retweets de Twitter/X de @username - ID: 5555555555]"),
            
            ("https://twitter.com/username/status/6666666666/likes", 
             "Likes del tweet",
             "[❤️ Likes de Twitter/X de @username - ID: 6666666666]"),
            
            # Perfiles
            ("https://twitter.com/username", 
             "Perfil de usuario",
             "[👤 Perfil de Twitter/X de @username]"),
            
            ("https://twitter.com/johndoe", 
             "Perfil John Doe",
             "[👤 Perfil de Twitter/X de @johndoe]"),
            
            ("https://x.com/username", 
             "Perfil en x.com",
             "[👤 Perfil de Twitter/X de @username]"),
            
            # Perfiles con secciones
            ("https://twitter.com/username/with_replies", 
             "Perfil con respuestas",
             "[💬 Perfil con respuestas de Twitter/X de @username]"),
            
            ("https://twitter.com/username/media", 
             "Perfil con medios",
             "[📸 Perfil con medios de Twitter/X de @username]"),
            
            ("https://twitter.com/username/likes", 
             "Perfil con likes",
             "[👍 Perfil con likes de Twitter/X de @username]"),
            
            ("https://twitter.com/username/following", 
             "Siguiendo",
             "[👀 Siguiendo de Twitter/X de @username]"),
            
            ("https://twitter.com/username/followers", 
             "Seguidores",
             "[👥 Seguidores de Twitter/X de @username]"),
            
            # Búsquedas
            ("https://twitter.com/search", 
             "Búsqueda principal",
             "[🔍 Búsqueda de Twitter/X]"),
            
            ("https://twitter.com/search?q=python", 
             "Búsqueda Python",
             "[🔍 Búsqueda de Twitter/X: python]"),
            
            ("https://twitter.com/i/search?q=javascript", 
             "Búsqueda interna JavaScript",
             "[🔍 Búsqueda de Twitter/X: javascript]"),
            
            # Mensajes
            ("https://twitter.com/messages", 
             "Mensajes",
             "[💌 Mensajes de Twitter/X]"),
            
            ("https://twitter.com/messages/123456", 
             "Conversación específica",
             "[💌 Mensajes de Twitter/X - ID: 123456]"),
            
            # Listas
            ("https://twitter.com/username/lists", 
             "Listas de usuario",
             "[📋 Lista de Twitter/X de @username]"),
            
            ("https://twitter.com/username/lists/123456", 
             "Lista específica",
             "[📋 Lista de Twitter/X de @username - ID: 123456]"),
            
            # Bookmarks y otras funcionalidades
            ("https://twitter.com/i/bookmarks", 
             "Marcadores",
             "[🔖 Marcadores de Twitter/X]"),
            
            ("https://twitter.com/explore", 
             "Explorar",
             "[🌐 Explorar de Twitter/X]"),
            
            ("https://twitter.com/explore/tabs/for-you", 
             "Explorar para ti",
             "[🌐 Explorar de Twitter/X - ID: for-you]"),
            
            ("https://twitter.com/explore/tabs/trending", 
             "Explorar tendencias",
             "[🌐 Explorar de Twitter/X - ID: trending]"),
            
            ("https://twitter.com/i/trends", 
             "Tendencias",
             "[📈 Tendencias de Twitter/X]"),
            
            ("https://twitter.com/notifications", 
             "Notificaciones",
             "[🔔 Notificaciones de Twitter/X]"),
            
            ("https://twitter.com/i/communities", 
             "Comunidades",
             "[🏘️ Comunidades de Twitter/X]"),
            
            ("https://twitter.com/i/communities/123456", 
             "Comunidad específica",
             "[🏘️ Comunidades de Twitter/X - ID: 123456]"),
            
            ("https://twitter.com/i/moments", 
             "Moments",
             "[⭐ Moments de Twitter/X]"),
            
            ("https://twitter.com/i/moments/123456", 
             "Moment específico",
             "[⭐ Moments de Twitter/X - ID: 123456]"),
            
            # Enlaces cortos
            ("https://t.co/abc123", 
             "Enlace corto t.co",
             "[🔗 Enlace corto de Twitter/X]"),
            
            ("https://t.co/def456", 
             "Otro enlace corto",
             "[🔗 Enlace corto de Twitter/X]"),
            
            # Configuración
            ("https://twitter.com/settings", 
             "Configuración",
             "[⚙️ Configuración de Twitter/X]"),
            
            ("https://twitter.com/settings/account", 
             "Configuración cuenta",
             "[👤 Configuración de cuenta de Twitter/X]"),
            
            ("https://twitter.com/settings/privacy", 
             "Configuración privacidad",
             "[🛡️ Configuración de privacidad de Twitter/X]"),
            
            ("https://twitter.com/settings/display", 
             "Configuración pantalla",
             "[🖥️ Configuración de pantalla de Twitter/X]"),
            
            # Composición y autenticación
            ("https://twitter.com/compose/tweet", 
             "Componer tweet",
             "[✍️ Componer tweet de Twitter/X]"),
            
            ("https://twitter.com/i/flow/login", 
             "Login",
             "[🔑 Inicio de sesión de Twitter/X]"),
            
            ("https://twitter.com/i/flow/signup", 
             "Registro",
             "[📝 Registro de Twitter/X]"),
            
            ("https://twitter.com/logout", 
             "Logout",
             "[🚪 Cerrar sesión de Twitter/X]"),
            
            # Información
            ("https://twitter.com/about", 
             "Acerca de",
             "[ℹ️ Acerca de de Twitter/X]"),
            
            ("https://twitter.com/tos", 
             "Términos de servicio",
             "[📜 Términos de servicio de Twitter/X]"),
            
            ("https://twitter.com/privacy", 
             "Privacidad",
             "[🔒 Privacidad de Twitter/X]"),
            
            ("https://twitter.com/help", 
             "Ayuda",
             "[❓ Ayuda de Twitter/X]"),
            
            # Hashtags y contenido especial
            ("https://twitter.com/hashtag/python", 
             "Hashtag Python",
             "[#️⃣ Hashtag de Twitter/X #python]"),
            
            ("https://twitter.com/hashtag/JavaScript", 
             "Hashtag JavaScript",
             "[#️⃣ Hashtag de Twitter/X #JavaScript]"),
            
            ("https://twitter.com/i/events/123456", 
             "Evento",
             "[🎉 Evento de Twitter/X - ID: 123456]"),
            
            ("https://twitter.com/i/spaces/123456", 
             "Spaces",
             "[🎤 Space de Twitter/X - ID: 123456]"),
            
            ("https://twitter.com/i/grok", 
             "Grok",
             "[🤖 Grok de Twitter/X]"),
            
            ("https://twitter.com/i/premium", 
             "Premium",
             "[💎 Premium de Twitter/X]"),
            
            # Página principal
            ("https://twitter.com", 
             "Página principal",
             "[🏠 Inicio de Twitter/X]"),
            
            ("https://x.com", 
             "Página principal x.com",
             "[🏠 Inicio de Twitter/X]"),
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
                
                self.add_test_result(f"Twitter - {description}", success, details)
                self.print_test_result(f"Twitter - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Twitter - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Twitter - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = TwitterTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()