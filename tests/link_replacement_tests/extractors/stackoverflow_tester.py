from tests.base_tester import Tester, LinkProcessor

class StackOverflowTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("❓ Ejecutando tests de Stack Overflow...")
        
        test_cases = [
            # Preguntas
            ("https://stackoverflow.com/questions/123456/python-list-comprehension", 
             "Pregunta específica",
             "[❓ Pregunta - ID: 123456]"),
            
            ("https://www.stackoverflow.com/questions/789012/javascript-array-methods", 
             "Pregunta con www",
             "[❓ Pregunta - ID: 789012]"),
            
            ("https://stackoverflow.com/questions/555555/django-models/555556", 
             "Respuesta específica",
             "[💬 Respuesta - ID: 555555, Respuesta: 555556]"),
            
            ("https://stackoverflow.com/questions/777777/react-hooks", 
             "Pregunta con slug",
             "[❓ Pregunta - ID: 777777]"),
            
            # Usuarios
            ("https://stackoverflow.com/users/123456/johndoe", 
             "Perfil de usuario",
             "[👤 Usuario - Usuario: 123456]"),
            
            ("https://stackoverflow.com/users/789012/janesmith", 
             "Otro perfil",
             "[👤 Usuario - Usuario: 789012]"),
            
            ("https://stackoverflow.com/users/123456/johndoe/profile", 
             "Perfil completo",
             "[👤 Perfil de usuario - Usuario: 123456]"),
            
            ("https://stackoverflow.com/users/789012/janesmith/edit", 
             "Editar perfil",
             "[✏️ Editar perfil - Usuario: 789012]"),
            
            ("https://stackoverflow.com/users/123456/johndoe/top-questions", 
             "Mejores preguntas",
             "[❓ Mejores preguntas - Usuario: 123456]"),
            
            ("https://stackoverflow.com/users/789012/janesmith/top-answers", 
             "Mejores respuestas",
             "[💬 Mejores respuestas - Usuario: 789012]"),
            
            # Etiquetas
            ("https://stackoverflow.com/tags/python", 
             "Etiqueta Python",
             "[🏷️ Etiqueta - python]"),
            
            ("https://stackoverflow.com/tags/javascript", 
             "Etiqueta JavaScript",
             "[🏷️ Etiqueta - javascript]"),
            
            ("https://stackoverflow.com/tags/python/info", 
             "Info etiqueta Python",
             "[ℹ️ Info de etiqueta - python]"),
            
            ("https://stackoverflow.com/tags/javascript/unanswered", 
             "JavaScript sin respuesta",
             "[❓ Etiqueta sin respuesta - javascript]"),
            
            # Búsquedas
            ("https://stackoverflow.com/search?q=python+list", 
             "Búsqueda Python",
             "[🔍 Búsqueda: python list]"),
            
            ("https://stackoverflow.com/search?q=javascript+promise", 
             "Búsqueda JavaScript",
             "[🔍 Búsqueda: javascript promise]"),
            
            # Colecciones y posts
            ("https://stackoverflow.com/collection/123456", 
             "Colección específica",
             "[📚 Colección - ID: 123456]"),
            
            ("https://stackoverflow.com/collection/789012", 
             "Otra colección",
             "[📚 Colección - ID: 789012]"),
            
            ("https://stackoverflow.com/posts/123456", 
             "Post específico",
             "[📝 Post - ID: 123456]"),
            
            ("https://stackoverflow.com/posts/789012", 
             "Otro post",
             "[📝 Post - ID: 789012]"),
            
            # Empresas y empleos
            ("https://stackoverflow.com/company/google", 
             "Empresa Google",
             "[🏢 Empresa - google]"),
            
            ("https://stackoverflow.com/company/microsoft", 
             "Empresa Microsoft",
             "[🏢 Empresa - microsoft]"),
            
            ("https://stackoverflow.com/jobs/123456/senior-developer", 
             "Empleo específico",
             "[💼 Empleo - ID: 123456]"),
            
            ("https://stackoverflow.com/jobs/789012/frontend-engineer", 
             "Otro empleo",
             "[💼 Empleo - ID: 789012]"),
            
            ("https://stackoverflow.com/jobs/companies", 
             "Empresas con empleos",
             "[🏢 Empresas con empleos]"),
            
            ("https://stackoverflow.com/jobs/developer", 
             "Empleos desarrolladores",
             "[💻 Empleos para desarrolladores]"),
            
            # Documentación y teams
            ("https://stackoverflow.com/documentation/python", 
             "Documentación Python",
             "[📚 Documentación - python]"),
            
            ("https://stackoverflow.com/documentation/javascript", 
             "Documentación JavaScript",
             "[📚 Documentación - javascript]"),
            
            ("https://stackoverflow.com/teams/team-name", 
             "Teams específico",
             "[👥 Teams - team-name]"),
            
            ("https://stackoverflow.com/teams/another-team", 
             "Otro team",
             "[👥 Teams - another-team]"),
            
            # Blog y ayuda
            ("https://stackoverflow.com/blog/announcement", 
             "Blog anuncio",
             "[📰 Blog - announcement]"),
            
            ("https://stackoverflow.com/blog/technical-article", 
             "Blog artículo",
             "[📰 Blog - technical-article]"),
            
            ("https://stackoverflow.com/help/asking", 
             "Ayuda preguntas",
             "[🛟 Ayuda - asking]"),
            
            ("https://stackoverflow.com/help/formatting", 
             "Ayuda formato",
             "[🛟 Ayuda - formatting]"),
            
            # Revisión y elecciones
            ("https://stackoverflow.com/review/tasks/123456", 
             "Revisión tarea",
             "[👀 Revisión - ID: 123456]"),
            
            ("https://stackoverflow.com/review/suggested-edits/789012", 
             "Revisión ediciones",
             "[👀 Revisión - ID: 789012]"),
            
            ("https://stackoverflow.com/election/123456", 
             "Elección",
             "[🗳️ Elección - ID: 123456]"),
            
            # Insignias
            ("https://stackoverflow.com/badges/123/gold-badge", 
             "Insignia específica",
             "[🏅 Insignias - 123]"),
            
            ("https://stackoverflow.com/badges/456/silver-badge", 
             "Otra insignia",
             "[🏅 Insignias - 456]"),
            
            # Páginas principales
            ("https://stackoverflow.com/", 
             "Página principal",
             "[🏠 Inicio]"),
            
            ("https://stackoverflow.com", 
             "Página principal sin barra",
             "[🏠 Inicio]"),
            
            # Sitios específicos
            ("https://es.stackoverflow.com/questions/123456", 
             "Stack Overflow español",
             "[❓ Stack Overflow en español - Pregunta - ID: 123456]"),
            
            ("https://stackexchange.com/questions/123456", 
             "Stack Exchange",
             "[❓ Pregunta - ID: 123456]"),
            
            # URLs con parámetros (deben ignorar los parámetros y extraer el contenido base)
            ("https://stackoverflow.com/questions/123456/title?answertab=votes", 
             "Pregunta con parámetros",
             "[❓ Pregunta - ID: 123456]"),
            
            ("https://stackoverflow.com/users/123456/johndoe?tab=profile", 
             "Perfil con pestaña",
             "[👤 Usuario - Usuario: 123456]"),
            
            ("https://stackoverflow.com/search?q=python&sort=votes", 
             "Búsqueda con ordenación",
             "[🔍 Búsqueda: python]"),
            
            # Secciones generales
            ("https://stackoverflow.com/users", 
             "Lista de usuarios",
             "[👤 Usuarios]"),
            
            ("https://stackoverflow.com/questions", 
             "Lista de preguntas",
             "[❓ Preguntas]"),
            
            ("https://stackoverflow.com/tags", 
             "Lista de etiquetas",
             "[🏷️ Etiquetas]"),
            
            ("https://stackoverflow.com/jobs", 
             "Lista de empleos",
             "[💼 Empleos]"),
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
                
                self.add_test_result(f"Stack Overflow - {description}", success, details)
                self.print_test_result(f"Stack Overflow - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Stack Overflow - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Stack Overflow - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = StackOverflowTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()