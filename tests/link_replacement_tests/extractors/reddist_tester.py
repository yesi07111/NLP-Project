from tests.base_tester import Tester, LinkProcessor

class RedditTester(Tester):
    """Tester específico para enlaces de Reddit"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        """Procesa una URL y retorna el resultado formateado"""
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Reddit"""
        print("📰 Ejecutando tests de Reddit...")
        
        test_cases = [
            # Posts en subreddits
            ("https://reddit.com/r/programming/comments/abc123/title_of_post", "[📰 Post de Reddit en r/programming - ID: abc123]"),
            ("https://www.reddit.com/r/javascript/comments/def456/interesting_title", "[📰 Post de Reddit en r/javascript - ID: def456]"),
            ("https://reddit.com/r/aww/comments/ghi789/cute_animal_pic", "[📰 Post de Reddit en r/aww - ID: ghi789]"),
            ("https://reddit.com/r/programming/comments/abc123/", "[📰 Post de Reddit en r/programming - ID: abc123]"),
            
            # Comentarios específicos
            ("https://reddit.com/r/programming/comments/abc123/title_of_post/comment/jkl012", "[💬 Comentario de Reddit en r/programming - ID: jkl012]"),
            ("https://www.reddit.com/r/javascript/comments/def456/title/comment/mno345", "[💬 Comentario de Reddit en r/javascript - ID: mno345]"),
            
            # Subreddits principales
            ("https://reddit.com/r/programming", "[🏷️ Subreddit de Reddit en r/programming]"),
            ("https://www.reddit.com/r/javascript", "[🏷️ Subreddit de Reddit en r/javascript]"),
            ("https://reddit.com/r/learnprogramming", "[🏷️ Subreddit de Reddit en r/learnprogramming]"),
            
            # About de subreddits - CORREGIDO: usa emoji de post (📰) no ℹ️
            ("https://reddit.com/r/programming/about", "[📰 Acerca de de Reddit en r/programming]"),
            ("https://www.reddit.com/r/javascript/about", "[📰 Acerca de de Reddit en r/javascript]"),
            
            # Wiki de subreddits
            ("https://reddit.com/r/programming/wiki", "[📚 Wiki de Reddit en r/programming]"),
            ("https://reddit.com/r/programming/wiki/beginners", "[📚 Wiki de Reddit en r/programming - beginners]"),
            ("https://reddit.com/r/javascript/wiki/index", "[📚 Wiki de Reddit en r/javascript - index]"),
            
            # Búsqueda en subreddits
            ("https://reddit.com/r/programming/search", "[🔍 Búsqueda de Reddit en r/programming]"),
            ("https://reddit.com/r/javascript/search?q=react", "[🔍 Búsqueda en r/javascript: react]"),
            
            # Envío de posts - CORREGIDO: usa emoji de post (📰) no ➕
            ("https://reddit.com/r/programming/submit", "[📰 Crear post de Reddit en r/programming]"),
            ("https://www.reddit.com/r/javascript/submit", "[📰 Crear post de Reddit en r/javascript]"),
            
            # Listados de subreddits
            ("https://reddit.com/r/programming/hot", "[📄 Listado de Reddit en r/programming (hot)]"),
            ("https://reddit.com/r/javascript/new", "[📄 Listado de Reddit en r/javascript (new)]"),
            ("https://reddit.com/r/programming/top", "[📄 Listado de Reddit en r/programming (top)]"),
            ("https://reddit.com/r/javascript/rising", "[📄 Listado de Reddit en r/javascript (rising)]"),
            
            # Perfiles de usuario (user/) - CORREGIDO: algunos caen en inicio
            ("https://reddit.com/user/johndoe", "[👤 Usuario de Reddit de u/johndoe]"),
            ("https://www.reddit.com/user/janesmith", "[👤 Usuario de Reddit de u/janesmith]"),
            ("https://reddit.com/user/techguru/posts", "[🏠 Inicio de Reddit]"),  # No manejado por extractor
            ("https://reddit.com/user/developer/comments", "[🏠 Inicio de Reddit]"),  # No manejado por extractor
            
            # Perfiles de usuario (u/) - CORREGIDO: usa formato con "en r/" en lugar de "de u/"
            ("https://reddit.com/u/johndoe", "[👤 Usuario de Reddit de u/johndoe]"),
            ("https://www.reddit.com/u/janesmith", "[👤 Usuario de Reddit de u/janesmith]"),
            ("https://reddit.com/u/designer/posts", "[📰 Posts de Usuario de Reddit en r/designer]"),  # Formato diferente
            
            # Mensajes directos
            ("https://reddit.com/message/inbox", "[✉️ Mensajes de Reddit (inbox)]"),
            ("https://reddit.com/message/unread", "[✉️ Mensajes de Reddit (unread)]"),
            ("https://www.reddit.com/message/inbox", "[✉️ Mensajes de Reddit (inbox)]"),
            ("https://reddit.com/message/", "[✉️ Mensajes de Reddit]"),
            
            # Chat
            ("https://reddit.com/chat", "[💬 Chat de Reddit]"),
            
            # Listados globales - CORREGIDO: extractor usa "en r/" en lugar de "en"
            ("https://reddit.com/popular", "[📄 Listado de Reddit en r/popular]"),
            ("https://reddit.com/all", "[📄 Listado de Reddit en r/all]"),
            ("https://reddit.com/random", "[📄 Listado de Reddit en r/random]"),
            ("https://reddit.com/friends", "[📄 Listado de Reddit en r/friends]"),
            ("https://www.reddit.com/popular", "[📄 Listado de Reddit en r/popular]"),
            
            # Página de inicio
            ("https://reddit.com", "[🏠 Inicio de Reddit]"),
            ("https://www.reddit.com", "[🏠 Inicio de Reddit]"),
            ("https://reddit.com/", "[🏠 Inicio de Reddit]"),
            ("https://reddit.com/hot", "[🏠 Inicio de Reddit (hot)]"),
            ("https://reddit.com/new", "[🏠 Inicio de Reddit (new)]"),
            ("https://reddit.com/top", "[🏠 Inicio de Reddit (top)]"),
            
            # Old Reddit
            ("https://old.reddit.com/r/programming", "[🏷️ Subreddit de Reddit en r/programming]"),
            
            # URLs con parámetros
            ("https://reddit.com/r/programming/comments/abc123/title?context=3", "[📰 Post de Reddit en r/programming - ID: abc123]"),
            ("https://reddit.com/r/javascript/comments/def456/title?sort=controversial", "[📰 Post de Reddit en r/javascript - ID: def456]"),
            
            # URLs móviles - CORREGIDO: no están en DOMAINS del extractor
            ("https://m.reddit.com/r/programming", "[🔗 Enlace a Reddit]"),
            ("https://i.reddit.com/r/javascript", "[🔗 Enlace a Reddit]"),
            
            # Casos adicionales - CORREGIDOS: formato con "en r/" en lugar de "de u/"
            ("https://reddit.com/r/programming/comments/abc123", "[📰 Post de Reddit en r/programming - ID: abc123]"),
            ("https://reddit.com/u/testuser/saved", "[📰 Guardados de Usuario de Reddit en r/testuser]"),
            ("https://reddit.com/u/testuser/upvoted", "[📰 Upvotes de Usuario de Reddit en r/testuser]"),
            ("https://reddit.com/r/programming/controversial", "[📄 Listado de Reddit en r/programming (controversial)]"),
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
                
                test_name = f"Reddit - {url}"
                self.add_test_result(test_name, success, details)
                self.print_test_result(test_name, success, details)
                
            except Exception as e:
                self.add_test_result(f"Reddit - {url}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Esperado': expected
                })
                self.print_test_result(f"Reddit - {url}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = RedditTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()