from tests.base_tester import Tester, LinkProcessor

class FlickrTester(Tester):
    """Tester específico para enlaces de Flickr con verificaciones precisas"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _get_expected_result(self, url, description):
        """Define los resultados esperados para cada caso de prueba"""
        expected_map = {
            # Fotos individuales
            "https://www.flickr.com/photos/johndoe/12345678901/": "[📷 Foto de Flickr de johndoe - ID: 12345678901]",
            "https://flickr.com/photos/janesmith/98765432109": "[📷 Foto de Flickr de janesmith - ID: 98765432109]",
            "https://flickr.com/photos/123456789@N01/55555555555/": "[📷 Foto de Flickr de 123456789@N01 - ID: 55555555555]",
            
            # Stream de fotos de usuario
            "https://flickr.com/photos/johndoe/": "[📷 Foto de Flickr de johndoe]",
            "https://flickr.com/photos/123456789@N01/": "[📷 Foto de Flickr de 123456789@N01]",
            
            # Álbumes
            "https://flickr.com/photos/johndoe/albums/72157612345678901": "[📚 Álbum de Flickr de johndoe - ID: 72157612345678901]",
            "https://flickr.com/photos/janesmith/albums": "[📚 Álbum de Flickr de janesmith]",
            "https://flickr.com/photos/johndoe/albums/72157612345678901/with/12345678901/": "[📚 Álbum de Flickr de johndoe - ID: 72157612345678901]",
            
            # Sets (conjuntos)
            "https://flickr.com/photos/johndoe/sets/72157623456789012": "[🖼️ Set de Flickr de johndoe - ID: 72157623456789012]",
            "https://flickr.com/photos/janesmith/sets": "[🖼️ Set de Flickr - ID: janesmith]",
            "https://flickr.com/photos/johndoe/sets/72157623456789012/with/12345678901/": "[🖼️ Set de Flickr de johndoe - ID: 72157623456789012]",
            
            # Galerías
            "https://flickr.com/photos/johndoe/galleries/72157634567890123": "[🎨 Galería de Flickr de johndoe - ID: 72157634567890123]",
            "https://flickr.com/photos/janesmith/galleries": "[🎨 Galería de Flickr de janesmith]",
            
            # Favoritos
            "https://flickr.com/photos/johndoe/favorites": "[⭐ Favoritos de Flickr de johndoe]",
            "https://flickr.com/photos/janesmith/favorites/": "[⭐ Favoritos de Flickr de janesmith]",
            
            # Grupos
            "https://flickr.com/groups/landscapephotography/": "[👥 Grupo de Flickr - ID: landscapephotography]",
            "https://flickr.com/groups/nature/pool/": "[👥 Grupo de Flickr - ID: nature]",
            "https://flickr.com/groups/urbanexploration/discuss/": "[👥 Grupo de Flickr - ID: urbanexploration]",
            
            # Perfiles de usuario
            "https://flickr.com/people/johndoe/": "[👤 Usuario de Flickr - ID: johndoe]",
            "https://flickr.com/people/123456789@N01/": "[👤 Usuario de Flickr - ID: 123456789@N01]",
            
            # Explore
            "https://flickr.com/explore": "[🔍 Explorar de Flickr]",
            "https://flickr.com/explore/2024/01/15/": "[🔍 Explorar de Flickr]",
            "https://flickr.com/explore/tags/sunset/": "[🔍 Explorar de Flickr]",
            
            # Mapas
            "https://flickr.com/map": "[🗺️ Mapa de Flickr]",
            "https://flickr.com/map?min_upload_date=2024&min_taken_date=2024": "[🗺️ Mapa de Flickr]",
            
            # The Commons
            "https://flickr.com/commons": "[🏛️ Commons de Flickr]",
            "https://flickr.com/commons/usage/": "[🏛️ Commons de Flickr]",
            
            # Búsquedas
            "https://flickr.com/search?text=mountains": "[🔍 Explorar de Flickr]",
            "https://flickr.com/search?user_id=123456789@N01": "[🔍 Explorar de Flickr]",
            
            # Fotos interesantes
            "https://flickr.com/explore/interesting/2024/01/15/": "[🔍 Explorar de Flickr]",
            "https://flickr.com/explore/interesting": "[🔍 Explorar de Flickr]",
            
            # Licencias
            "https://flickr.com/creativecommons/": "[🔍 Explorar de Flickr]",
            "https://flickr.com/creativecommons/commercial-use/": "[🔍 Explorar de Flickr]",
            
            # Variaciones de URL
            "https://www.flickr.com/photos/johndoe/12345678901/in/album-72157612345678901/": "[📷 Foto de Flickr de johndoe - ID: 12345678901]",
            "https://flickr.com/photos/johndoe/12345678901/in/photostream/": "[📷 Foto de Flickr de johndoe - ID: 12345678901]",
            "https://flickr.com/photos/johndoe/12345678901/in/dateposted/": "[📷 Foto de Flickr de johndoe - ID: 12345678901]",
            
            # URLs cortas (posibles)
            "https://flic.kr/p/abc123": "[📷 Foto de Flickr - ID: abc123]",
            "https://flic.kr/ps/abc123": "[🖼️ Set de Flickr - ID: abc123]",
        }
        
        return expected_map.get(url)
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Flickr con verificaciones específicas"""
        print("🧪 Ejecutando tests específicos de Flickr...")
        
        test_cases = [
            # Fotos individuales
            ("https://www.flickr.com/photos/johndoe/12345678901/", "Foto de usuario"),
            ("https://flickr.com/photos/janesmith/98765432109", "Foto sin barra final"),
            ("https://flickr.com/photos/123456789@N01/55555555555/", "Foto con ID numérico"),
            
            # Stream de fotos de usuario
            ("https://flickr.com/photos/johndoe/", "Stream de fotos de usuario"),
            ("https://flickr.com/photos/123456789@N01/", "Stream con ID numérico"),
            
            # Álbumes
            ("https://flickr.com/photos/johndoe/albums/72157612345678901", "Álbum específico"),
            ("https://flickr.com/photos/janesmith/albums", "Lista de álbumes"),
            ("https://flickr.com/photos/johndoe/albums/72157612345678901/with/12345678901/", "Álbum con foto"),
            
            # Sets (conjuntos)
            ("https://flickr.com/photos/johndoe/sets/72157623456789012", "Set de fotos"),
            ("https://flickr.com/photos/janesmith/sets", "Lista de sets"),
            ("https://flickr.com/photos/johndoe/sets/72157623456789012/with/12345678901/", "Set con foto específica"),
            
            # Galerías
            ("https://flickr.com/photos/johndoe/galleries/72157634567890123", "Galería"),
            ("https://flickr.com/photos/janesmith/galleries", "Lista de galerías"),
            
            # Favoritos
            ("https://flickr.com/photos/johndoe/favorites", "Fotos favoritas"),
            ("https://flickr.com/photos/janesmith/favorites/", "Favoritos con barra final"),
            
            # Grupos
            ("https://flickr.com/groups/landscapephotography/", "Grupo de fotografía"),
            ("https://flickr.com/groups/nature/pool/", "Pool de grupo"),
            ("https://flickr.com/groups/urbanexploration/discuss/", "Discusión de grupo"),
            
            # Perfiles de usuario
            ("https://flickr.com/people/johndoe/", "Perfil de usuario"),
            ("https://flickr.com/people/123456789@N01/", "Perfil con ID numérico"),
            
            # Explore
            ("https://flickr.com/explore", "Explore principal"),
            ("https://flickr.com/explore/2024/01/15/", "Explore por fecha"),
            ("https://flickr.com/explore/tags/sunset/", "Explore por tag"),
            
            # Mapas
            ("https://flickr.com/map", "Mapa de Flickr"),
            ("https://flickr.com/map?min_upload_date=2024&min_taken_date=2024", "Mapa con filtros"),
            
            # The Commons
            ("https://flickr.com/commons", "Flickr Commons"),
            ("https://flickr.com/commons/usage/", "Uso de Commons"),
            
            # Búsquedas
            ("https://flickr.com/search?text=mountains", "Búsqueda por texto"),
            ("https://flickr.com/search?user_id=123456789@N01", "Búsqueda por usuario"),
            
            # Fotos interesantes
            ("https://flickr.com/explore/interesting/2024/01/15/", "Fotos interesantes por fecha"),
            ("https://flickr.com/explore/interesting", "Fotos interesantes recientes"),
            
            # Licencias
            ("https://flickr.com/creativecommons/", "Creative Commons"),
            ("https://flickr.com/creativecommons/commercial-use/", "CC comercial"),
            
            # Variaciones de URL
            ("https://www.flickr.com/photos/johndoe/12345678901/in/album-72157612345678901/", "Foto en álbum"),
            ("https://flickr.com/photos/johndoe/12345678901/in/photostream/", "Foto en photostream"),
            ("https://flickr.com/photos/johndoe/12345678901/in/dateposted/", "Foto por fecha"),
            
            # URLs cortas (posibles)
            ("https://flic.kr/p/abc123", "URL corta de foto"),
            ("https://flic.kr/ps/abc123", "URL corta de set"),
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
                    success = "Flickr" in result and "[" in result and "]" in result
                    match_info = "Verificación genérica"
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected if expected else "N/A",
                    'Coincide': match_info,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Flickr - {description}", success, details)
                self.print_test_result(f"Flickr - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Flickr - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Flickr - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = FlickrTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()