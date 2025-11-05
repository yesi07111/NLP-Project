import os
import sys

# Agregar el directorio padre al path para importar los modulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from regex.regex_extractor import extract_regex_patterns, analyze_text_patterns
from base_tester import Tester

class RegexTester(Tester):
    """
    Tester especifico para probar los patrones de extraccion de texto.
    Hereda de la clase base Tester.
    """
    
    def __init__(self, verbose=False):
        """
        Inicializa el tester de patrones.
        
        Args:
            verbose: Si es True, muestra detalles de cada test
        """
        super().__init__(verbose)
    
    def run_all_tests(self):
        """
        Ejecuta todos los tests de patrones definidos.
        """
        if self.verbose:
            print("🧪 Iniciando pruebas de patrones de texto...")
            print()
        
        # Ejecutar cada categoria de tests
        self._run_monetary_tests()
        self._run_date_tests() 
        self._run_mixed_tests()
        self._run_url_replacement_tests()
    
    def _run_monetary_tests(self):
        """Ejecuta tests relacionados con patrones monetarios."""
        test_cases = [
            {
                "name": "Monedas basicas",
                "text": "Vendo por 20 mn y 30 mlc",
                "expected_min_patterns": 2
            },
            {
                "name": "Rangos monetarios complejos", 
                "text": "Precio: 150-200 mlc, también 140 - 340 mn y de 300 a 400 usd",
                "expected_min_patterns": 3
            },
            {
                "name": "Monedas con preposiciones",
                "text": "Cuesta 20 en clásica y 25 en mlc, 30 clasica sin en",
                "expected_min_patterns": 3
            },
            {
                "name": "Formatos decimales y multiples",
                "text": "Entre 100 y 150 mn, 200.50 mlc, 300,00 usd. Pago: 30 clasica, 35 USD, 40 dólares",
                "expected_min_patterns": 6
            },
            {
                "name": "Precios implicitos variados",
                "text": "sale en 700, cuesta 500, vale 300. subió a 400, bajó a 350. precio: 250, valor: 200",
                "expected_min_patterns": 7
            }
        ]
        
        for case in test_cases:
            self._run_single_pattern_test(case)
    
    def _run_date_tests(self):
        """Ejecuta tests relacionados con patrones de fecha."""
        test_cases = [
            {
                "name": "Fechas relativas basicas",
                "text": "hoy, ayer, antier, mañana, pasado mañana",
                "expected_min_patterns": 5
            },
            {
                "name": "Fechas con cantidades",
                "text": "en 5 dias, en 3 días, hace 2 semanas, en 1 mes, hace 2 años",
                "expected_min_patterns": 5  
            },
            {
                "name": "Referencias temporales complejas",
                "text": "semana que viene, semana pasada, esta semana, mes que viene, año pasado, este fin de semana",
                "expected_min_patterns": 6
            },
            {
                "name": "Dias y meses especificos",
                "text": "lunes, martes, miércoles, jueves, viernes, sábado, domingo, enero, febrero, marzo",
                "expected_min_patterns": 10
            },
            {
                "name": "Festivos y estaciones",
                "text": "navidad, año nuevo, reyes, semana santa, primavera, verano, otoño, invierno",
                "expected_min_patterns": 8
            }
        ]
        
        for case in test_cases:
            self._run_single_pattern_test(case)
    
    def _run_mixed_tests(self):
        """Ejecuta tests con mezcla de diferentes patrones."""
        test_cases = [
            {
                "name": "Venta con contacto completo",
                "text": "Vendo iPhone en 300 mlc, contacto: @ventas tel: +5351234567 email: ventas@tienda.com #oferta",
                "expected_min_patterns": 5
            },
            {
                "name": "Reunion con detalles",
                "text": "Reunión el próximo miércoles a las 10:00 AM. Lugar: oficina central. Email: reuniones@empresa.com URL: https://empresa.com/reunion",
                "expected_min_patterns": 4
            },
            {
                "name": "Anuncio complejo",
                "text": "¡Gran oferta! iPhone 13 por 500 mlc (antes 600). Solo hoy y mañana. Contacto: @techdeals +5355112233 #tecnologia #oferta",
                "expected_min_patterns": 8
            }
        ]
        
        for case in test_cases:
            self._run_single_pattern_test(case)
    
    def _run_url_replacement_tests(self):
        """Ejecuta tests especificos para el reemplazo de URLs."""
        test_cases = [
            {
                "name": "URLs de redes sociales",
                "text": "Mira este video: https://youtube.com/watch?v=abc123 y este reel: https://instagram.com/reel/XYZ789",
                "expected_min_patterns": 2,
                "check_url_replacement": True
            },
            {
                "name": "Enlaces multiples",
                "text": "Siguenos en https://facebook.com/pagina y https://twitter.com/usuario. Mas info: https://github.com/usuario/repo",
                "expected_min_patterns": 3,
                "check_url_replacement": True
            }
        ]
        
        for case in test_cases:
            self._run_single_pattern_test(case)
    
    def _run_single_pattern_test(self, test_case):
        """
        Ejecuta un test individual de patrones.
        
        Args:
            test_case: Diccionario con la definicion del test
        """
        text = test_case["text"]
        expected_min = test_case["expected_min_patterns"]
        check_urls = test_case.get("check_url_replacement", False)
        
        # Extraer patrones del texto
        patterns = extract_regex_patterns(text)
        enriched_text = analyze_text_patterns(text)
        
        # Contar patrones detectados
        total_patterns = self._count_total_patterns(patterns)
        
        # Verificar si el test pasa
        success = total_patterns >= expected_min
        
        # Preparar detalles para mostrar en modo verbose
        details = {}
        if self.verbose:
            details = {
                "Texto original": text,
                "Texto enriquecido": enriched_text,
                "Patrones detectados": total_patterns,
                "Esperados minimo": expected_min,
                "Desglose": self._get_patterns_breakdown(patterns)
            }
            
            if check_urls:
                details["Reemplazo URLs"] = "Verificado" if "[🔗" in enriched_text else "No verificado"
        
        # Agregar y mostrar resultado
        self.add_test_result(test_case["name"], success, details)
        self.print_test_result(test_case["name"], success, details)
    
    def _count_total_patterns(self, patterns):
        """
        Cuenta el total de patrones encontrados, excluyendo listas vacias.
        
        Args:
            patterns: Diccionario con todos los patrones
            
        Returns:
            Numero total de patrones detectados
        """
        count = 0
        for key, value in patterns.items():
            if isinstance(value, list):
                count += len(value)
            elif value:  # Para valores que no son lista pero tienen contenido
                count += 1
        return count
    
    def _get_patterns_breakdown(self, patterns):
        """
        Obtiene un desglose legible de los patrones encontrados.
        
        Args:
            patterns: Diccionario con los patrones
            
        Returns:
            String con el desglose formateado
        """
        breakdown = []
        for category, items in patterns.items():
            if items and (isinstance(items, list) and len(items) > 0):
                count = len(items) if isinstance(items, list) else 1
                breakdown.append(f"{category}: {count}")
        
        return ", ".join(breakdown) if breakdown else "No se detectaron patrones"