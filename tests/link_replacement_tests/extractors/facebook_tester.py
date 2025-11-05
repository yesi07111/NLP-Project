from tests.base_tester import Tester, LinkProcessor

class FacebookTester(Tester):
    """Tester específico para enlaces de Facebook con verificaciones precisas"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _get_expected_result(self, url, description):
        """Define los resultados esperados para cada caso de prueba"""
        expected_map = {
            # Perfiles
            "https://facebook.com/profile.php?id=1234567890": "[👤 Perfil de Facebook - ID: 1234567890]",
            "https://fb.com/john.doe": "[👤 Perfil de Facebook - ID: john.doe]",
            "https://facebook.com/username123": "[👤 Perfil de Facebook - ID: username123]",
            
            # Grupos
            "https://facebook.com/groups/1234567890": "[👥 Grupo de Facebook - ID: 1234567890]",
            "https://facebook.com/groups/1234567890/permalink/1234567890/": "[👥 Grupo de Facebook (permalink) - ID: 1234567890]",
            
            # Eventos
            "https://facebook.com/events/1234567890": "[📅 Evento de Facebook - ID: 1234567890]",
            
            # Páginas
            "https://facebook.com/pages/Page-Name/1234567890": "[📄 Página de Facebook - ID: 1234567890]",
            "https://facebook.com/pg/BusinessPage": "[📄 Página de Facebook - ID: BusinessPage]",
            
            # Videos
            "https://facebook.com/watch/?v=1234567890": "[🎥 Video de Facebook - ID: 1234567890]",
            "https://facebook.com/video.php?v=1234567890": "[🎥 Video de Facebook - ID: 1234567890]",
            "https://facebook.com/reel/1234567890": "[🎥 Video de Facebook (reel) - ID: 1234567890]",
            
            # Marketplace
            "https://facebook.com/marketplace": "[🛒 Marketplace de Facebook]",
            "https://facebook.com/marketplace/item/1234567890": "[🛒 Marketplace de Facebook - ID: 1234567890]",
            "https://facebook.com/marketplace/search/?query=laptop": "[🛒 Marketplace de Facebook (search)]",
            
            # Juegos
            "https://facebook.com/games/SomeGame": "[🎮 Juego de Facebook - ID: SomeGame]",
            
            # Fotos
            "https://facebook.com/photo.php?fbid=1234567890": "[🖼️ Foto de Facebook - ID: 1234567890]",
            "https://facebook.com/photo/1234567890": "[🖼️ Foto de Facebook - ID: 1234567890]",
            
            # Stories y publicaciones
            "https://facebook.com/story.php?story_fbid=1234567890": "[📖 Historia de Facebook - ID: 1234567890]",
            "https://facebook.com/posts/1234567890": "[📝 Publicación de Facebook - ID: 1234567890]",
            
            # Facebook Watch
            "https://facebook.com/watch": "[📺 Watch de Facebook]",
            
            # Facebook Live
            "https://facebook.com/live/1234567890": "[🔴 Live de Facebook - ID: 1234567890]",
            
            # Facebook Stories
            "https://facebook.com/stories/1234567890": "[📱 Stories de Facebook - ID: 1234567890]",
            
            # Facebook Gaming
            "https://facebook.com/gaming/streamer": "[🎮 Gaming de Facebook - ID: streamer]",
            
            # Facebook Notes
            "https://facebook.com/notes/note-title/1234567890": "[📝 Nota de Facebook - ID: 1234567890]",
            
            # Dominios alternativos
            "https://fb.com/groups/1234567890": "[👥 Grupo de Facebook - ID: 1234567890]",
            "https://fb.com/events/1234567890": "[📅 Evento de Facebook - ID: 1234567890]",
        }
        
        return expected_map.get(url)
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Facebook con verificaciones específicas"""
        print("🧪 Ejecutando tests específicos de Facebook...")
        
        test_cases = [
            # Perfiles
            ("https://facebook.com/profile.php?id=1234567890", "Perfil con ID"),
            ("https://fb.com/john.doe", "Perfil con username"),
            ("https://facebook.com/username123", "Perfil con username numérico"),
            
            # Grupos
            ("https://facebook.com/groups/1234567890", "Grupo básico"),
            ("https://facebook.com/groups/1234567890/permalink/1234567890/", "Permalink de grupo"),
            
            # Eventos
            ("https://facebook.com/events/1234567890", "Evento"),
            
            # Páginas
            ("https://facebook.com/pages/Page-Name/1234567890", "Página con pages"),
            ("https://facebook.com/pg/BusinessPage", "Página con pg"),
            
            # Videos
            ("https://facebook.com/watch/?v=1234567890", "Video con parámetro v"),
            ("https://facebook.com/video.php?v=1234567890", "Video con video.php"),
            ("https://facebook.com/reel/1234567890", "Reel"),
            
            # Marketplace
            ("https://facebook.com/marketplace", "Marketplace principal"),
            ("https://facebook.com/marketplace/item/1234567890", "Item de marketplace"),
            ("https://facebook.com/marketplace/search/?query=laptop", "Búsqueda en marketplace"),
            
            # Juegos
            ("https://facebook.com/games/SomeGame", "Juego"),
            
            # Fotos
            ("https://facebook.com/photo.php?fbid=1234567890", "Foto con fbid"),
            ("https://facebook.com/photo/1234567890", "Foto con ID directo"),
            
            # Stories y publicaciones
            ("https://facebook.com/story.php?story_fbid=1234567890", "Story"),
            ("https://facebook.com/posts/1234567890", "Publicación"),
            
            # Facebook Watch
            ("https://facebook.com/watch", "Facebook Watch"),
            
            # Facebook Live
            ("https://facebook.com/live/1234567890", "Facebook Live"),
            
            # Facebook Stories
            ("https://facebook.com/stories/1234567890", "Facebook Stories"),
            
            # Facebook Gaming
            ("https://facebook.com/gaming/streamer", "Facebook Gaming"),
            
            # Facebook Notes
            ("https://facebook.com/notes/note-title/1234567890", "Facebook Notes"),
            
            # Dominios alternativos
            ("https://fb.com/groups/1234567890", "Grupo en fb.com"),
            ("https://fb.com/events/1234567890", "Evento en fb.com"),
        ]
        
        for url, description in test_cases:
            try:
                result = self.processor.process_url(url)
                expected = self._get_expected_result(url, description)
                
                if expected:
                    # Verificar que el resultado es exactamente el esperado
                    success = expected == result
                    match_info = f"Esperado: {expected}"
                else:
                    # Fallback para casos no definidos
                    success = "Facebook" in result and "[" in result and "]" in result
                    match_info = "Verificación genérica"
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected if expected else "N/A",
                    'Coincide': match_info,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Facebook - {description}", success, details)
                self.print_test_result(f"Facebook - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Facebook - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Facebook - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })
                
if __name__ == "__main__":
    tester = FacebookTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()
