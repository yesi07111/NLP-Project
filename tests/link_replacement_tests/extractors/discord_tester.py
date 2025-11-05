from tests.base_tester import Tester, LinkProcessor

class DiscordTester(Tester):
    """Tester específico para enlaces de Discord con verificaciones precisas"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def _get_expected_result(self, url, description):
        """Define los resultados esperados para cada caso de prueba"""
        expected_map = {
            # Invitaciones
            "https://discord.gg/abc123": "[🎮 Invitación de Discord - Servidor: abc123]",
            "https://discord.com/invite/xyz789": "[🎮 Invitación de Discord - Servidor: xyz789]",
            
            # Canales y servidores
            "https://discord.com/channels/1234567890/1234567891": "[💬 Canal de Discord - Servidor: 1234567890 (Canal: 1234567891)]",
            "https://discord.com/channels/1234567890": "[💬 Canal de Discord - Servidor: 1234567890]",
            
            # Tienda
            "https://discord.com/store": "[🛒 Tienda de Discord]",
            "https://discord.com/store/skus/123": "[🛒 SKUs de tienda de Discord - Servidor: 123]",
            "https://discord.com/store/published-listings": "[🛒 Listados de tienda de Discord]",
            
            # Nitro y servicios
            "https://discord.com/nitro": "[💎 Nitro de Discord]",
            "https://discord.com/servers": "[🖥️ Servidores de Discord]",
            
            # Aplicaciones
            "https://discord.com/application-directory": "[📱 Aplicaciones de Discord]",
            "https://discord.com/application-directory/1234567890": "[📱 Aplicaciones de Discord - Servidor: 1234567890]",
            
            # Biblioteca y descargas
            "https://discord.com/library": "[📚 Biblioteca de Discord]",
            "https://discord.com/download": "[📥 Descargar de Discord]",
            
            # Blog y soporte
            "https://discord.com/blog": "[📰 Blog de Discord]",
            "https://discord.com/blog/post-slug": "[📰 Blog de Discord - Servidor: post-slug]",
            "https://discord.com/support": "[🛟 Soporte de Discord]",
            "https://discord.com/support/category": "[🛟 Soporte de Discord - Servidor: category]",
            
            # Legal
            "https://discord.com/terms": "[📄 Términos de Discord]",
            "https://discord.com/privacy": "[🔒 Privacidad de Discord]",
            "https://discord.com/guidelines": "[📋 Guías de Discord]",
            
            # Status y sistemas
            "https://discord.com/status": "[📊 Estado de Discord]",
            
            # Modales y OAuth
            "https://discord.com/modal/some-type": "[📝 Modal de Discord - Servidor: some-type]",
            "https://discord.com/oauth2/authorize": "[🔐 Autorización OAuth de Discord]",
            
            # Programas especiales
            "https://discord.com/hypesquad": "[🏠 Hypesquad de Discord]",
            "https://discord.com/student-hub": "[🎓 Student Hub de Discord]",
            
            # Actividad
            "https://discord.com/activity": "[🎯 Actividad de Discord]",
            "https://discord.com/activity/gaming": "[🎯 Actividad de Discord - Servidor: gaming]",
            
            # Media y CDN
            "https://media.discordapp.net/attachments/123/456/image.png": "[🖼️ Media de Discord - Servidor: attachments/123/456/image.png]",
            "https://cdn.discordapp.com/attachments/123/456/file.txt": "[🖼️ Media de Discord - Servidor: attachments/123/456/file.txt]",
            "https://cdn.discordapp.com/emojis/1234567890.png": "[🖼️ Media de Discord - Servidor: emojis/1234567890.png]",
            "https://cdn.discordapp.com/icons/1234567890/abc123.png": "[🖼️ Media de Discord - Servidor: icons/1234567890/abc123.png]",
        }
        
        return expected_map.get(url)
    
    def run_all_tests(self):
        """Ejecuta todos los tests de Discord con verificaciones específicas"""
        print("🧪 Ejecutando tests específicos de Discord...")
        
        test_cases = [
            # Invitaciones
            ("https://discord.gg/abc123", "Invitación corta"),
            ("https://discord.com/invite/xyz789", "Invitación completa"),
            
            # Canales y servidores
            ("https://discord.com/channels/1234567890/1234567891", "Canal específico"),
            ("https://discord.com/channels/1234567890", "Servidor específico"),
            
            # Tienda
            ("https://discord.com/store", "Tienda principal"),
            ("https://discord.com/store/skus/123", "SKUs de tienda"),
            ("https://discord.com/store/published-listings", "Listados de tienda"),
            
            # Nitro y servicios
            ("https://discord.com/nitro", "Discord Nitro"),
            ("https://discord.com/servers", "Servidores recomendados"),
            
            # Aplicaciones
            ("https://discord.com/application-directory", "Directorio de aplicaciones"),
            ("https://discord.com/application-directory/1234567890", "Aplicación específica"),
            
            # Biblioteca y descargas
            ("https://discord.com/library", "Biblioteca"),
            ("https://discord.com/download", "Descargas"),
            
            # Blog y soporte
            ("https://discord.com/blog", "Blog"),
            ("https://discord.com/blog/post-slug", "Post específico del blog"),
            ("https://discord.com/support", "Soporte"),
            ("https://discord.com/support/category", "Categoría de soporte"),
            
            # Legal
            ("https://discord.com/terms", "Términos de servicio"),
            ("https://discord.com/privacy", "Política de privacidad"),
            ("https://discord.com/guidelines", "Guías de la comunidad"),
            
            # Status y sistemas
            ("https://discord.com/status", "Estado del servicio"),
            
            # Modales y OAuth
            ("https://discord.com/modal/some-type", "Modal"),
            ("https://discord.com/oauth2/authorize", "Autorización OAuth"),
            
            # Programas especiales
            ("https://discord.com/hypesquad", "Hypesquad"),
            ("https://discord.com/student-hub", "Student Hub"),
            
            # Actividad
            ("https://discord.com/activity", "Actividad"),
            ("https://discord.com/activity/gaming", "Actividad de gaming"),
            
            # Media y CDN
            ("https://media.discordapp.net/attachments/123/456/image.png", "Media de Discord"),
            ("https://cdn.discordapp.com/attachments/123/456/file.txt", "CDN de Discord"),
            ("https://cdn.discordapp.com/emojis/1234567890.png", "Emoji de Discord"),
            ("https://cdn.discordapp.com/icons/1234567890/abc123.png", "Icono de servidor"),
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
                    success = "Discord" in result and "[" in result and "]" in result
                    match_info = "Verificación genérica"
                
                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected if expected else "N/A",
                    'Coincide': match_info,
                    'Éxito': "SÍ" if success else "NO"
                }
                
                self.add_test_result(f"Discord - {description}", success, details)
                self.print_test_result(f"Discord - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"Discord - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"Discord - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

if __name__ == "__main__":
    tester = DiscordTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()