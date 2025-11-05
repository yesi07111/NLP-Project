from tests.base_tester import Tester, LinkProcessor

class SnapchatTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("👻 Ejecutando tests de Snapchat...")
        
        test_cases = [
            # Agregar amigos
            ("https://snapchat.com/add/johndoe", "[👻 Agregar de Snapchat de johndoe]"),
            ("https://www.snapchat.com/add/janesmith", "[👻 Agregar de Snapchat de janesmith]"),
            ("https://snapchat.com/add", "[👻 Agregar de Snapchat]"),
            
            # Discover
            ("https://snapchat.com/discover", "[🔍 Discover de Snapchat]"),
            ("https://snapchat.com/discover/editorial", "[🔍 Discover de Snapchat - editorial]"),
            ("https://snapchat.com/discover/entertainment", "[🔍 Discover de Snapchat - entertainment]"),
            ("https://snapchat.com/discover/news", "[🔍 Discover de Snapchat - news]"),
            ("https://snapchat.com/discover/editorial/edition", "[📰 Discover Edition de Snapchat - editorial]"),
            ("https://snapchat.com/discover/entertainment/show", "[🎬 Discover Show de Snapchat - entertainment]"),
            
            # Stories
            ("https://snapchat.com/stories/username123", "[📖 Historia de Snapchat de username123]"),
            ("https://snapchat.com/stories/officialchannel", "[📖 Historia de Snapchat de officialchannel]"),
            ("https://snapchat.com/stories/", "[📖 Historia de Snapchat]"),
            
            # Spotlight
            ("https://snapchat.com/spotlight/1234567890", "[✨ Spotlight de Snapchat - 1234567890]"),
            ("https://snapchat.com/spotlight/9876543210", "[✨ Spotlight de Snapchat - 9876543210]"),
            
            # Mapa
            ("https://snapchat.com/map", "[🗺️ Mapa de Snapchat]"),
            ("https://snapchat.com/map/location123", "[🗺️ Mapa de Snapchat - location123]"),
            
            # Memories y Scan
            ("https://snapchat.com/memories", "[💾 Memories de Snapchat]"),
            ("https://snapchat.com/scan", "[📷 Scan de Snapchat]"),
            
            # Chat
            ("https://snapchat.com/chat/friend123", "[💬 Chat de Snapchat de friend123]"),
            ("https://snapchat.com/chat/group456", "[💬 Chat de Snapchat de group456]"),
            
            # Lentes
            ("https://snapchat.com/lenses/123456", "[🎭 Lens de Snapchat - 123456]"),
            ("https://snapchat.com/lenses/789012", "[🎭 Lens de Snapchat - 789012]"),
            ("https://snapchat.com/lenses/123456/try", "[🎭 Probar Lens de Snapchat - 123456]"),
            
            # Filters
            ("https://snapchat.com/filters/555555", "[🖼️ Filter de Snapchat - 555555]"),
            ("https://snapchat.com/filters/666666", "[🖼️ Filter de Snapchat - 666666]"),
            
            # Bitmoji
            ("https://snapchat.com/bitmoji/outfit-123", "[👤 Bitmoji de Snapchat - outfit-123]"),
            ("https://snapchat.com/bitmoji/avatar-456", "[👤 Bitmoji de Snapchat - avatar-456]"),
            
            # Snapcodes
            ("https://snapchat.com/snapcode/johndoe", "[📱 Snapcode de Snapchat de johndoe]"),
            ("https://snapchat.com/snapcode/business", "[📱 Snapcode de Snapchat de business]"),
            
            # Ads
            ("https://snapchat.com/ads/campaign-123", "[📢 Anuncios de Snapchat - campaign-123]"),
            ("https://snapchat.com/ads/promotion-456", "[📢 Anuncios de Snapchat - promotion-456]"),
            ("https://snapchat.com/ads", "[📢 Anuncios de Snapchat]"),
            
            # Business
            ("https://snapchat.com/business", "[💼 Negocios de Snapchat]"),
            ("https://snapchat.com/business/dashboard", "[💼 Negocios de Snapchat - dashboard]"),
            ("https://snapchat.com/business/insights", "[💼 Negocios de Snapchat - insights]"),
            
            # Store
            ("https://snapchat.com/store/product-123", "[🛒 Tienda de Snapchat - product-123]"),
            ("https://snapchat.com/store/merch-456", "[🛒 Tienda de Snapchat - merch-456]"),
            ("https://snapchat.com/store", "[🛒 Tienda de Snapchat]"),
            
            # Games
            ("https://snapchat.com/games/game-name", "[🎮 Juegos de Snapchat - game-name]"),
            ("https://snapchat.com/games/trivia", "[🎮 Juegos de Snapchat - trivia]"),
            ("https://snapchat.com/games", "[🎮 Juegos de Snapchat]"),
            
            # Minis
            ("https://snapchat.com/minis/app-name", "[📱 Minis de Snapchat - app-name]"),
            ("https://snapchat.com/minis/utility", "[📱 Minis de Snapchat - utility]"),
            ("https://snapchat.com/minis", "[📱 Minis de Snapchat]"),
            
            # Cameos y Originals
            ("https://snapchat.com/cameos", "[🎭 Cameos de Snapchat]"),
            ("https://snapchat.com/originals/show-name", "[🎬 Originals de Snapchat - show-name]"),
            ("https://snapchat.com/originals/series-123", "[🎬 Originals de Snapchat - series-123]"),
            ("https://snapchat.com/originals", "[🎬 Originals de Snapchat]"),
            
            # Perfiles
            ("https://snapchat.com/username123", "[👤 Perfil de Snapchat de username123]"),
            ("https://snapchat.com/officialaccount", "[👤 Perfil de Snapchat de officialaccount]"),
            
            # Página principal
            ("https://snapchat.com", "[🏠 Inicio de Snapchat]"),
            ("https://www.snapchat.com", "[🏠 Inicio de Snapchat]"),
            ("https://snapchat.com/", "[🏠 Inicio de Snapchat]"),
        ]
        
        for url, expected in test_cases:
            try:
                result = self._process_url(url)
                success = result == expected
                
                details = {
                    'URL': url,
                    'Resultado': result,
                    'Esperado': expected,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                test_name = f"Snapchat - {url}"
                self.add_test_result(test_name, success, details)
                self.print_test_result(test_name, success, details)
                
            except Exception as e:
                self.add_test_result(f"Snapchat - {url}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Esperado': expected
                })
                self.print_test_result(f"Snapchat - {url}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = SnapchatTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()