from tests.base_tester import Tester, LinkProcessor

class InstagramTester(Tester):
    """Tester específico para enlaces de Instagram"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Instagram"""
        print("🧪 Ejecutando tests de Instagram...")
        
        test_cases = [
            # Perfiles de usuario
            ("https://instagram.com/johndoe", "Perfil básico", "[👤 Perfil de @johndoe]"),
            ("https://www.instagram.com/janesmith/", "Perfil con www y barra", "[👤 Perfil de @janesmith]"),
            ("https://instagram.com/_u/johndoe", "Perfil con formato _u", "[👤 Perfil de @johndoe]"),
            
            # Posts individuales (IDs se acortan a 8 caracteres + ...)
            ("https://instagram.com/p/ABC123def45/", "Post individual", "[📸 Publicación - ID: ABC123de...]"),
            ("https://www.instagram.com/p/DEF456ghi78/", "Post con www", "[📸 Publicación - ID: DEF456gh...]"),
            ("https://instagram.com/p/1a2b3c4d5e/", "Post corto", "[📸 Publicación - ID: 1a2b3c4d...]"),
            
            # Reels (IDs se acortan a 8 caracteres + ...)
            ("https://instagram.com/reel/ABC123def45/", "Reel", "[📹 Reel - ID: ABC123de...]"),
            ("https://www.instagram.com/reel/DEF456ghi78/", "Reel con www", "[📹 Reel - ID: DEF456gh...]"),
            
            # Stories
            ("https://instagram.com/stories/johndoe/1234567890/", "Story de usuario", "[📱 Historia de @johndoe - ID: 12345678...]"),
            ("https://www.instagram.com/stories/janesmith/9876543210/", "Story con www", "[📱 Historia de @janesmith - ID: 98765432...]"),
            
            # Highlights
            ("https://instagram.com/stories/highlights/12345678901234567/", "Highlight", "[🌟 Highlight - ID: 12345678...]"),
            ("https://www.instagram.com/stories/highlights/98765432109876543/", "Highlight con www", "[🌟 Highlight - ID: 98765432...]"),
            
            # Guides
            ("https://instagram.com/johndoe/guide/1234567890/", "Guide de usuario", "[📚 Guía de @johndoe - ID: 12345678...]"),
            ("https://www.instagram.com/janesmith/guide/9876543210/", "Guide con www", "[📚 Guía de @janesmith - ID: 98765432...]"),
            
            # Explore
            ("https://instagram.com/explore", "Explore principal", "[🔍 Explorar de Instagram]"),
            ("https://www.instagram.com/explore/", "Explore con barra", "[🔍 Explorar de Instagram]"),
            ("https://instagram.com/explore/people", "Explore People", "[👥 Explorar Personas de Instagram]"),
            ("https://instagram.com/explore/places", "Explore Places", "[🗺️ Explorar Lugares de Instagram]"),
            
            # Locations (IDs se acortan a 8 caracteres + ...)
            ("https://instagram.com/explore/locations/123456789/", "Location", "[📍 Ubicación - ID: 12345678...]"),
            ("https://www.instagram.com/explore/locations/987654321/", "Location con www", "[📍 Ubicación - ID: 98765432...]"),
            
            # Hashtags (algunos se acortan)
            ("https://instagram.com/explore/tags/photo", "Hashtag", "[🏷️ Hashtag - ID: photo]"),
            ("https://www.instagram.com/explore/tags/instagram/", "Hashtag con www", "[🏷️ Hashtag - ID: instagra...]"),
            ("https://instagram.com/tags/landscape", "Hashtag formato directo", "[🏷️ Hashtag - ID: landscap...]"),
            
            # Direct Messages
            ("https://instagram.com/direct/inbox/", "Bandeja de Direct", "[📨 Bandeja directa de Instagram]"),
            ("https://www.instagram.com/direct/inbox/", "Bandeja con www", "[📨 Bandeja directa de Instagram]"),
            ("https://instagram.com/direct/t/1234567890/", "Hilo de mensajes", "[💬 Mensaje directo - ID: 12345678...]"),
            ("https://www.instagram.com/direct/t/9876543210/", "Hilo con www", "[💬 Mensaje directo - ID: 98765432...]"),
            
            # Secciones de perfil
            ("https://instagram.com/johndoe/tagged/", "Perfil - Etiquetado", "[🏷️ Perfil - Etiquetado de @johndoe]"),
            ("https://www.instagram.com/janesmith/tagged/", "Etiquetado con www", "[🏷️ Perfil - Etiquetado de @janesmith]"),
            ("https://instagram.com/johndoe/reels/", "Perfil - Reels", "[📹 Perfil - Reels de @johndoe]"),
            ("https://instagram.com/johndoe/guides/", "Perfil - Guides", "[📚 Perfil - Guías de @johndoe]"),
            ("https://instagram.com/johndoe/channel/", "Perfil - Canal", "[📺 Perfil - Canal de @johndoe]"),
            ("https://instagram.com/johndoe/saved/", "Perfil - Guardado", "[💾 Perfil - Guardado de @johndoe]"),
            
            # Shop
            ("https://instagram.com/shop/", "Shop principal", "[🛒 Tienda de Instagram]"),
            ("https://www.instagram.com/shop/", "Shop con www", "[🛒 Tienda de Instagram]"),
            ("https://instagram.com/shop/product/1234567890/", "Producto del shop", "[🛒 Producto - ID: 12345678...]"),
            ("https://www.instagram.com/shop/product/9876543210/", "Producto con www", "[🛒 Producto - ID: 98765432...]"),
            ("https://instagram.com/johndoe/shop/", "Perfil - Shop", "[🛒 Perfil - Tienda de @johndoe]"),
            ("https://www.instagram.com/janesmith/shop/", "Perfil Shop con www", "[🛒 Perfil - Tienda de @janesmith]"),
            
            # Live
            ("https://instagram.com/johndoe/live/", "Live", "[🔴 Transmisión en vivo de @johndoe]"),
            ("https://www.instagram.com/janesmith/live/", "Live con www", "[🔴 Transmisión en vivo de @janesmith]"),
            
            # IG TV (formato antiguo) - NOTA: hay un problema con el emoji aquí
            ("https://instagram.com/tv/ABC123def45/", "IG TV", "[📺 IG TV - ID: ABC123de...]"),
            ("https://www.instagram.com/tv/DEF456ghi78/", "IG TV con www", "[📺 IG TV - ID: DEF456gh...]"),
            
            # Threads
            ("https://instagram.com/threads/1234567890/", "Thread", "[🧵 Thread - ID: 12345678...]"),
            
            # URLs con parámetros (deben funcionar igual)
            ("https://instagram.com/p/ABC123def45/?utm_source=ig_web_copy_link", "Post con parámetros UTM", "[📸 Publicación - ID: ABC123de...]"),
            ("https://www.instagram.com/reel/DEF456ghi78/?hl=en", "Reel con parámetro de idioma", "[📹 Reel - ID: DEF456gh...]"),
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
                
                self.add_test_result(f"Instagram - {description}", success, details)
                self.print_test_result(f"Instagram - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Instagram - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Instagram - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = InstagramTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()