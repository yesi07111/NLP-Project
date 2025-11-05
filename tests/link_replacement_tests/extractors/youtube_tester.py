# tests/youtube_tester.py
from tests.base_tester import Tester, LinkProcessor

class YouTubeTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("🎥 Ejecutando tests de YouTube...")
        
        test_cases = [
            # Videos básicos
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", 
             "Video normal",
             "[🎥 Video de YouTube - ID: dQw4w9WgXcQ]"),
            
            ("https://www.youtube.com/watch?v=abc123def456", 
             "Video con www",
             "[🎥 Video de YouTube - ID: abc123def456]"),
            
            ("https://youtube.com/watch?v=xyz789&feature=share", 
             "Video con parámetros",
             "[🎥 Video de YouTube - ID: xyz789]"),
            
            # URLs cortas
            ("https://youtu.be/dQw4w9WgXcQ", 
             "URL corta youtu.be",
             "[🎥 Video de YouTube - ID: dQw4w9WgXcQ]"),
            
            ("https://youtu.be/abc123def456", 
             "Otra URL corta",
             "[🎥 Video de YouTube - ID: abc123def456]"),
            
            # Shorts
            ("https://youtube.com/shorts/AbCdEfGhIjK", 
             "Short",
             "[🎬 Short de YouTube - ID: AbCdEfGhIjK]"),
            
            ("https://youtube.com/shorts/ZyXwVuTsRqP", 
             "Otro short",
             "[🎬 Short de YouTube - ID: ZyXwVuTsRqP]"),
            
            # Embeds
            ("https://youtube.com/embed/dQw4w9WgXcQ", 
             "Video embed",
             "[📺 Video incrustado de YouTube - ID: dQw4w9WgXcQ]"),
            
            ("https://youtube.com/embed/abc123def456", 
             "Otro embed",
             "[📺 Video incrustado de YouTube - ID: abc123def456]"),
            
            # Live streams
            ("https://youtube.com/live/AbCdEfGhIjK", 
             "Transmisión en vivo",
             "[🔴 Transmisión en vivo de YouTube - ID: AbCdEfGhIjK]"),
            
            ("https://youtube.com/live/ZyXwVuTsRqP", 
             "Otra transmisión",
             "[🔴 Transmisión en vivo de YouTube - ID: ZyXwVuTsRqP]"),
            
            # Formato /v/
            ("https://youtube.com/v/abc123def456", 
             "Video formato /v/",
             "[🎥 Video de YouTube - ID: abc123def456]"),
            
            # Canales
            ("https://youtube.com/c/ChannelName", 
             "Canal con /c/",
             "[📺 Canal de YouTube - Canal: ChannelName]"),
            
            ("https://youtube.com/c/TechReviews", 
             "Canal tech",
             "[📺 Canal de YouTube - Canal: TechReviews]"),
            
            ("https://youtube.com/channel/UC1234567890abcdef", 
             "Canal con ID",
             "[📺 Canal de YouTube - Canal ID: UC1234567890abcdef]"),
            
            ("https://youtube.com/channel/UCabcdef1234567890", 
             "Otro canal con ID",
             "[📺 Canal de YouTube - Canal ID: UCabcdef1234567890]"),
            
            ("https://youtube.com/user/Username", 
             "Canal con /user/",
             "[📺 Canal de YouTube - Canal: Username]"),
            
            ("https://youtube.com/user/TechGuru", 
             "Usuario específico",
             "[📺 Canal de YouTube - Canal: TechGuru]"),
            
            ("https://youtube.com/@username", 
             "Canal con @",
             "[📺 Canal de YouTube - Canal: @username]"),
            
            ("https://youtube.com/@TechChannel", 
             "Canal tech con @",
             "[📺 Canal de YouTube - Canal: @TechChannel]"),
            
            # Playlists
            ("https://youtube.com/watch?v=abc123&list=PL1234567890", 
             "Video con playlist",
             "[🎥 Video de YouTube - ID: abc123 - Playlist: PL1234567890]"),
            
            ("https://youtube.com/playlist?list=PL1234567890", 
             "Solo playlist",
             "[📋 Lista de reproducción de YouTube - ID: PL1234567890]"),
            
            ("https://youtube.com/playlist?list=PLabcdef123456", 
             "Otra playlist",
             "[📋 Lista de reproducción de YouTube - ID: PLabcdef123456]"),
            
            # Páginas principales
            ("https://youtube.com", 
             "Página principal",
             "[🏠 Inicio de YouTube]"),
            
            ("https://youtube.com/", 
             "Página principal con barra",
             "[🏠 Inicio de YouTube]"),
            
            ("https://www.youtube.com", 
             "Página principal con www",
             "[🏠 Inicio de YouTube]"),
            
            # YouTube Music
            ("https://music.youtube.com", 
             "YouTube Music principal",
             "[🎵 YouTube Music de YouTube]"),
            
            ("https://music.youtube.com/watch?v=abc123def456", 
             "YouTube Music video",
             "[🎵 Video en YouTube Music de YouTube - ID: abc123def456]"),
            
            ("https://music.youtube.com/playlist?list=PL1234567890", 
             "YouTube Music playlist",
             "[🎵 Lista en YouTube Music de YouTube - ID: PL1234567890]"),
            
            # YouTube Kids
            ("https://youtubekids.com", 
             "YouTube Kids principal",
             "[🧒 YouTube Kids de YouTube]"),
            
            ("https://youtubekids.com/watch?v=abc123def456", 
             "YouTube Kids video",
             "[🧒 Video en YouTube Kids de YouTube - ID: abc123def456]"),
            
            # YouTube Studio
            ("https://studio.youtube.com", 
             "YouTube Studio",
             "[⚙️ YouTube Studio de YouTube]"),
            
            ("https://studio.youtube.com/channel/UC1234567890", 
             "Studio canal específico",
             "[⚙️ YouTube Studio de YouTube]"),
            
            # Videos con tiempo
            ("https://youtube.com/watch?v=abc123&t=120", 
             "Video con tiempo",
             "[🎥 Video de YouTube - ID: abc123 - Tiempo: 120]"),
            
            ("https://youtube.com/watch?v=abc123&start=120", 
             "Video con start",
             "[🎥 Video de YouTube - ID: abc123 - Tiempo: 120]"),
            
            ("https://youtu.be/abc123?t=60", 
             "URL corta con tiempo",
             "[🎥 Video de YouTube - ID: abc123 - Tiempo: 60]"),
            
            ("https://youtube.com/embed/abc123?start=120", 
             "Embed con tiempo",
             "[📺 Video incrustado de YouTube - ID: abc123 - Tiempo: 120]"),
            
            # Secciones de canales
            ("https://youtube.com/c/ChannelName/videos", 
             "Canal - videos",
             "[📺 Canal de YouTube - Canal: ChannelName - Sección: Videos]"),
            
            ("https://youtube.com/c/ChannelName/playlists", 
             "Canal - playlists",
             "[📺 Canal de YouTube - Canal: ChannelName - Sección: Playlists]"),
            
            ("https://youtube.com/c/ChannelName/community", 
             "Canal - comunidad",
             "[📺 Canal de YouTube - Canal: ChannelName - Sección: Comunidad]"),
            
            ("https://youtube.com/c/ChannelName/about", 
             "Canal - acerca de",
             "[📺 Canal de YouTube - Canal: ChannelName - Sección: Acerca de]"),
            
            ("https://youtube.com/channel/UC1234567890/videos", 
             "Canal ID - videos",
             "[📺 Canal de YouTube - Canal ID: UC1234567890 - Sección: Videos]"),
            
            ("https://youtube.com/user/Username/videos", 
             "Usuario - videos",
             "[📺 Canal de YouTube - Canal: Username - Sección: Videos]"),
            
            ("https://youtube.com/@username/videos", 
             "Canal @ - videos",
             "[📺 Canal de YouTube - Canal: @username - Sección: Videos]"),
            
            # Feeds
            ("https://youtube.com/feed/subscriptions", 
             "Feed suscripciones",
             "[📰 Feed de YouTube - Feed: Suscripciones]"),
            
            ("https://youtube.com/feed/trending", 
             "Trending",
             "[📰 Feed de YouTube - Feed: Trending]"),
            
            ("https://youtube.com/feed/history", 
             "Historial",
             "[📰 Feed de YouTube - Feed: Historial]"),
            
            ("https://youtube.com/feed/library", 
             "Biblioteca",
             "[📰 Feed de YouTube - Feed: Biblioteca]"),
            
            # Búsqueda
            ("https://youtube.com/results?search_query=python", 
             "Resultados búsqueda",
             "[🔍 Búsqueda de YouTube - Búsqueda: python]"),
            
            ("https://youtube.com/results?search_query=web+development", 
             "Búsqueda desarrollo web",
             "[🔍 Búsqueda de YouTube - Búsqueda: web development]"),
            
            # Hashtags
            ("https://youtube.com/hashtag/python", 
             "Hashtag Python",
             "[🏷️ Hashtag de YouTube - #python]"),
            
            ("https://youtube.com/hashtag/technology", 
             "Hashtag tecnología",
             "[🏷️ Hashtag de YouTube - #technology]"),
            
            # Páginas específicas
            ("https://youtube.com/gaming", 
             "YouTube Gaming",
             "[🎮 Gaming de YouTube]"),
            
            ("https://youtube.com/movies", 
             "Películas",
             "[🎬 Películas de YouTube]"),
            
            ("https://youtube.com/tv", 
             "YouTube TV",
             "[📡 TV de YouTube]"),
            
            ("https://youtube.com/creators", 
             "Creadores",
             "[✨ Creadores de YouTube]"),
            
            ("https://youtube.com/ads", 
             "Anuncios",
             "[📢 Anuncios de YouTube]"),
            
            ("https://youtube.com/account", 
             "Cuenta",
             "[👤 Cuenta de YouTube]"),
            
            ("https://youtube.com/premium", 
             "YouTube Premium",
             "[⭐ Premium de YouTube]"),
            
            ("https://youtube.com/originals", 
             "YouTube Originals",
             "[🎭 Originals de YouTube]"),
            
            ("https://youtube.com/education", 
             "Educación",
             "[📚 Educación de YouTube]"),
            
            ("https://youtube.com/new", 
             "Subir video",
             "[⬆️ Subir video de YouTube]"),
            
            ("https://youtube.com/upload", 
             "Upload",
             "[⬆️ Upload de YouTube]"),
            
            ("https://youtube.com/live_dashboard", 
             "Dashboard en vivo",
             "[📊 Dashboard en vivo de YouTube]"),
            
            ("https://youtube.com/analytics", 
             "Analytics",
             "[📈 Analytics de YouTube]"),
            
            ("https://youtube.com/comment", 
             "Comentarios",
             "[💬 Comentarios de YouTube]"),
            
            ("https://youtube.com/subscribe", 
             "Suscribirse",
             "[✅ Suscribirse de YouTube]"),
            
            ("https://youtube.com/share", 
             "Compartir",
             "[↗️ Compartir de YouTube]"),
            
            ("https://youtube.com/redirect", 
             "Redirect",
             "[↪️ Redirect de YouTube]"),
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
                
                self.add_test_result(f"YouTube - {description}", success, details)
                self.print_test_result(f"YouTube - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"YouTube - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"YouTube - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = YouTubeTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()