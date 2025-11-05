from tests.base_tester import Tester, LinkProcessor

class GoogleTester(Tester):
    """Tester específico para enlaces de Google"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Google"""
        print("🧪 Ejecutando tests de Google...")
        
        test_cases = [
            # Búsquedas generales
            ("https://www.google.com/search?q=python+programming", "Búsqueda general", "[🔍 Búsqueda: python programming]"),
            ("https://google.com/search?q=openai&hl=es", "Búsqueda en español", "[🔍 Búsqueda: openai]"),
            
            # Búsquedas especializadas
            ("https://google.com/search?q=cats&tbm=isch", "Búsqueda de imágenes", "[🖼️ Búsqueda de imágenes: cats]"),
            ("https://google.com/search?q=music&tbm=vid", "Búsqueda de videos", "[🎬 Búsqueda de videos: music]"),
            ("https://google.com/search?q=news&tbm=nws", "Búsqueda de noticias", "[📰 Búsqueda de noticias: news]"),
            ("https://google.com/search?q=books&tbm=bks", "Búsqueda de libros", "[📚 Búsqueda de libros: books]"),
            ("https://google.com/search?q=restaurant&tbm=lcl", "Búsqueda en maps", "[🗺️ Búsqueda en Maps: restaurant]"),
            ("https://google.com/search?q=laptop&tbm=shop", "Búsqueda shopping", "[🛒 Shopping: laptop]"),
            ("https://google.com/search?q=flights&tbm=flm", "Búsqueda de vuelos", "[✈️ Vuelos: flights]"),
            ("https://google.com/search?q=stocks&tbm=fin", "Búsqueda financiera", "[💹 Finanzas: stocks]"),
            
            # Google Drive
            ("https://drive.google.com/drive/folders/1ABC123def456", "Carpeta de Drive", "[📁 Carpeta - ID: 1ABC123def456]"),
            ("https://drive.google.com/file/d/1XYZ789abc012/view", "Archivo de Drive", "[📁 Archivo - ID: 1XYZ789abc012]"),
            ("https://drive.google.com/drive/u/0/folders/1DEF456ghi789", "Carpeta con usuario", "[📁 Carpeta - ID: 1DEF456ghi789]"),
            ("https://drive.google.com/open?id=1GHI789jkl012", "Drive con parámetro ID", "[📁 Archivo - ID: 1GHI789jkl012]"),
            ("https://drive.google.com/drive/mobile", "Drive móvil", "[📁 Móvil]"),
            ("https://drive.google.com/drive/search?q=document", "Búsqueda en Drive", "[📁 Buscar: document]"),
            ("https://drive.google.com/drive/recent", "Drive reciente", "[📁 Reciente]"),
            ("https://drive.google.com/drive/shared-with-me", "Compartido conmigo", "[📁 Compartido]"),
            ("https://drive.google.com/drive/trash", "Papelera de Drive", "[📁 Papelera]"),
            
            # Google Docs
            ("https://docs.google.com/document/d/1DOC123edit/view", "Documento de Google", "[📄 Documento - ID: 1DOC123edit]"),
            ("https://docs.google.com/spreadsheets/d/1SHEET456/edit", "Hoja de cálculo", "[📊 Hoja de cálculo - ID: 1SHEET456]"),
            ("https://docs.google.com/presentation/d/1SLIDE789/edit", "Presentación", "[🎞️ Presentación - ID: 1SLIDE789]"),
            ("https://docs.google.com/forms/d/1FORM012/edit", "Formulario", "[📝 Formulario - ID: 1FORM012]"),
            ("https://docs.google.com/drawings/d/1DRAW345/edit", "Dibujo", "[🎨 Dibujo - ID: 1DRAW345]"),
            
            # Gmail
            ("https://mail.google.com/mail/u/0/#inbox", "Bandeja de entrada", "[📧 Bandeja de entrada]"),
            ("https://gmail.com/#inbox/123", "Bandeja específica", "[📧 Bandeja de entrada]"),
            ("https://mail.google.com/mail/u/0/#compose", "Redactar correo", "[📧 Redactar]"),
            ("https://gmail.com/#sent", "Enviados", "[📧 Enviados]"),
            ("https://gmail.com/#drafts", "Borradores", "[📧 Borradores]"),
            ("https://gmail.com/#starred", "Destacados", "[📧 Destacados]"),
            ("https://gmail.com/#spam", "Spam", "[📧 Spam]"),
            ("https://gmail.com/#trash", "Papelera", "[📧 Papelera]"),
            ("https://gmail.com/#label/Work", "Etiqueta específica", "[📧 Etiqueta - ID: Work]"),
            
            # Google Maps
            ("https://maps.google.com/maps?q=New+York", "Búsqueda en Maps", "[🗺️ Buscar: New York]"),
            ("https://google.com/maps/place/Eiffel+Tower", "Lugar específico", "[🗺️ Lugar - ID: Eiffel+Tower]"),
            ("https://maps.google.com/maps/dir/Paris/London", "Direcciones", "[🗺️ Direcciones - ID: Paris/London]"),
            ("https://google.com/maps/search/restaurants+near+me", "Búsqueda lugares", "[🗺️ Buscar: restaurants+near+me]"),
            ("https://maps.google.com/maps/contributions", "Contribuciones", "[🗺️ Contribuciones]"),
            ("https://maps.google.com/maps/reviews", "Reseñas", "[🗺️ Reseñas]"),
            
            # Google Photos
            ("https://photos.google.com/photo/1PHOTO123", "Foto específica", "[🖼️ Foto - ID: 1PHOTO123]"),
            ("https://photos.google.com/album/1ALBUM456", "Álbum", "[🖼️ Álbum - ID: 1ALBUM456]"),
            ("https://photos.google.com/search/dogs", "Búsqueda en Fotos", "[🖼️ Buscar: dogs]"),
            ("https://photos.google.com/memories", "Recuerdos", "[🖼️ Recuerdos]"),
            ("https://photos.google.com/archive", "Archivo", "[🖼️ Archivo]"),
            
            # Google Calendar
            ("https://calendar.google.com/calendar/r/eventedit?text=Meeting", "Evento de calendario", "[📅 Evento]"),
            ("https://calendar.google.com/calendar/u/0/r", "Vista principal", "[📅 Calendar]"),
            ("https://calendar.google.com/calendar?action=create", "Crear evento", "[📅 Calendar]"),
            
            # Google Meet
            ("https://meet.google.com/abc-defg-hij", "Reunión de Meet", "[💻 Reunión - ID: abc-defg-hij]"),
            ("https://meet.google.com/new", "Nueva reunión", "[💻 Nueva reunión]"),
            
            # Google Classroom
            ("https://classroom.google.com/c/1COURSE123", "Curso de Classroom", "[🎒 Curso - ID: 1COURSE123]"),
            ("https://classroom.google.com/u/0/h", "Classroom principal", "[🎒 Classroom]"),
            
            # Google Sites
            ("https://sites.google.com/view/mysite", "Sitio de Google", "[🌐 Sitio - ID: mysite]"),
            ("https://sites.google.com/site/oldsite", "Sitio antiguo", "[🌐 Sitio antiguo - ID: oldsite]"),
            
            # Google Keep
            ("https://keep.google.com", "Google Keep", "[📝 Keep]"),
            ("https://keep.google.com/u/0/", "Keep con usuario", "[📝 Keep]"),
            
            # Google Scholar
            ("https://scholar.google.com/scholar?q=AI", "Google Scholar", "[🎓 Búsqueda académica: AI]"),
            ("https://scholar.google.com/citations?user=USER123", "Perfil académico", "[🎓 Perfil académico - ID: USER123]"),
            
            # Google Play
            ("https://play.google.com/store/apps/details?id=com.whatsapp", "App en Play Store", "[🛒 App - ID: com.whatsapp]"),
            ("https://play.google.com/store/books/details?id=BOOK123", "Libro en Play", "[🛒 Libro - ID: BOOK123]"),
            
            # Google News
            ("https://news.google.com", "Google News", "[📰 Noticias]"),
            ("https://news.google.com/topstories", "Noticias principales", "[📰 Noticias principales]"),
            
            # My Account
            ("https://myaccount.google.com", "Mi Cuenta", "[👤 Mi Cuenta]"),
            ("https://myaccount.google.com/personal-info", "Información personal", "[👤 Información personal]"),
            ("https://myaccount.google.com/security", "Seguridad", "[👤 Seguridad]"),
            
            # Otros servicios
            ("https://translate.google.com", "Google Translate", "[🔤 Traductor]"),
            ("https://earth.google.com", "Google Earth", "[🌍 Earth]"),
            ("https://takeout.google.com", "Google Takeout", "[📦 Takeout]"),
            ("https://contacts.google.com", "Contactos", "[👤 Contactos]"),
            
            # URLs cortas
            ("https://goo.gl/abc123", "URL corta goo.gl", "[🔗 Enlace corto - ID: abc123]"),
            ("https://g.co/def456", "URL corta g.co", "[🔗 Enlace corto - ID: def456]"),
            
            # Dominios regionales (solo algunos ejemplos)
            ("https://google.es/search?q=españa", "Google España", "[🔍 Búsqueda: españa]"),
            ("https://google.com.mx/search?q=méxico", "Google México", "[🔍 Búsqueda: méxico]"),
            ("https://google.co.uk/search?q=london", "Google Reino Unido", "[🔍 Búsqueda: london]"),
        ]
        
        for url, description, expected in test_cases:
            try:
                result = self.processor.process_url(url)
                success = result.strip() == expected.strip()
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected,
                    'Coincide': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Google - {description}", success, details)
                self.print_test_result(f"Google - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Google - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Google - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = GoogleTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()