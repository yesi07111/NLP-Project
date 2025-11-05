from tests.base_tester import Tester, LinkProcessor

class MediumTester(Tester):
    """Tester específico para enlaces de Medium"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Medium"""
        print("📖 Ejecutando tests de Medium...")
        
        test_cases = [
            # Artículos con formato /p/slug
            ("https://medium.com/p/understanding-react-hooks-123456", "Artículo básico con /p/", "[📖 Artículo de Medium - ID: understa...]"),
            ("https://www.medium.com/p/javascript-closures-789012", "Artículo con www", "[📖 Artículo de Medium - ID: javascri...]"),
            ("https://medium.com/p/a-very-long-article-title-here-555555", "Artículo con título largo", "[📖 Artículo de Medium - ID: a-very-l...]"),
            
            # Perfiles de usuario
            ("https://medium.com/@johndoe", "Perfil de usuario básico", "[✍️ Perfil de Medium de @johndoe]"),
            ("https://www.medium.com/@janesmith", "Perfil con www", "[✍️ Perfil de Medium de @janesmith]"),
            ("https://medium.com/@techwriter", "Perfil de escritor técnico", "[✍️ Perfil de Medium de @techwriter]"),
            
            # Publicaciones + artículos
            ("https://medium.com/towards-data-science/machine-learning-101-123456", "Artículo en publicación", "[📖 Artículo de Medium en towards-data-science - ID: machine-...]"),
            ("https://medium.com/aws-cloud/cloud-computing-basics-789012", "Artículo en publicación AWS", "[📖 Artículo de Medium en aws-cloud - ID: cloud-co...]"),
            ("https://medium.com/javascript-scene/es6-features-555555", "Artículo en publicación JavaScript", "[📖 Artículo de Medium en javascript-scene - ID: es6-feat...]"),
            
            # Páginas de publicación
            ("https://medium.com/towards-data-science", "Página de publicación principal", "[📰 Publicación de Medium en towards-data-science]"),
            ("https://medium.com/aws-cloud", "Página de publicación AWS", "[📰 Publicación de Medium en aws-cloud]"),
            ("https://medium.com/towards-data-science/about", "Acerca de publicación", "[📰 Publicación de Medium en towards-data-science (about)]"),
            ("https://medium.com/towards-data-science/latest", "Últimos artículos de publicación", "[📰 Publicación de Medium en towards-data-science (latest)]"),
            ("https://medium.com/towards-data-science/search", "Búsqueda en publicación", "[📰 Publicación de Medium en towards-data-science (search)]"),
            ("https://medium.com/towards-data-science/write", "Escribir en publicación", "[📰 Publicación de Medium en towards-data-science (write)]"),
            
            # Tópicos/tags - AHORA NO SE ACORTAN
            ("https://medium.com/tag/javascript", "Tópico JavaScript", "[🏷️ Tema de Medium - ID: javascript]"),
            ("https://medium.com/tag/python", "Tópico Python", "[🏷️ Tema de Medium - ID: python]"),
            ("https://medium.com/tag/artificial-intelligence", "Tópico IA", "[🏷️ Tema de Medium - ID: artificial-intelligence]"),
            
            # Búsqueda
            ("https://medium.com/search", "Búsqueda principal", "[🔍 Búsqueda de Medium]"),
            ("https://medium.com/search?q=machine+learning", "Búsqueda con término", "[🔍 Búsqueda: machine learnin...]"),
            ("https://medium.com/search/posts", "Búsqueda en posts", "[🔍 Búsqueda de Medium - ID: posts]"),
            
            # Páginas personales - AHORA MUESTRAN IDs COMPLETOS
            ("https://medium.com/me", "Página personal", "[👤 Personal de Medium - ID: me]"),
            ("https://medium.com/you", "Página 'you'", "[👤 Personal de Medium - ID: you]"),
            ("https://medium.com/recommendations", "Recomendaciones", "[👤 Personal de Medium - ID: recommendations]"),
            ("https://medium.com/readinglist", "Lista de lectura", "[👤 Personal de Medium - ID: readinglist]"),
            ("https://medium.com/me/stats", "Estadísticas personales", "[👤 Personal de Medium - ID: stats]"),
            ("https://medium.com/me/notifications", "Notificaciones personales", "[👤 Personal de Medium - ID: notifications]"),
            
            # Subdominios personalizados (publicaciones) - AHORA DETECTADOS CORRECTAMENTE
            ("https://towardsdatascience.com/machine-learning-tutorial-123456", "Subdominio publicación + artículo", "[📖 Artículo de Medium en towardsdatascience - ID: machine-...]"),
            ("https://aws.medium.com/cloud-guide-789012", "Subdominio aws.medium.com", "[📖 Artículo de Medium en aws - ID: cloud-gu...]"),
            ("https://javascript.plainenglish.io/es6-guide-555555", "Subdominio plainenglish", "[📖 Artículo de Medium en javascript - ID: es6-guid...]"),
            ("https://blog.prototypr.io/design-tips-123456", "Subdominio prototypr", "[📖 Artículo de Medium en blog - ID: design-t...]"),
            
            # URLs con parámetros
            ("https://medium.com/p/react-tutorial-123456?source=homepage", "Artículo con parámetros", "[📖 Artículo de Medium - ID: react-tu...]"),
            ("https://medium.com/@johndoe?source=follow", "Perfil con parámetros", "[✍️ Perfil de Medium de @johndoe]"),
            ("https://medium.com/towards-data-science?source=topics", "Publicación con parámetros", "[📰 Publicación de Medium en towards-data-science]"),
            
            # URLs móviles
            ("https://medium.com/m/global-identity-2", "URL móvil identidad global", "[📱 Móvil de Medium - ID: identity]"),
            ("https://medium.com/m/signin", "URL móvil signin", "[📱 Móvil de Medium - ID: signin]"),
            
            # Historias destacadas
            ("https://medium.com/s/story/data-science-future-123456", "Historia destacada", "[📖 Artículo de Medium - ID: data-sci... (destacado)]"),
            ("https://medium.com/s/notes-on-ai/ai-ethics-789012", "Notas destacadas", "[📖 Artículo de Medium - ID: ai-ethic... (destacado)]"),
            
            # Series
            ("https://medium.com/series/react-from-zero-to-hero-123456", "Serie de artículos", "[📚 Serie de Medium - ID: react-fr...]"),
            
            # Listas
            ("https://medium.com/list/react-resources-123456", "Lista de recursos", "[📋 Lista de Medium - ID: react-re...]"),
            
            # URLs de miembros
            ("https://medium.com/membership", "Membresía", "[💎 Membresía de Medium]"),
            ("https://medium.com/subscribe", "Suscripción", "[🔔 Suscripción de Medium]"),
            
            # Página principal
            ("https://medium.com", "Página principal", "[🏠 Inicio de Medium]"),
            ("https://www.medium.com/", "Página principal con www", "[🏠 Inicio de Medium]"),
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
                
                self.add_test_result(f"Medium - {description}", success, details)
                self.print_test_result(f"Medium - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Medium - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Medium - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = MediumTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()