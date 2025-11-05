# tests/whatsapp_tester.py
from tests.base_tester import Tester, LinkProcessor

class WhatsAppTester(Tester):
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _process_url(self, url: str) -> str:
        result = self.processor.process_url(url)
        return result if result else "ERROR: No se pudo procesar la URL"
    
    def run_all_tests(self):
        print("💬 Ejecutando tests de WhatsApp...")
        
        test_cases = [
            # Canales
            ("https://whatsapp.com/channel/1234567890", 
             "Canal oficial",
             "[💬 Canal de WhatsApp - ID: 1234567890]"),
            
            ("https://www.whatsapp.com/channel/9876543210", 
             "Canal con www",
             "[💬 Canal de WhatsApp - ID: 9876543210]"),
            
            ("https://whatsapp.com/channel/1234567890/info", 
             "Info del canal",
             "[💬 Info del canal de WhatsApp - ID: 1234567890]"),
            
            # Invitaciones
            ("https://whatsapp.com/invite/ABCDEFGHIJ", 
             "Invitación de grupo",
             "[📨 Invitación de WhatsApp - ID: ABCDEFGHIJ]"),
            
            ("https://whatsapp.com/invite/KLMNOPQRST", 
             "Otra invitación",
             "[📨 Invitación de WhatsApp - ID: KLMNOPQRST]"),
            
            ("https://whatsapp.com/invite/ABCDEFGHIJ?context=group", 
             "Invitación con contexto",
             "[📨 Invitación de WhatsApp - ID: ABCDEFGHIJ]"),
            
            # Chats directos (wa.me)
            ("https://wa.me/1234567890", 
             "Chat directo",
             "[💬 Chat de WhatsApp]"),
            
            ("https://wa.me/15551234567", 
             "Chat con número internacional",
             "[💬 Chat de WhatsApp]"),
            
            ("https://wa.me/1234567890?text=Hello", 
             "Chat con texto",
             "[✉️ Chat con texto de WhatsApp]"),
            
            ("https://wa.me/15551234567?text=Hi%20there", 
             "Chat con texto codificado",
             "[✉️ Chat con texto de WhatsApp]"),
            
            ("https://wa.me/1234567890?text=Hello%20World", 
             "Chat con texto largo",
             "[✉️ Chat con texto de WhatsApp]"),
            
            ("https://wa.me/1234567890?text=Hola%20Mundo", 
             "Chat con texto español",
             "[✉️ Chat con texto de WhatsApp]"),
            
            # Business
            ("https://whatsapp.com/business", 
             "WhatsApp Business",
             "[💼 WhatsApp Business de WhatsApp]"),
            
            ("https://whatsapp.com/business/profile", 
             "Perfil Business",
             "[👔 Perfil Business de WhatsApp]"),
            
            ("https://whatsapp.com/business/catalog", 
             "Catálogo Business",
             "[📋 Catálogo Business de WhatsApp]"),
            
            ("https://whatsapp.com/business/api", 
             "API Business",
             "[🔧 API Business de WhatsApp]"),
            
            ("https://business.whatsapp.com", 
             "Business principal",
             "[🏢 Business principal de WhatsApp]"),
            
            ("https://business.whatsapp.com/product", 
             "Business producto",
             "[📦 Business producto de WhatsApp]"),
            
            # Contactos
            ("https://whatsapp.com/contact/1234567890", 
             "Contacto",
             "[👤 Contacto de WhatsApp - ID: 1234567890]"),
            
            ("https://whatsapp.com/contact/15551234567", 
             "Contacto internacional",
             "[👤 Contacto de WhatsApp - ID: 15551234567]"),
            
            ("https://whatsapp.com/contact/1234567890?name=John", 
             "Contacto con nombre",
             "[👤 Contacto de WhatsApp - ID: 1234567890]"),
            
            # API
            ("https://whatsapp.com/api", 
             "API",
             "[🔌 API de WhatsApp]"),
            
            ("https://whatsapp.com/api/endpoint", 
             "Endpoint API",
             "[🔌 Endpoint API de WhatsApp - ID: endpoint]"),
            
            ("https://whatsapp.com/api/v1/endpoint", 
             "API versión específica",
             "[🔌 API versión específica de WhatsApp - ID: 1]"),
            
            # Blog
            ("https://whatsapp.com/blog", 
             "Blog",
             "[📰 Blog de WhatsApp]"),
            
            ("https://whatsapp.com/blog/new-features", 
             "Post del blog",
             "[📰 Post del blog de WhatsApp - ID: new-features]"),
            
            ("https://whatsapp.com/blog/2024/announcement", 
             "Blog con fecha",
             "[📰 Blog con fecha de WhatsApp - ID: 2024]"),
            
            # Soporte
            ("https://whatsapp.com/support", 
             "Soporte",
             "[🛟 Soporte de WhatsApp]"),
            
            ("https://whatsapp.com/support/help", 
             "Sección ayuda",
             "[🛟 Sección ayuda de WhatsApp - ID: help]"),
            
            ("https://whatsapp.com/support/privacy", 
             "Soporte privacidad",
             "[🛟 Sección ayuda de WhatsApp - ID: privacy]"),
            
            ("https://whatsapp.com/support/contact-us", 
             "Soporte contactar",
             "[🛟 Soporte contactar de WhatsApp]"),
            
            # Descargas
            ("https://whatsapp.com/download", 
             "Descargar",
             "[📥 Descargar de WhatsApp]"),
            
            ("https://whatsapp.com/download/windows", 
             "Descargar Windows",
             "[💻 Descargar Windows de WhatsApp]"),
            
            ("https://whatsapp.com/download/mac", 
             "Descargar Mac",
             "[💻 Descargar Mac de WhatsApp]"),
            
            ("https://whatsapp.com/download/android", 
             "Descargar Android",
             "[📱 Descargar Android de WhatsApp]"),
            
            ("https://whatsapp.com/download/ios", 
             "Descargar iOS",
             "[📱 Descargar iOS de WhatsApp]"),
            
            # Web
            ("https://whatsapp.com/web", 
             "Web",
             "[🌐 Web de WhatsApp]"),
            
            ("https://web.whatsapp.com", 
             "Web app",
             "[🖥️ Web app de WhatsApp]"),
            
            ("https://web.whatsapp.com/", 
             "Web app con barra",
             "[🖥️ Web app de WhatsApp]"),
            
            # Status
            ("https://whatsapp.com/status/1234567890", 
             "Estado",
             "[📊 Estado de WhatsApp - ID: 1234567890]"),
            
            ("https://whatsapp.com/status/1234567890/view", 
             "Ver estado",
             "[📊 Ver estado de WhatsApp - ID: 1234567890]"),
            
            # Broadcast
            ("https://whatsapp.com/broadcast/1234567890", 
             "Broadcast",
             "[📢 Broadcast de WhatsApp - ID: 1234567890]"),
            
            ("https://whatsapp.com/broadcast/1234567890/send", 
             "Enviar broadcast",
             "[📢 Enviar broadcast de WhatsApp - ID: 1234567890]"),
            
            # QR
            ("https://whatsapp.com/qr/abcdef123456", 
             "Código QR",
             "[🔲 Código QR de WhatsApp - ID: abcdef123456]"),
            
            ("https://whatsapp.com/qr/abcdef123456/download", 
             "Descargar QR",
             "[🔲 Descargar QR de WhatsApp - ID: abcdef123456]"),
            
            # Página principal
            ("https://whatsapp.com", 
             "Página principal",
             "[🏠 Inicio de WhatsApp]"),
            
            ("https://whatsapp.com/", 
             "Página principal con barra",
             "[🏠 Inicio de WhatsApp]"),
            
            ("https://www.whatsapp.com", 
             "Página principal con www",
             "[🏠 Inicio de WhatsApp]"),
            
            # Características y políticas
            ("https://whatsapp.com/features", 
             "Características",
             "[⭐ Características de WhatsApp]"),
            
            ("https://whatsapp.com/security", 
             "Seguridad",
             "[🔒 Seguridad de WhatsApp]"),
            
            ("https://whatsapp.com/privacy", 
             "Privacidad",
             "[🛡️ Privacidad de WhatsApp]"),
            
            ("https://whatsapp.com/terms", 
             "Términos",
             "[📄 Términos de WhatsApp]"),
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
                
                self.add_test_result(f"WhatsApp - {description}", success, details)
                self.print_test_result(f"WhatsApp - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"WhatsApp - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description,
                    'Esperado': expected
                })
                self.print_test_result(f"WhatsApp - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = WhatsAppTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()