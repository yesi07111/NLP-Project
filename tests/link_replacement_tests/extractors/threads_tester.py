# tests/threads_tester.py
from tests.base_tester import Tester, LinkProcessor

class ThreadsTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("🧵 Ejecutando tests de Threads...")
        
        test_cases = [
            ("https://threads.net/@username/post/123456789", 
             "Thread específico con @",
             "[🧵 Thread de Threads - ID: 123456789, @username]"),
            
            ("https://www.threads.net/@johndoe/post/987654321", 
             "Thread con www",
             "[🧵 Thread de Threads - ID: 987654321, @johndoe]"),
            
            ("https://threads.net/username/post/555555555", 
             "Thread sin @",
             "[🧵 Thread de Threads - ID: 555555555, @username]"),
            
            ("https://threads.net/post/123456789", 
             "Thread directo sin usuario",
             "[🧵 Thread de Threads - ID: 123456789]"),
            
            ("https://threads.net/post/987654321", 
             "Otro thread directo",
             "[🧵 Thread de Threads - ID: 987654321]"),
            
            ("https://threads.net/@username", 
             "Perfil con @",
             "[👤 Perfil de Threads - @username]"),
            
            ("https://threads.net/username", 
             "Perfil sin @",
             "[👤 Perfil de Threads - @username]"),
            
            ("https://threads.net/johndoe", 
             "Perfil John Doe",
             "[👤 Perfil de Threads - @johndoe]"),
            
            ("https://threads.net/janesmith", 
             "Perfil Jane Smith",
             "[👤 Perfil de Threads - @janesmith]"),
            
            ("https://threads.net/search", 
             "Búsqueda principal",
             "[🔍 Búsqueda de Threads]"),
            
            ("https://threads.net/search/python", 
             "Búsqueda término específico",
             "[🔍 Búsqueda: python]"),
            
            ("https://threads.net/search/web%20development", 
             "Búsqueda con espacios",
             "[🔍 Búsqueda: web development]"),
            
            ("https://threads.net/explore", 
             "Explorar",
             "[🔍 Explorar de Threads]"),
            
            ("https://threads.net/notifications", 
             "Notificaciones",
             "[🔔 Notificaciones de Threads]"),
            
            ("https://threads.net/@username/replies", 
             "Perfil - Respuestas",
             "[💬 Respuestas de Threads - @username]"),
            
            ("https://threads.net/@username/reposts", 
             "Perfil - Reposts",
             "[🔄 Reposts de Threads - @username]"),
            
            ("https://threads.net/@username/likes", 
             "Perfil - Me gusta",
             "[❤️ Me gusta de Threads - @username]"),
            
            ("https://threads.net/username/replies", 
             "Perfil respuestas sin @",
             "[💬 Respuestas de Threads - @username]"),
            
            ("https://threads.net/username/reposts", 
             "Perfil reposts sin @",
             "[🔄 Reposts de Threads - @username]"),
            
            ("https://threads.net/username/likes", 
             "Perfil likes sin @",
             "[❤️ Me gusta de Threads - @username]"),
            
            ("https://threads.net/@user.name/post/123456789", 
             "Thread con puntos en usuario",
             "[🧵 Thread de Threads - ID: 123456789, @user.name]"),
            
            ("https://threads.net/@user_name/post/987654321", 
             "Thread con guiones",
             "[🧵 Thread de Threads - ID: 987654321, @user_name]"),
            
            ("https://threads.net/@123username/post/555555555", 
             "Thread usuario numérico",
             "[🧵 Thread de Threads - ID: 555555555, @123username]"),
            
            ("https://threads.net/", 
             "Página principal",
             "[🧵 Inicio de Threads]"),
            
            ("https://threads.net", 
             "Página principal sin barra",
             "[🧵 Inicio de Threads]"),
            
            ("https://threads.net/post/123456789/", 
             "Thread con barra final",
             "[🧵 Thread de Threads - ID: 123456789]"),
            
            ("https://threads.net/@username/", 
             "Perfil con barra final",
             "[👤 Perfil de Threads - @username]"),
            
            ("https://threads.net/search/", 
             "Búsqueda con barra final",
             "[🔍 Búsqueda de Threads]"),
            
            ("https://threads.net/explore/", 
             "Explorar con barra final",
             "[🔍 Explorar de Threads]"),
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
                
                self.add_test_result(f"Threads - {description}", success, details)
                self.print_test_result(f"Threads - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Threads - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Threads - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = ThreadsTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()