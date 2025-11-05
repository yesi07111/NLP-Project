from tests.base_tester import Tester, LinkProcessor

class LinkedInTester(Tester):
    """Tester específico para enlaces de LinkedIn"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de LinkedIn"""
        print("💼 Ejecutando tests de LinkedIn...")
        
        test_cases = [
            # Perfiles personales
            ("https://linkedin.com/in/johndoe", "Perfil personal básico", "[💼 Perfil de LinkedIn - ID: johndoe]"),
            ("https://www.linkedin.com/in/janesmith", "Perfil con www", "[💼 Perfil de LinkedIn - ID: janesmith]"),
            ("https://linkedin.com/in/johndoe/", "Perfil con barra final", "[💼 Perfil de LinkedIn - ID: johndoe]"),
            ("https://linkedin.com/in/johndoe/edit/", "Edición de perfil", "[💼 Perfil de LinkedIn - ID: johndoe (edit)]"),
            ("https://linkedin.com/in/johndoe/details/experience/", "Experiencia laboral", "[💼 Perfil de LinkedIn - ID: johndoe (experience)]"),
            
            # Empresas
            ("https://linkedin.com/company/microsoft", "Perfil de empresa", "[🏢 Empresa de LinkedIn - ID: microsoft]"),
            ("https://www.linkedin.com/company/google", "Empresa con www", "[🏢 Empresa de LinkedIn - ID: google]"),
            ("https://linkedin.com/company/apple/about/", "Acerca de empresa", "[🏢 Empresa de LinkedIn - ID: apple (about)]"),
            ("https://linkedin.com/company/amazon/people/", "Personas en empresa", "[🏢 Empresa de LinkedIn - ID: amazon (people)]"),
            ("https://linkedin.com/company/tesla/jobs/", "Empleos en empresa", "[🏢 Empresa de LinkedIn - ID: tesla (jobs)]"),
            
            # Publicaciones
            ("https://linkedin.com/posts/1234567890", "Publicación individual", "[📊 Publicación de LinkedIn - ID: 12345678...]"),
            ("https://www.linkedin.com/posts/9876543210", "Publicación con www", "[📊 Publicación de LinkedIn - ID: 98765432...]"),
            ("https://linkedin.com/posts/company_microsoft_1234567890", "Publicación de empresa", "[📊 Publicación de LinkedIn - ID: company_...]"),
            
            # Feed y actividad
            ("https://linkedin.com/feed/", "Feed principal", "[📰 Feed de LinkedIn]"),
            ("https://linkedin.com/feed/?filter=top", "Feed con filtro", "[📰 Feed de LinkedIn]"),
            ("https://linkedin.com/activity/", "Actividad reciente", "[📈 Actividad de LinkedIn]"),
            
            # Empleos
            ("https://linkedin.com/jobs/", "Búsqueda de empleos", "[💼 Empleo de LinkedIn]"),
            ("https://linkedin.com/jobs/view/1234567890", "Vista de empleo específico", "[💼 Empleo de LinkedIn - ID: 12345678...]"),
            ("https://www.linkedin.com/jobs/view/9876543210", "Empleo con www", "[💼 Empleo de LinkedIn - ID: 98765432...]"),
            ("https://linkedin.com/jobs/search/", "Búsqueda de empleos", "[💼 Empleo de LinkedIn (search)]"),
            ("https://linkedin.com/jobs/collections/", "Colecciones de empleos", "[💼 Empleo de LinkedIn (collections)]"),
            ("https://linkedin.com/jobs/collections/recommended/", "Empleos recomendados", "[💼 Empleo de LinkedIn - ID: recommen... (collections)]"),
            
            # Aprendizaje/Cursos
            ("https://linkedin.com/learning/", "Learning principal", "[🎓 Curso de LinkedIn]"),
            ("https://linkedin.com/learning/path/python-developer", "Ruta de aprendizaje", "[🎓 Ruta de aprendizaje de LinkedIn - ID: python-d...]"),
            ("https://linkedin.com/learning/course-123456", "Curso específico", "[🎓 Curso de LinkedIn - ID: course-1...]"), # No tiene patrón específico
            ("https://linkedin.com/learning/exam/789012", "Examen de curso", "[🎓 Curso de LinkedIn - ID: 789012 (exam)]"),
            ("https://www.linkedin.com/learning/data-science", "Learning con www", "[🎓 Curso de LinkedIn - ID: data-sci...]"),
            
            # Mensajería
            ("https://linkedin.com/messaging/", "Messaging principal", "[💬 Mensajes de LinkedIn]"),
            ("https://linkedin.com/messaging/thread/1234567890", "Hilo de mensajes", "[💬 Mensajes de LinkedIn - ID: 12345678... (thread)]"),
            ("https://www.linkedin.com/messaging/thread/9876543210", "Thread con www", "[💬 Mensajes de LinkedIn - ID: 98765432... (thread)]"),
            
            # Búsqueda
            ("https://linkedin.com/search/", "Búsqueda principal", "[🔍 Búsqueda de LinkedIn]"),
            ("https://linkedin.com/search/results/", "Resultados de búsqueda", "[🔍 Búsqueda de LinkedIn (results)]"),
            ("https://linkedin.com/search/results/people/", "Búsqueda de personas", "[🔍 Búsqueda de LinkedIn (people)]"),
            ("https://linkedin.com/search/results/content/", "Búsqueda de contenido", "[🔍 Búsqueda de LinkedIn (content)]"),
            
            # Grupos
            ("https://linkedin.com/groups/12345", "Grupo específico", "[👥 Grupo de LinkedIn - ID: 12345]"),
            ("https://www.linkedin.com/groups/67890", "Grupo con www", "[👥 Grupo de LinkedIn - ID: 67890]"),
            ("https://linkedin.com/groups/12345/discussion/", "Discusiones del grupo", "[👥 Grupo de LinkedIn - ID: 12345 (discussion)]"),
            ("https://linkedin.com/groups/12345/members/", "Miembros del grupo", "[👥 Grupo de LinkedIn - ID: 12345 (members)]"),
            
            # Eventos
            ("https://linkedin.com/events/1234567890", "Evento específico", "[📅 Evento de LinkedIn - ID: 12345678...]"),
            ("https://www.linkedin.com/events/9876543210", "Evento con www", "[📅 Evento de LinkedIn - ID: 98765432...]"),
            ("https://linkedin.com/events/1234567890/attendees/", "Asistentes a evento", "[📅 Evento de LinkedIn - ID: 12345678... (attendees)]"),
            
            # Noticias (Pulse)
            ("https://linkedin.com/pulse/", "Pulse principal", "[📰 Noticias de LinkedIn]"),
            ("https://linkedin.com/pulse/title-article-123456", "Artículo Pulse", "[📰 Noticias de LinkedIn - ID: title-ar...]"),
            ("https://www.linkedin.com/pulse/another-article-789012", "Artículo con www", "[📰 Noticias de LinkedIn - ID: another-...]"),
            
            # Sales Navigator
            ("https://linkedin.com/sales/", "Sales Navigator", "[💰 Ventas de LinkedIn]"),
            ("https://linkedin.com/sales/lead/1234567890", "Lead específico", "[💰 Ventas de LinkedIn - ID: 12345678... (lead)]"),
            ("https://linkedin.com/sales/account/9876543210", "Cuenta específica", "[💰 Ventas de LinkedIn - ID: 98765432... (account)]"),
            ("https://www.linkedin.com/sales/lead/5555555555", "Lead con www", "[💰 Ventas de LinkedIn - ID: 55555555... (lead)]"),
            
            # Learning Path alternativo
            ("https://linkedin.com/learning-path/1234567890", "Ruta de aprendizaje específica", "[🎓 Ruta de aprendizaje de LinkedIn - ID: 12345678...]"),
            ("https://www.linkedin.com/learning-path/9876543210", "Learning path con www", "[🎓 Ruta de aprendizaje de LinkedIn - ID: 98765432...]"),
            
            # Notificaciones y Red
            ("https://linkedin.com/notifications/", "Notificaciones", "[🔔 Notificaciones de LinkedIn]"),
            ("https://linkedin.com/mynetwork/", "Mi red", "[🌐 Red de LinkedIn]"),
            ("https://linkedin.com/mynetwork/invite-connect/", "Invitar conectar", "[🌐 Red de LinkedIn (invite)]"),
            
            # URLs con parámetros
            ("https://linkedin.com/in/johndoe?trk=profile", "Perfil con tracking", "[💼 Perfil de LinkedIn - ID: johndoe]"),
            ("https://linkedin.com/jobs/view/1234567890?refId=abc123", "Empleo con referencia", "[💼 Empleo de LinkedIn - ID: 12345678...]"),
            ("https://linkedin.com/search/results/people/?keywords=recruiter", "Búsqueda con parámetros", "[🔍 Búsqueda de LinkedIn (people)]"),
            
            # Página principal
            ("https://linkedin.com", "Página principal", "[💼 Inicio de LinkedIn]"),
            ("https://www.linkedin.com/", "Página principal con www", "[💼 Inicio de LinkedIn]"),
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
                
                self.add_test_result(f"LinkedIn - {description}", success, details)
                self.print_test_result(f"LinkedIn - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"LinkedIn - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"LinkedIn - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = LinkedInTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()