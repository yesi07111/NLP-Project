# extractors/whatsapp.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class WhatsAppExtractor(BaseExtractor):
    DOMAINS = ['whatsapp.com', 'wa.me', 'www.whatsapp.com', 'web.whatsapp.com', 'business.whatsapp.com']
    SITE_NAME = 'WhatsApp'

    # Patrones regex para WhatsApp - ORDENADOS de más específico a más general
    PATTERNS = [
        # Canales oficiales específicos
        ("channel_info", r'^/channel/([^/]+)/info/?$'),
        ("channel", r'^/channel/([^/]+)/?$'),
        
        # Invitaciones con parámetros
        ("invite_with_context", r'^/invite/([^/]+)/?$'),
        ("invite", r'^/invite/([^/]+)/?$'),
        
        # Business específico
        ("business_catalog", r'^/business/catalog/?$'),
        ("business_profile", r'^/business/profile/?$'),
        ("business_api", r'^/business/api/?$'),
        ("business", r'^/business/?$'),
        
        # Contactos con parámetros
        ("contact_with_name", r'^/contact/([^/]+)/?$'),
        ("contact", r'^/contact/([^/]+)/?$'),
        
        # API específica
        ("api_version", r'^/api/v(\d+)/[^/]+/?$'),
        ("api_endpoint", r'^/api/([^/]+)/?$'),
        ("api", r'^/api/?$'),
        
        # Blog con estructura
        ("blog_dated", r'^/blog/(\d+)/([^/]+)/?$'),
        ("blog_post", r'^/blog/([^/]+)/?$'),
        ("blog", r'^/blog/?$'),
        
        # Soporte específico
        ("support_contact", r'^/support/contact-us/?$'),
        ("support_section", r'^/support/([^/]+)/?$'),
        ("support", r'^/support/?$'),
        
        # Descargas específicas
        ("download_ios", r'^/download/ios/?$'),
        ("download_android", r'^/download/android/?$'),
        ("download_mac", r'^/download/mac/?$'),
        ("download_windows", r'^/download/windows/?$'),
        ("download_os", r'^/download/([^/]+)/?$'),
        ("download", r'^/download/?$'),
        
        # Web (página de información sobre WhatsApp Web)
        ("web", r'^/web/?$'),
        
        # Estados y visualizaciones
        ("status_view", r'^/status/([^/]+)/view/?$'),
        ("status", r'^/status/([^/]+)/?$'),
        
        # Broadcast acciones
        ("broadcast_send", r'^/broadcast/([^/]+)/send/?$'),
        ("broadcast", r'^/broadcast/([^/]+)/?$'),
        
        # QR acciones
        ("qr_download", r'^/qr/([^/]+)/download/?$'),
        ("qr", r'^/qr/([^/]+)/?$'),
        
        # Características y políticas
        ("features", r'^/features/?$'),
        ("security", r'^/security/?$'),
        ("privacy", r'^/privacy/?$'),
        ("terms", r'^/terms/?$'),
        
        # Página principal
        ("home", r'^/?$'),
    ]
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, channel_id = self._extract_whatsapp_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['whatsapp'].get(content_type, '💬'),
            'channel_id': channel_id,
            'content_type': content_type
        }
    
    def _extract_whatsapp_info(self, parsed_url) -> Tuple[str, str]:
        """Extrae metadata completa de WhatsApp usando regex"""
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        clean_path = path.rstrip('/')
        content_type = "home"
        channel_id = ""
        
        # URLs de wa.me (chat directo) - manejo especial
        if "wa.me" in parsed_url.netloc:
            if clean_path:
                content_type = "chat"
                channel_id = clean_path.lstrip('/')
            else:
                content_type = "chat"
            
            # Si hay parámetro text, es chat con texto
            if "text" in query_params:
                content_type = "chat_with_text"
            return content_type, channel_id
        
        # WhatsApp Business (subdominio business)
        if "business.whatsapp.com" in parsed_url.netloc:
            if clean_path and clean_path != "/":
                if "product" in clean_path:
                    content_type = "business_product"
                else:
                    content_type = "business_home"
            else:
                content_type = "business_home"
            return content_type, channel_id
        
        # Web app (subdominio web) - ESTO ES LO IMPORTANTE
        if "web.whatsapp.com" in parsed_url.netloc:
            content_type = "web_app"
            return content_type, channel_id
        
        # Para el resto de URLs de whatsapp.com
        for pattern_type, pattern in self.PATTERNS:
            match = re.match(pattern, clean_path)
            if not match:
                continue
                
            groups = match.groups()
            
            if pattern_type in ["channel_info", "channel", "invite_with_context", "invite", 
                               "contact_with_name", "contact", "api_version", "api_endpoint",
                               "blog_dated", "blog_post", "support_section", "download_os",
                               "status_view", "status", "broadcast_send", "broadcast",
                               "qr_download", "qr"]:
                channel_id = groups[0] if groups else ""
                content_type = pattern_type
            else:
                content_type = pattern_type
            break
        
        return content_type, channel_id
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para WhatsApp"""
        emoji = data.get('emoji', '💬')
        channel_id = data.get('channel_id', '')
        content_type = data.get('content_type', '')
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "channel": "Canal", "channel_info": "Info del canal", 
            "invite": "Invitación", "invite_with_context": "Invitación",
            "chat": "Chat", "chat_with_text": "Chat con texto", 
            "business": "WhatsApp Business", "business_profile": "Perfil Business", 
            "business_catalog": "Catálogo Business", "business_api": "API Business",
            "business_home": "Business principal", "business_product": "Business producto",
            "contact": "Contacto", "contact_with_name": "Contacto",
            "api": "API", "api_endpoint": "Endpoint API", "api_version": "API versión específica",
            "blog": "Blog", "blog_post": "Post del blog", "blog_dated": "Blog con fecha",
            "support": "Soporte", "support_section": "Sección ayuda", "support_contact": "Soporte contactar",
            "download": "Descargar", "download_os": "Descargar", "download_windows": "Descargar Windows",
            "download_mac": "Descargar Mac", "download_android": "Descargar Android", "download_ios": "Descargar iOS",
            "web": "Web", "web_app": "Web app",  
            "status": "Estado", "status_view": "Ver estado",
            "broadcast": "Broadcast", "broadcast_send": "Enviar broadcast",
            "qr": "Código QR", "qr_download": "Descargar QR",
            "home": "Inicio", "features": "Características", "security": "Seguridad",
            "privacy": "Privacidad", "terms": "Términos"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        # Construir partes del display
        parts = []
        
        if channel_id and content_type not in ["home", "chat", "chat_with_text", "business_home", 
                                             "web_app", "web", "features", "security", "privacy", "terms"]:
            parts.append(f"ID: {channel_id}")

        parts_display = " - " + ", ".join(parts) if parts else ""
        
        return f"[{emoji} {type_display} de {self.SITE_NAME}{parts_display}]"