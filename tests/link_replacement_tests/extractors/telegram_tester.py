from tests.base_tester import Tester, LinkProcessor

class TelegramTester(Tester):
    """Tester específico para enlaces de Telegram"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        """Procesa una URL y retorna el resultado formateado"""
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Telegram"""
        print("💬 Ejecutando tests de Telegram...")
        
        test_cases = [
            # Invitaciones de grupo/canal
            ("https://t.me/joinchat/ABC123def456", 
             "Invitación de grupo básica",
             "[💬 Invitación de Telegram - ID: ABC123def456]"),
            
            ("https://telegram.me/joinchat/DEF456ghi789", 
             "Invitación con telegram.me",
             "[💬 Invitación de Telegram - ID: DEF456ghi789]"),
            
            ("https://t.me/+1234567890", 
             "Invitación con formato +",
             "[💬 Invitación de Telegram - ID: 1234567890]"),
            
            ("https://t.me/joinchat/abcdefghijk123456", 
             "Invitación con ID largo",
             "[💬 Invitación de Telegram - ID: abcdefghijk123456]"),
            
            # Canales públicos
            ("https://t.me/channelname", 
             "Canal público básico",
             "[📢 Canal de Telegram - de @channelname]"),
            
            ("https://telegram.me/username", 
             "Canal con telegram.me",
             "[📢 Canal de Telegram - de @username]"),
            
            ("https://t.me/@channelname", 
             "Canal con @",
             "[📢 Canal de Telegram - de @channelname]"),
            
            ("https://t.me/technews", 
             "Canal de noticias",
             "[📢 Canal de Telegram - de @technews]"),
            
            ("https://t.me/memeschannel", 
             "Canal de memes",
             "[📢 Canal de Telegram - de @memeschannel]"),
            
            # Mensajes específicos
            ("https://t.me/s/channelname/123", 
             "Mensaje específico con /s/",
             "[📨 Mensaje de Telegram - de @channelname, Mensaje: 123]"),
            
            ("https://t.me/channelname/456", 
             "Mensaje en canal",
             "[📨 Mensaje en canal de Telegram - de @channelname, Mensaje: 456]"),
            
            ("https://telegram.me/username/789", 
             "Mensaje con telegram.me",
             "[📨 Mensaje en canal de Telegram - de @username, Mensaje: 789]"),
            
            ("https://t.me/channelname/123456789", 
             "Mensaje con ID largo",
             "[📨 Mensaje en canal de Telegram - de @channelname, Mensaje: 123456789]"),
            
            # Mensajes en canales privados
            ("https://t.me/c/123456789/123", 
             "Mensaje en canal privado",
             "[📨 Mensaje en canal de Telegram - ID: 123456789, Mensaje: 123]"),
            
            ("https://t.me/c/987654321/456", 
             "Canal privado con ID diferente",
             "[📨 Mensaje en canal de Telegram - ID: 987654321, Mensaje: 456]"),
            
            # Bots con parámetros start
            ("https://t.me/mybot?start=123", 
             "Bot con parámetro start",
             "[🤖 Bot - Inicio de Telegram - de @mybot, ID: 123]"),
            
            ("https://t.me/@mybot?start=welcome", 
             "Bot con @ y start",
             "[🤖 Bot - Inicio de Telegram - de @mybot, ID: welcome]"),
            
            ("https://telegram.me/echo_bot?start=hello", 
             "Bot con telegram.me",
             "[🤖 Bot - Inicio de Telegram - de @echo_bot, ID: hello]"),
            
            ("https://t.me/mybot?start=ref_12345", 
             "Bot con referencia",
             "[🤖 Bot - Inicio de Telegram - de @mybot, ID: ref_12345]"),
            
            # Bots con parámetros game
            ("https://t.me/gamebot?game=treasurehunt", 
             "Bot con juego",
             "[🎮 Bot - Juego de Telegram - de @gamebot, ID: treasurehunt]"),
            
            ("https://t.me/@gamebot?game=quiz", 
             "Bot juego con @",
             "[🎮 Bot - Juego de Telegram - de @gamebot, ID: quiz]"),
            
            # Stickers
            ("https://t.me/addstickers/mypack", 
             "Paquete de stickers",
             "[🖼️ Stickers de Telegram - ID: mypack]"),
            
            ("https://t.me/addstickers/animals", 
             "Stickers de animales",
             "[🖼️ Stickers de Telegram - ID: animals]"),
            
            ("https://telegram.me/addstickers/emoji", 
             "Stickers con telegram.me",
             "[🖼️ Stickers de Telegram - ID: emoji]"),
            
            # Temas
            ("https://t.me/addtheme/darkmode", 
             "Tema dark mode",
             "[🎨 Tema de Telegram - ID: darkmode]"),
            
            ("https://t.me/addtheme/blueocean", 
             "Tema azul",
             "[🎨 Tema de Telegram - ID: blueocean]"),
            
            # Emojis
            ("https://t.me/addemoji/custompack", 
             "Paquete de emojis",
             "[😀 Emoji de Telegram - ID: custompack]"),
            
            # Login
            ("https://t.me/login/123456", 
             "Login con código",
             "[🔑 Login de Telegram - ID: 123456]"),
            
            ("https://telegram.me/login/auth", 
             "Login auth",
             "[🔑 Login de Telegram - ID: auth]"),
            
            # Proxy
            ("https://t.me/proxy?server=1.2.3.4&port=443", 
             "Proxy con servidor",
             "[🔌 Proxy de Telegram - ID: 1.2.3.4]"),
            
            ("https://t.me/proxy?server=proxy.example.com", 
             "Proxy con dominio",
             "[🔌 Proxy de Telegram - ID: proxy.example.com]"),
            
            # Share
            ("https://t.me/share/url?url=https://example.com", 
             "Compartir URL",
             "[↗️ Compartir de Telegram - ID: https://example.com]"),
            
            ("https://t.me/share/url?text=Hello", 
             "Compartir texto",
             "[↗️ Compartir de Telegram]"),
            
            # Donate
            ("https://t.me/donate", 
             "Donación",
             "[💳 Donación de Telegram]"),
            
            # Contact
            ("https://t.me/contact?contact=123", 
             "Contacto",
             "[👤 Contacto de Telegram]"),
            
            ("https://t.me/@supportbot?contact=help", 
             "Contacto con bot",
             "[👤 Contacto de Telegram - de @supportbot]"),
            
            # Phone
            ("https://t.me/phone?phone=123456789", 
             "Teléfono como parámetro",
             "[📞 Teléfono de Telegram - ID: 123456789]"),
            
            # Dominios alternativos
            ("https://telegram.dog/channelname", 
             "Dominio telegram.dog",
             "[📢 Canal de Telegram - de @channelname]"),
            
            ("https://telesco.pe/channelname", 
             "Dominio telesco.pe",
             "[📢 Canal de Telegram - de @channelname]"),
            
            ("https://telegram.dog/joinchat/ABC123", 
             "Invitación en telegram.dog",
             "[💬 Invitación de Telegram - ID: ABC123]"),
            
            # URLs con múltiples parámetros
            ("https://t.me/bot?start=123&ref=abc", 
             "Bot con múltiples parámetros",
             "[🤖 Bot - Inicio de Telegram - de @bot, ID: 123]"),
            
            # Página principal
            ("https://t.me/", 
             "Página principal",
             "[💬 Inicio de Telegram]"),
            
            ("https://telegram.me", 
             "Página principal sin barra",
             "[💬 Inicio de Telegram]"),
            
            # URLs que no coinciden con ningún patrón específico
            ("https://t.me/support", 
             "Soporte",
             "[📢 Canal de Telegram - de @support]"),
            
            ("https://t.me/faq", 
             "FAQ",
             "[📢 Canal de Telegram - de @faq]"),
            
            ("https://t.me/blog", 
             "Blog",
             "[📢 Canal de Telegram - de @blog]"),
            
            ("https://t.me/telegram", 
             "Canal oficial",
             "[📢 Canal de Telegram - de @telegram]"),
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
                
                self.add_test_result(f"Telegram - {description}", success, details)
                self.print_test_result(f"Telegram - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Telegram - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"Telegram - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = TelegramTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()