from tests.base_tester import Tester, LinkProcessor

class AmazonTester(Tester):
    """Tester específico para enlaces de Amazon con verificaciones precisas"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _get_expected_result(self, url, description):
        """Define los resultados esperados para cada caso de prueba con emojis correctos"""
        expected_map = {
            # Productos
            "https://www.amazon.com/dp/B08N5WRWNW": "[🛒 Producto de Amazon - ID: B08N5WRWNW]",
            "https://amazon.com/gp/product/B08N5WRWNW": "[🛒 Producto de Amazon - ID: B08N5WRWNW]",
            "https://amazon.com.mx/product/B08N5WRWNW": "[🛒 Producto de Amazon - ID: B08N5WRWNW]",
            "https://amazon.com/B08N5WRWNW": "[🛒 Producto de Amazon - ID: B08N5WRWNW]",
            
            # Búsquedas
            "https://amazon.com/s?k=laptop+gaming": "[🔍 Búsqueda de Amazon - Búsqueda: 'laptop gaming']",
            "https://amazon.com/s?field-keywords=teclado+mecanico": "[🔍 Búsqueda de Amazon - Búsqueda: 'teclado mecanico']",
            "https://amazon.com/s?k=python+programming+books": "[🔍 Búsqueda de Amazon - Búsqueda: 'python programming books']",
            
            # Ofertas
            "https://amazon.com/deal/1234567890": "[💰 Oferta de Amazon - ID: 1234567890]",
            "https://amazon.com/gp/goldbox": "[💰 Ofertas del día de Amazon]",
            "https://amazon.com/gp/lightning-deals": "[⚡ Oferta relámpago de Amazon]",
            
            # Tiendas
            "https://amazon.com/store/ExampleStore": "[🏪 Tienda de Amazon - Categoría: ExampleStore]",
            
            # Listas de deseos
            "https://amazon.com/wishlist/1234567890": "[❤️ Lista de deseos de Amazon - ID: 1234567890]",
            "https://amazon.com/wishlist/1234567890?lm=1": "[❤️ Lista de deseos pública de Amazon - ID: 1234567890]",
            
            # Carrito y pedidos
            "https://amazon.com/cart": "[🛒 Carrito de Amazon]",
            "https://amazon.com/your-orders": "[📦 Pedidos de Amazon]",
            
            # Reseñas
            "https://amazon.com/review/create-review": "[⭐ Crear reseña de Amazon]",
            "https://amazon.com/product-reviews/B08N5WRWNW": "[⭐ Reseñas del producto de Amazon - ID: B08N5WRWNW]",
            
            # Vendedores
            "https://amazon.com/s?me=A1234567890": "[👤 Vendedor de Amazon - ID: A1234567890]",
            "https://amazon.com/sp?seller=A1234567890": "[👤 Vendedor de Amazon - ID: A1234567890]",
            
            # Servicios Amazon
            "https://amazon.com/alm/storefront": "[🥦 Amazon Fresh de Amazon]",
            "https://amazon.com/prime": "[👑 Prime de Amazon]",
            "https://amazon.com/prime/video": "[🎥 Prime Video de Amazon]",
            "https://amazon.com/music/unlimited": "[🎵 Music Unlimited de Amazon]",
            "https://amazon.com/video": "[🎥 Amazon Video de Amazon]",
            "https://amazon.com/books": "[📚 Libros de Amazon]",
            "https://amazon.com/mobile-apps": "[📱 Appstore de Amazon]",
            "https://amazon.com/kindle/store": "[📖 Tienda Kindle de Amazon]",
            "https://amazon.com/echo": "[🔊 Echo de Amazon]",
            
            # Categorías
            "https://amazon.com/fashion": "[👗 Moda de Amazon]",
            "https://amazon.com/electronics": "[📱 Electrónicos de Amazon]",
            "https://amazon.com/home": "[🏠 Hogar de Amazon]",
            "https://amazon.com/garden": "[🌿 Jardín de Amazon]",
            "https://amazon.com/automotive": "[🚗 Automotriz de Amazon]",
            
            # Amazon Business
            "https://business.amazon.com": "[💼 Amazon Business de Amazon]",
            "https://amazon.com/b2b": "[💼 Amazon Business de Amazon]",
            
            # Outlet y Warehouse
            "https://amazon.com/warehouse-deals": "[🏭 Warehouse de Amazon]",
            "https://amazon.com/outlet": "[🏪 Outlet de Amazon]",
            
            # Subscribe & Save
            "https://amazon.com/subscribe-and-save": "[📦 Subscribe & Save de Amazon]",
        }
        
        return expected_map.get(url)
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Amazon con verificaciones específicas"""
        print("🧪 Ejecutando tests específicos de Amazon...")
        
        test_cases = [
            # Productos
            ("https://www.amazon.com/dp/B08N5WRWNW", "Producto con ID"),
            ("https://amazon.com/gp/product/B08N5WRWNW", "Producto alternativo"),
            ("https://amazon.com.mx/product/B08N5WRWNW", "Producto en dominio local"),
            ("https://amazon.com/B08N5WRWNW", "Producto con ASIN directo"),
            
            # Búsquedas
            ("https://amazon.com/s?k=laptop+gaming", "Búsqueda simple"),
            ("https://amazon.com/s?field-keywords=teclado+mecanico", "Búsqueda con field-keywords"),
            ("https://amazon.com/s?k=python+programming+books", "Búsqueda con espacios"),
            
            # Ofertas
            ("https://amazon.com/deal/1234567890", "Oferta regular"),
            ("https://amazon.com/gp/goldbox", "Ofertas del día"),
            ("https://amazon.com/gp/lightning-deals", "Ofertas relámpago"),
            
            # Tiendas
            ("https://amazon.com/store/ExampleStore", "Tienda específica"),
            
            # Listas de deseos
            ("https://amazon.com/wishlist/1234567890", "Lista de deseos personal"),
            ("https://amazon.com/wishlist/1234567890?lm=1", "Lista de deseos pública"),
            
            # Carrito y pedidos
            ("https://amazon.com/cart", "Carrito de compras"),
            ("https://amazon.com/your-orders", "Historial de pedidos"),
            
            # Reseñas
            ("https://amazon.com/review/create-review", "Crear reseña"),
            ("https://amazon.com/product-reviews/B08N5WRWNW", "Reseñas de producto"),
            
            # Vendedores
            ("https://amazon.com/s?me=A1234567890", "Página de vendedor"),
            ("https://amazon.com/sp?seller=A1234567890", "Página de vendedor alternativo"),
            
            # Servicios Amazon
            ("https://amazon.com/alm/storefront", "Amazon Fresh"),
            ("https://amazon.com/prime", "Amazon Prime"),
            ("https://amazon.com/prime/video", "Prime Video"),
            ("https://amazon.com/music/unlimited", "Amazon Music Unlimited"),
            ("https://amazon.com/video", "Amazon Video"),
            ("https://amazon.com/books", "Amazon Books"),
            ("https://amazon.com/mobile-apps", "Amazon Appstore"),
            ("https://amazon.com/kindle/store", "Kindle Store"),
            ("https://amazon.com/echo", "Amazon Echo"),
            
            # Categorías
            ("https://amazon.com/fashion", "Amazon Fashion"),
            ("https://amazon.com/electronics", "Amazon Electronics"),
            ("https://amazon.com/home", "Amazon Home"),
            ("https://amazon.com/garden", "Amazon Garden"),
            ("https://amazon.com/automotive", "Amazon Automotive"),
            
            # Amazon Business
            ("https://business.amazon.com", "Amazon Business"),
            ("https://amazon.com/b2b", "Amazon B2B"),
            
            # Outlet y Warehouse
            ("https://amazon.com/warehouse-deals", "Amazon Warehouse"),
            ("https://amazon.com/outlet", "Amazon Outlet"),
            
            # Subscribe & Save
            ("https://amazon.com/subscribe-and-save", "Subscribe & Save"),
        ]
        
        for url, description in test_cases:
            try:
                result = self.processor.process_url(url)
                expected = self._get_expected_result(url, description)
                
                if expected:
                    # Verificar que el resultado contiene el texto esperado
                    success = expected == result
                    match_info = f"Esperado: {expected}"
                else:
                    # Fallback para casos no definidos
                    success = "Amazon" in result and "[" in result and "]" in result
                    match_info = "Verificación genérica"
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected if expected else "N/A",
                    'Coincide': match_info,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Amazon - {description}", success, details)
                self.print_test_result(f"Amazon - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Amazon - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Amazon - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = AmazonTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()