from tests.base_tester import Tester, LinkProcessor

class PinterestTester(Tester):
    """Tester específico para enlaces de Pinterest"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        """Procesa una URL y retorna el resultado formateado"""
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Pinterest"""
        print("📌 Ejecutando tests de Pinterest...")
        
        test_cases = [
            # Pins individuales
            ("https://pinterest.com/pin/1234567890", "[📌 Pin de Pinterest - ID: 12345678...]"),
            ("https://www.pinterest.com/pin/9876543210", "[📌 Pin de Pinterest - ID: 98765432...]"),
            ("https://pinterest.com/pin/1234567890/", "[📌 Pin de Pinterest - ID: 12345678...]"),
            ("https://pinterest.com/pin/12345678901234567890", "[📌 Pin de Pinterest - ID: 12345678...]"),
            ("https://pinterest.com/pin/1234567890/some-title", "[📌 Pin de Pinterest - ID: 12345678...]"),
            
            # Tableros
            ("https://pinterest.com/johndoe/my-board-123456", "[📋 Tablero de Pinterest de @johndoe - my-board-123456]"),
            ("https://www.pinterest.com/janesmith/home-decor-ideas-789012", "[📋 Tablero de Pinterest de @janesmith - home-decor-ideas-789012]"),
            ("https://pinterest.com/username/board-name-555555/", "[📋 Tablero de Pinterest de @username - board-name-555555]"),
            
            # Perfiles de usuario
            ("https://pinterest.com/@johndoe", "[👤 Perfil de Pinterest de @johndoe]"),
            ("https://www.pinterest.com/@janesmith", "[👤 Perfil de Pinterest de @janesmith]"),
            ("https://pinterest.com/@username/", "[👤 Perfil de Pinterest de @username]"),
            
            # Secciones del perfil
            ("https://pinterest.com/@johndoe/pins", "[📌 Pins de Pinterest de @johndoe - Pins]"),
            ("https://pinterest.com/@janesmith/boards", "[📋 Tableros de Pinterest de @janesmith - Tableros]"),
            ("https://pinterest.com/@username/tries", "[🔨 Probados de Pinterest de @username - Probados]"),
            ("https://pinterest.com/@johndoe/likes", "[❤️ Me gusta de Pinterest de @johndoe - Me gusta]"),
            ("https://pinterest.com/@janesmith/followers", "[👥 Seguidores de Pinterest de @janesmith - Seguidores]"),
            ("https://pinterest.com/@username/following", "[👥 Siguiendo de Pinterest de @username - Siguiendo]"),
            
            # Ideas
            ("https://pinterest.com/ideas/home-decor", "[💡 Ideas de Pinterest - home-decor]"),
            ("https://www.pinterest.com/ideas/recipes", "[💡 Ideas de Pinterest - recipes]"),
            ("https://pinterest.com/ideas/diy-projects", "[💡 Ideas de Pinterest - diy-projects]"),
            ("https://pinterest.com/ideas/home-decor/some-subcategory", "[💡 Ideas de Pinterest - home-decor]"),
            
            # Búsqueda
            ("https://pinterest.com/search/pins/", "[🔍 Búsqueda de Pinterest]"),
            ("https://pinterest.com/search/pins/?q=wedding%20ideas", "[🔍 Búsqueda de Pinterest: wedding ideas]"),
            ("https://www.pinterest.com/search/pins/?q=home%20decor", "[🔍 Búsqueda de Pinterest: home decor]"),
            ("https://pinterest.com/search/pins/?q=christmas%20crafts&rs=typed", "[🔍 Búsqueda de Pinterest: christmas crafts]"),
            ("https://pinterest.com/search/", "[🔍 Búsqueda de Pinterest]"),
            ("https://pinterest.com/search/?q=winter", "[🔍 Búsqueda de Pinterest: winter]"),
            
            # Crear pin
            ("https://pinterest.com/pin/create", "[➕ Crear Pin de Pinterest]"),
            ("https://www.pinterest.com/pin/create/", "[➕ Crear Pin de Pinterest]"),
            
            # Business Hub
            ("https://pinterest.com/business", "[💼 Negocios de Pinterest]"),
            ("https://pinterest.com/business/hub", "[💼 Negocios de Pinterest - hub]"),
            ("https://pinterest.com/business/learn", "[💼 Negocios de Pinterest - learn]"),
            
            # Analytics
            ("https://pinterest.com/analytics", "[📊 Analytics de Pinterest]"),
            ("https://www.pinterest.com/analytics/", "[📊 Analytics de Pinterest]"),
            
            # Ads
            ("https://pinterest.com/ads", "[📢 Anuncios de Pinterest]"),
            ("https://pinterest.com/ads/create", "[📢 Anuncios de Pinterest - create]"),
            
            # Shop
            ("https://pinterest.com/shop/home-decor", "[🛒 Tienda de Pinterest - home-decor]"),
            ("https://www.pinterest.com/shop/fashion", "[🛒 Tienda de Pinterest - fashion]"),
            ("https://pinterest.com/shop/", "[🛒 Tienda de Pinterest]"),
            
            # Página principal (Today)
            ("https://pinterest.com", "[🏠 Inicio de Pinterest]"),
            ("https://www.pinterest.com", "[🏠 Inicio de Pinterest]"),
            ("https://pinterest.com/", "[🏠 Inicio de Pinterest]"),
            
            # Following feed
            ("https://pinterest.com/following", "[👀 Siguiendo de Pinterest]"),
            ("https://www.pinterest.com/following/", "[👀 Siguiendo de Pinterest]"),
            
            # Categorías
            ("https://pinterest.com/categories/home-decor", "[📂 Categoría de Pinterest - home-decor]"),
            ("https://pinterest.com/categories/food-drink", "[📂 Categoría de Pinterest - food-drink]"),
            ("https://pinterest.com/categories/diy-crafts", "[📂 Categoría de Pinterest - diy-crafts]"),
            
            # URLs con parámetros adicionales (deben funcionar igual)
            ("https://pinterest.com/pin/1234567890/?mt=login", "[📌 Pin de Pinterest - ID: 12345678...]"),
            ("https://pinterest.com/@johndoe/?filter=boards", "[👤 Perfil de Pinterest de @johndoe]"),
            
            # Casos edge importantes
            ("https://pinterest.com/pin/create/button", "[📌 Pin de Pinterest - ID: create]"),  # Este puede fallar - necesita arreglo en extractor
            ("https://pinterest.com/search/pins", "[🔍 Búsqueda de Pinterest]"),  # Sin barra final
            
            # Rutas que no deberían coincidir con tableros (reservadas)
            ("https://pinterest.com/pin/something", "[📌 Pin de Pinterest - ID: somethin...]"),
            ("https://pinterest.com/search/anything", "[🔍 Búsqueda de Pinterest: anything]"),
            ("https://pinterest.com/ideas/test", "[💡 Ideas de Pinterest - test]"),
            
            # Casos adicionales que faltaban
            ("https://pinterest.com/business/tools", "[💼 Negocios de Pinterest - tools]"),
            ("https://pinterest.com/business/ads", "[💼 Negocios de Pinterest - ads]"),
            ("https://pinterest.com/shop/new-arrivals", "[🛒 Tienda de Pinterest - new-arrivals]"),
            ("https://pinterest.com/categories/wedding", "[📂 Categoría de Pinterest - wedding]"),
            ("https://pinterest.com/@testuser/following", "[👥 Siguiendo de Pinterest de @testuser - Siguiendo]"),
            ("https://pinterest.com/@testuser/followers", "[👥 Seguidores de Pinterest de @testuser - Seguidores]"),
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
                
                test_name = f"Pinterest - {url}"
                self.add_test_result(test_name, success, details)
                self.print_test_result(test_name, success, details)
                
            except Exception as e:
                self.add_test_result(f"Pinterest - {url}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Esperado': expected
                })
                self.print_test_result(f"Pinterest - {url}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = PinterestTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()