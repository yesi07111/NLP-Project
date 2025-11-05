from tests.base_tester import Tester, LinkProcessor

class LikeeTester(Tester):
    """Tester específico para enlaces de Likee"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Likee"""
        print("🎬 Ejecutando tests de Likee...")
        
        test_cases = [
            # Videos individuales
            ("https://likee.com/video/1234567890", "Video individual", "[🎬 Video - ID: 12345678...]"),
            ("https://www.likee.com/video/9876543210/", "Video con barra final", "[🎬 Video - ID: 98765432...]"),
            ("https://likee.com/video/1234567890/with/details", "Video con detalles adicionales", "[🏠 Inicio de Likee]"), # No coincide con patrón, cae en home
            
            # Perfiles de usuario
            ("https://likee.com/@username123", "Perfil de usuario básico", "[👤 Perfil de @username123]"),
            ("https://www.likee.com/@johndoe", "Perfil con www", "[👤 Perfil de @johndoe]"),
            ("https://likee.com/@username123/video", "Perfil - sección videos", "[🎬 Perfil - Videos de @username123]"),
            ("https://likee.com/@username123/like", "Perfil - me gusta", "[❤️ Perfil - Me gusta de @username123]"),
            ("https://likee.com/@username123/follower", "Perfil - seguidores", "[👥 Perfil - Seguidores de @username123]"),
            ("https://likee.com/@username123/following", "Perfil - siguiendo", "[👥 Perfil - Siguiendo de @username123]"),
            
            # Hashtags
            ("https://likee.com/hashtag/dance", "Hashtag simple", "[🏷️ Hashtag - ID: dance]"),
            ("https://www.likee.com/hashtag/funnyvideos", "Hashtag con www", "[🏷️ Hashtag - ID: funnyvid...]"), # Se acorta
            ("https://likee.com/hashtag/trending2024", "Hashtag trending", "[🏷️ Hashtag - ID: trending...]"), # Se acorta
            
            # Lives
            ("https://likee.com/live/username", "Transmisión en vivo", "[🔴 Transmisión en vivo de @username]"),
            ("https://www.likee.com/live/streamer123", "Live con www", "[🔴 Transmisión en vivo de @streamer123]"),
            
            # Trending
            ("https://likee.com/trending", "Trending principal", "[📈 Trending de Likee]"),
            ("https://likee.com/trending/dance", "Trending categoría específica", "[📈 Trending - ID: dance]"),
            ("https://www.likee.com/trending/comedy", "Trending con www", "[📈 Trending - ID: comedy]"),
            
            # Efectos
            ("https://likee.com/effect/123456", "Efecto específico", "[🎭 Efecto - ID: 123456]"),
            ("https://www.likee.com/effect/789012", "Efecto con www", "[🎭 Efecto - ID: 789012]"),
            
            # Música
            ("https://likee.com/music/555555", "Música específica", "[🎵 Música - ID: 555555]"),
            ("https://www.likee.com/music/666666", "Música con www", "[🎵 Música - ID: 666666]"),
            
            # Descubrir/Explorar
            ("https://likee.com/discover", "Descubrir principal", "[🔍 Descubrir de Likee]"),
            ("https://likee.com/explore", "Explorar principal", "[🔍 Descubrir de Likee]"), # explore también va a discover
            ("https://likee.com/discover/gaming", "Descubrir categoría gaming", "[🔍 Descubrir - ID: gaming]"),
            ("https://likee.com/explore/beauty", "Explorar categoría belleza", "[🔍 Descubrir - ID: beauty]"), # explore también va a discover
            
            # Notificaciones
            ("https://likee.com/notification", "Notificaciones", "[🔔 Notificaciones de Likee]"),
            ("https://www.likee.com/notification/", "Notificaciones con barra final", "[🔔 Notificaciones de Likee]"),
            
            # Mensajes
            ("https://likee.com/message", "Mensajes", "[💬 Mensajes de Likee]"),
            ("https://www.likee.com/message/", "Mensajes con www", "[💬 Mensajes de Likee]"),
            
            # Configuración
            ("https://likee.com/setting", "Configuración", "[⚙️ Configuración de Likee]"),
            ("https://www.likee.com/setting/", "Configuración con www", "[⚙️ Configuración de Likee]"),
            
            # Búsqueda
            ("https://likee.com/search", "Búsqueda principal", "[🔍 Búsqueda de Likee]"),
            ("https://likee.com/search?keyword=dance%20challenge", "Búsqueda con término keyword", "[🔍 Búsqueda: dance challenge]"),
            ("https://likee.com/search?q=funny", "Búsqueda con término q", "[🔍 Búsqueda: funny]"),
            ("https://www.likee.com/search", "Búsqueda con www", "[🔍 Búsqueda de Likee]"),
            
            # URLs complejas con parámetros
            ("https://likee.com/video/1234567890?shareId=abc123", "Video con parámetros", "[🎬 Video - ID: 12345678...]"),
            ("https://likee.com/@username123/video?sort=popular", "Perfil videos con parámetros", "[🎬 Perfil - Videos de @username123]"),
            ("https://likee.com/hashtag/dance?country=US", "Hashtag con parámetros", "[🏷️ Hashtag - ID: dance]"),
            
            # Página principal
            ("https://likee.com", "Página principal", "[🏠 Inicio de Likee]"),
            ("https://www.likee.com/", "Página principal con www", "[🏠 Inicio de Likee]"),
        ]
        
        for url, description, expected in test_cases:
            try:
                result = self.processor.process_url(url)
                
                # Verificar que el resultado es exactamente el esperado
                success = result == expected
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Likee - {description}", success, details)
                self.print_test_result(f"Likee - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Likee - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Likee - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = LikeeTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()