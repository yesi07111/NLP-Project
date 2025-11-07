# extractors/amazon.py
import re
from .base import BaseExtractor, register_extractor
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from ..utils.constants import EMOJI_MAPS

@register_extractor
class AmazonExtractor(BaseExtractor):
    DOMAINS = ['amazon.com', 'amazon.', 'business.amazon.com', 'www.amazon.com', 'amazon.com.mx']
    SITE_NAME = 'Amazon'
    
    # Patrones regex para diferentes tipos de URLs de Amazon
    PATTERNS = {
        'product': [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'^/([A-Z0-9]{10})$'  # ASIN directo
        ],
        'search': [
            r'/s$',
            r'/search'
        ],
        'deal': [
            r'/deal/([a-zA-Z0-9]+)'
        ],
        'today_deals': [
            r'/gp/goldbox',
            r'/deals',
            r'/today-deals'
        ],
        'lightning_deal': [
            r'/gp/lightning-deals',
            r'/lightning/deal'
        ],
        'store': [
            r'/store/([^/]+)'
        ],
        'wishlist': [
            r'/wishlist/([a-zA-Z0-9]+)'
        ],
        'cart': [
            r'/cart'
        ],
        'orders': [
            r'/your-orders'
        ],
        'recommendations': [
            r'/recommendations'
        ],
        'create_review': [
            r'/review/create-review'
        ],
        'product_reviews': [
            r'/product-reviews/([A-Z0-9]{10})'
        ],
        'fresh': [
            r'/alm/storefront'
        ],
        'prime': [
            r'/prime$',
            r'/prime/$'
        ],
        'prime_video': [
            r'/prime/video',
            r'/Prime-Video'
        ],
        'prime_music': [
            r'/prime/music'
        ],
        'music_unlimited': [
            r'/music/unlimited'
        ],
        'video': [
            r'/video$',
            r'/video/'
        ],
        'books': [
            r'/books$',
            r'/books/'
        ],
        'books_store': [
            r'/books/store'
        ],
        'appstore': [
            r'/mobile-apps'
        ],
        'kindle_store': [
            r'/kindle/store',
            r'/Kindle-Store'
        ],
        'kindle_unlimited': [
            r'/kindle-dbs'
        ],
        'echo': [
            r'/echo$',
            r'/echo/'
        ],
        'fashion': [
            r'/fashion'
        ],
        'electronics': [
            r'/electronics'
        ],
        'home': [
            r'/home'
        ],
        'garden': [
            r'/garden'
        ],
        'automotive': [
            r'/automotive'
        ],
        'business': [
            r'/b2b'
        ],
        'warehouse': [
            r'/warehouse-deals'
        ],
        'outlet': [
            r'/outlet'
        ],
        'subscribe': [
            r'/subscribe-and-save'
        ]
    }
    
    def extract(self, parsed_url, domain: str) -> Optional[Dict[str, Any]]:
        content_type, product_id, category, search_query = self._extract_amazon_info(parsed_url)
        
        return {
            'site_name': self.SITE_NAME,
            'emoji': EMOJI_MAPS['amazon'].get(content_type, '🛒'),
            'product_id': product_id,
            'category': category,
            'search_query': search_query,
            'content_type': content_type
        }
    
    def _extract_amazon_info(self, parsed_url) -> Tuple[str, str, str, str]:
        """Extrae metadata completa de Amazon usando expresiones regulares"""
        path = parsed_url.path
        netloc = parsed_url.netloc
        query_params = parse_qs(parsed_url.query)
        content_type = ""
        product_id = ""
        category = ""
        search_query = ""
        
        # Verificar Amazon Business en el netloc primero (caso especial)
        if 'business.amazon.com' in netloc:
            content_type = "business"
            return content_type, product_id, category, search_query
        
        # Verificar vendedores (usando query parameters) - DEBE IR ANTES de búsquedas
        if "me=" in parsed_url.query:
            content_type = "seller"
            product_id = query_params.get('me', [''])[0]
            return content_type, product_id, category, search_query
        
        if "seller=" in parsed_url.query:
            content_type = "seller"
            product_id = query_params.get('seller', [''])[0]
            return content_type, product_id, category, search_query
        
        # Verificar búsquedas (porque usan query parameters)
        if any(re.search(pattern, path) for pattern in self.PATTERNS['search']):
            content_type = "search"
            search_query = query_params.get('k', [''])[0] or query_params.get('field-keywords', [''])[0]
            return content_type, product_id, category, search_query
        
        # Verificar todos los patrones en orden de prioridad
        for content_type_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, path)
                if match:
                    content_type = content_type_name
                    
                    # Extraer IDs o categorías según el patrón
                    if content_type_name in ['product', 'deal', 'wishlist', 'product_reviews']:
                        product_id = match.group(1) if match.groups() else ""
                    elif content_type_name == 'store':
                        category = match.group(1) if match.groups() else ""
                    
                    # Casos especiales que requieren lógica adicional
                    if content_type_name == 'wishlist' and "lm" in query_params:
                        content_type = "public_wishlist"
                    
                    return content_type, product_id, category, search_query
        
        # Verificar Amazon Business en la ruta
        if "/b2b" in path:
            content_type = "business"
            return content_type, product_id, category, search_query
        
        # Si no coincide con ningún patrón, verificar ASIN directo
        parts = path.strip('/').split('/')
        if len(parts) == 1 and len(parts[0]) == 10 and parts[0].isalnum():
            content_type = "product"
            product_id = parts[0]
            return content_type, product_id, category, search_query
        
        return content_type, product_id, category, search_query
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Formato personalizado para Amazon basado en la lógica original"""
        emoji = data.get('emoji', '🛒')
        product_id = data.get('product_id', '')
        category = data.get('category', '')
        search_query = data.get('search_query', '')
        content_type = data.get('content_type', '')
        
        product_id_display = f" - ID: {product_id}" if product_id else ""
        category_display = f" - Categoría: {category}" if category else ""
        search_display = f" - Búsqueda: '{search_query}'" if search_query else ""
        
        # Mapeo de tipos a nombres en español
        type_names = {
            "product": "Producto", "search": "Búsqueda", "deal": "Oferta",
            "today_deals": "Ofertas del día", "lightning_deal": "Oferta relámpago",
            "store": "Tienda", "wishlist": "Lista de deseos", "public_wishlist": "Lista de deseos pública",
            "cart": "Carrito", "orders": "Pedidos", "recommendations": "Recomendaciones",
            "review": "Reseña", "create_review": "Crear reseña", "product_reviews": "Reseñas del producto",
            "seller": "Vendedor", "fresh": "Amazon Fresh", "prime": "Prime",
            "prime_video": "Prime Video", "prime_music": "Prime Music", "prime_gaming": "Prime Gaming",
            "prime_reading": "Prime Reading", "music": "Amazon Music", "music_unlimited": "Music Unlimited",
            "video": "Amazon Video", "books": "Libros", "books_store": "Tienda de libros",
            "appstore": "Appstore", "kindle": "Kindle", "kindle_store": "Tienda Kindle",
            "kindle_unlimited": "Kindle Unlimited", "echo": "Echo", "echo_show": "Echo Show",
            "echo_dot": "Echo Dot", "fashion": "Moda", "electronics": "Electrónicos",
            "home": "Hogar", "garden": "Jardín", "automotive": "Automotriz",
            "business": "Amazon Business", "warehouse": "Warehouse", "outlet": "Outlet",
            "subscribe": "Subscribe & Save"
        }
        
        type_display = type_names.get(content_type, "Contenido")
        
        return f"[{emoji} {type_display} de {self.SITE_NAME}{product_id_display}{category_display}{search_display}]"