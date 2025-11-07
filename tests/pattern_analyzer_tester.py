import json
from typing import List, Dict
from base_tester import Tester

class PatternAnalyzerTester(Tester):
    """
    Tester especializado para las funciones de pattern_analyzer.py y regex_extractor.py
    """
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.test_messages = self._create_test_messages()
    
    def _create_test_messages(self) -> List[Dict]:
        """
        Crea mensajes de prueba con diferentes patrones para testing
        """
        return [
            # Mensaje con patrones financieros
            {
                "id": 1,
                "text": "Vendo laptop en 300-350 mlc, precio original 400 usd. Contacto: ejemplo@correo.com",
                "date": "2023-10-01T10:00:00Z",
                "chat_name": "test_chat"
            },
            # Mensaje con patrones temporales
            {
                "id": 2,
                "text": "Quedamos el 15/10/2023 a las 14:00. Recuerda: hoy reunión importante. #trabajo",
                "date": "2023-10-01T11:00:00Z", 
                "chat_name": "test_chat"
            },
            # Mensaje con patrones de contacto
            {
                "id": 3,
                "text": "Mi teléfono es +34 666 123 456 y email: contacto@empresa.com. Coordenadas: 40.7128,-74.0060",
                "date": "2023-10-01T12:00:00Z",
                "chat_name": "test_chat"
            },
            # Mensaje con patrones técnicos
            {
                "id": 4,
                "text": "IP: 192.168.1.1, peso: 2.5 kg, medida: 15x20 cm. URL: https://ejemplo.com",
                "date": "2023-10-01T13:00:00Z",
                "chat_name": "test_chat"
            },
            # Mensaje con patrones sociales
            {
                "id": 5,
                "text": "¡Hola @amigo! Mira esto #importante 😊. Visita https://sitio.com para más info",
                "date": "2023-10-01T14:00:00Z",
                "chat_name": "test_chat"
            },
            # Mensaje con múltiples patrones
            {
                "id": 6,
                "text": "Oferta: 150 mn hasta mañana. Tel: 53456576. Hoy 25% descuento! 📱",
                "date": "2023-10-01T15:00:00Z",
                "chat_name": "test_chat"
            }
        ]
    
    def run_all_tests(self):
        """
        Ejecuta todos los tests del pattern analyzer y regex extractor
        """
        print("🧪 INICIANDO TESTS DE PATTERN ANALYZER Y REGEX EXTRACTOR")
        print("=" * 60)
        
        # Tests de funciones extract_* del pattern_analyzer
        self._test_extract_financial_patterns()
        self._test_extract_temporal_patterns()
        self._test_extract_social_patterns()
        self._test_extract_contact_patterns()
        self._test_extract_technical_patterns()
        self._test_calculate_conversation_metrics()
        self._test_create_patterns_summary()
        
        # Tests de regex_extractor
        self._test_regex_monetary_patterns()
        self._test_regex_date_patterns()
        self._test_regex_basic_patterns()
        self._test_analyze_text_patterns()
        
        # Tests de funciones auxiliares
        self._test_load_chat_messages()
        self._test_save_patterns_summary()
    
    def _test_extract_financial_patterns(self):
        """Test para extract_financial_patterns"""
        from regex.pattern_analyzer import extract_financial_patterns
        
        try:
            result = extract_financial_patterns(self.test_messages)
            
            # Verificar estructura
            required_keys = ["explicit_currencies", "implicit_prices", "currency_breakdown", "total_monetary_references"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            has_financial_data = len(result["explicit_currencies"]) > 0
            breakdown_ok = isinstance(result["currency_breakdown"], dict)
            
            success = structure_ok and has_financial_data and breakdown_ok
            details = {
                "explicit_currencies_found": len(result["explicit_currencies"]),
                "implicit_prices_found": len(result["implicit_prices"]),
                "total_references": result["total_monetary_references"],
                "currency_breakdown": result["currency_breakdown"]
            }
            
            self.add_test_result("extract_financial_patterns", success, details)
            self.print_test_result("extract_financial_patterns", success, details)
            
        except Exception as e:
            self.add_test_result("extract_financial_patterns", False, f"Error: {str(e)}")
            self.print_test_result("extract_financial_patterns", False, f"Error: {str(e)}")
    
    def _test_extract_temporal_patterns(self):
        """Test para extract_temporal_patterns"""
        from regex.pattern_analyzer import extract_temporal_patterns
        
        try:
            result = extract_temporal_patterns(self.test_messages)
            
            # Verificar estructura
            required_keys = ["absolute_dates", "relative_references", "time_expressions", "total_temporal_references"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            has_temporal_data = result["total_temporal_references"] > 0
            types_ok = (isinstance(result["absolute_dates"], list) and 
                       isinstance(result["relative_references"], list))
            
            success = structure_ok and has_temporal_data and types_ok
            details = {
                "absolute_dates": len(result["absolute_dates"]),
                "relative_references": len(result["relative_references"]),
                "total_temporal_references": result["total_temporal_references"]
            }
            
            self.add_test_result("extract_temporal_patterns", success, details)
            self.print_test_result("extract_temporal_patterns", success, details)
            
        except Exception as e:
            self.add_test_result("extract_temporal_patterns", False, f"Error: {str(e)}")
            self.print_test_result("extract_temporal_patterns", False, f"Error: {str(e)}")
    
    def _test_extract_social_patterns(self):
        """Test para extract_social_patterns"""
        from regex.pattern_analyzer import extract_social_patterns
        
        try:
            result = extract_social_patterns(self.test_messages)
            
            # Verificar estructura
            required_keys = ["hashtags", "mentions", "urls", "emojis", "social_engagement_score"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            has_social_data = (
                len(result["hashtags"]) > 0 or 
                len(result["mentions"]) > 0 or 
                len(result["urls"]) > 0
            )
            score_ok = isinstance(result["social_engagement_score"], int)
            
            success = structure_ok and has_social_data and score_ok
            details = {
                "hashtags": result["hashtags"],
                "mentions": result["mentions"],
                "urls": result["urls"],
                "emojis": result["emojis"],
                "engagement_score": result["social_engagement_score"]
            }
            
            self.add_test_result("extract_social_patterns", success, details)
            self.print_test_result("extract_social_patterns", success, details)
            
        except Exception as e:
            self.add_test_result("extract_social_patterns", False, f"Error: {str(e)}")
            self.print_test_result("extract_social_patterns", False, f"Error: {str(e)}")
    
    def _test_extract_contact_patterns(self):
        """Test para extract_contact_patterns"""
        from regex.pattern_analyzer import extract_contact_patterns
        
        try:
            result = extract_contact_patterns(self.test_messages)
            
            # Verificar estructura
            required_keys = ["emails", "phone_numbers", "contact_entities", "total_contact_points"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            has_contact_data = (
                len(result["emails"]) > 0 or 
                len(result["phone_numbers"]) > 0
            )
            entities_ok = isinstance(result["contact_entities"], list)
            
            success = structure_ok and has_contact_data and entities_ok
            details = {
                "emails": result["emails"],
                "phone_numbers": result["phone_numbers"],
                "total_contact_points": result["total_contact_points"]
            }
            
            self.add_test_result("extract_contact_patterns", success, details)
            self.print_test_result("extract_contact_patterns", success, details)
            
        except Exception as e:
            self.add_test_result("extract_contact_patterns", False, f"Error: {str(e)}")
            self.print_test_result("extract_contact_patterns", False, f"Error: {str(e)}")
    
    def _test_extract_technical_patterns(self):
        """Test para extract_technical_patterns"""
        from regex.pattern_analyzer import extract_technical_patterns
        
        try:
            result = extract_technical_patterns(self.test_messages)
            
            # Verificar estructura
            required_keys = ["coordinates", "ip_addresses", "measurements", "technical_entities", "total_technical_patterns"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            has_technical_data = (
                len(result["coordinates"]) > 0 or 
                len(result["ip_addresses"]) > 0 or
                len(result["measurements"]) > 0
            )
            total_ok = result["total_technical_patterns"] >= 0
            
            success = structure_ok and has_technical_data and total_ok
            details = {
                "coordinates": result["coordinates"],
                "ip_addresses": result["ip_addresses"],
                "measurements": result["measurements"],
                "total_technical_patterns": result["total_technical_patterns"]
            }
            
            self.add_test_result("extract_technical_patterns", success, details)
            self.print_test_result("extract_technical_patterns", success, details)
            
        except Exception as e:
            self.add_test_result("extract_technical_patterns", False, f"Error: {str(e)}")
            self.print_test_result("extract_technical_patterns", False, f"Error: {str(e)}")
    
    def _test_calculate_conversation_metrics(self):
        """Test para calculate_conversation_metrics"""
        from regex.pattern_analyzer import calculate_conversation_metrics
        
        try:
            result = calculate_conversation_metrics(self.test_messages)
            
            # Verificar estructura
            required_keys = ["total_messages_with_patterns", "patterns_per_message_avg", "most_active_categories", "temporal_distribution"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar datos
            metrics_ok = (
                isinstance(result["total_messages_with_patterns"], int) and
                isinstance(result["patterns_per_message_avg"], (int, float)) and
                isinstance(result["most_active_categories"], list)
            )
            
            success = structure_ok and metrics_ok
            details = {
                "messages_with_patterns": result["total_messages_with_patterns"],
                "patterns_per_message": result["patterns_per_message_avg"],
                "most_active_categories": result["most_active_categories"][:2] if result["most_active_categories"] else []
            }
            
            self.add_test_result("calculate_conversation_metrics", success, details)
            self.print_test_result("calculate_conversation_metrics", success, details)
            
        except Exception as e:
            self.add_test_result("calculate_conversation_metrics", False, f"Error: {str(e)}")
            self.print_test_result("calculate_conversation_metrics", False, f"Error: {str(e)}")
    
    def _test_create_patterns_summary(self):
        """Test para create_patterns_summary"""
        from regex.pattern_analyzer import create_patterns_summary
        
        try:
            result = create_patterns_summary(self.test_messages)
            
            # Verificar estructura principal
            required_keys = ["metadata", "extracted_patterns", "message_analysis", "conversation_metrics"]
            structure_ok = all(key in result for key in required_keys)
            
            # Verificar sub-estructuras
            metadata_ok = "total_messages" in result["metadata"]
            patterns_ok = all(key in result["extracted_patterns"] for key in 
                            ["financial", "temporal", "social", "contact", "technical"])
            analysis_ok = len(result["message_analysis"]) == len(self.test_messages)
            
            success = structure_ok and metadata_ok and patterns_ok and analysis_ok
            details = {
                "total_messages": result["metadata"]["total_messages"],
                "message_analysis_count": len(result["message_analysis"]),
                "patterns_categories": list(result["extracted_patterns"].keys())
            }
            
            self.add_test_result("create_patterns_summary", success, details)
            self.print_test_result("create_patterns_summary", success, details)
            
        except Exception as e:
            self.add_test_result("create_patterns_summary", False, f"Error: {str(e)}")
            self.print_test_result("create_patterns_summary", False, f"Error: {str(e)}")
    
    def _test_regex_monetary_patterns(self):
        """Test para patrones monetarios en regex_extractor"""
        from regex.regex_extractor import _extract_monetary_patterns
        
        test_cases = [
            {
                "text": "Precio: 150-200 mlc, también 300 usd y 50 en clasica",
                "expected": ["mlc", "usd", "clasica"]
            },
            {
                "text": "De 100 a 150 mn, entre 200 y 250 mlc",
                "expected": ["mn", "mlc"]
            },
            {
                "text": "Cuesta 75.50 usd, rebajado a 60",
                "expected": ["usd"]
            }
        ]
        
        all_passed = True
        details = {}
        
        for i, test_case in enumerate(test_cases):
            try:
                result = _extract_monetary_patterns(test_case["text"])
                
                # Verificar que se detecten las monedas esperadas
                detected_currencies = []
                for match in result.get('monedas_explicitas', []):
                    if len(match) >= 2:
                        detected_currencies.append(match[1].lower())
                
                passed = all(currency in str(detected_currencies) for currency in test_case["expected"])
                all_passed = all_passed and passed
                
                details[f"test_case_{i+1}"] = {
                    "text": test_case["text"],
                    "expected": test_case["expected"],
                    "detected": detected_currencies,
                    "passed": passed
                }
                
            except Exception as e:
                all_passed = False
                details[f"test_case_{i+1}"] = f"Error: {str(e)}"
        
        self.add_test_result("regex_monetary_patterns", all_passed, details)
        self.print_test_result("regex_monetary_patterns", all_passed, details)
    
    def _test_regex_date_patterns(self):
        """Test para patrones de fecha en regex_extractor"""
        from regex.regex_extractor import _extract_date_patterns
        
        test_cases = [
            {
                "text": "Quedamos hoy a las 15:00, mañana reunión",
                "expected_categories": ["dates_relative_simple"]
            },
            {
                "text": "El 15/10/2023 y 20 de enero de 2024",
                "expected_categories": ["dates_absolute", "dates_spanish_format"]
            },
            {
                "text": "En 5 días, hace 2 semanas",
                "expected_categories": ["dates_relative_quantified"]
            }
        ]
        
        all_passed = True
        details = {}
        
        for i, test_case in enumerate(test_cases):
            try:
                result = _extract_date_patterns(test_case["text"])
                
                # Verificar que las categorías esperadas tengan datos
                passed = all(
                    len(result.get(category, [])) > 0 
                    for category in test_case["expected_categories"]
                )
                all_passed = all_passed and passed
                
                detected_categories = {
                    category: len(result.get(category, [])) 
                    for category in test_case["expected_categories"]
                }
                
                details[f"test_case_{i+1}"] = {
                    "text": test_case["text"],
                    "expected_categories": test_case["expected_categories"],
                    "detected_counts": detected_categories,
                    "passed": passed
                }
                
            except Exception as e:
                all_passed = False
                details[f"test_case_{i+1}"] = f"Error: {str(e)}"
        
        self.add_test_result("regex_date_patterns", all_passed, details)
        self.print_test_result("regex_date_patterns", all_passed, details)
    
    def _test_regex_basic_patterns(self):
        """Test para patrones básicos en regex_extractor"""
        from regex.regex_extractor import extract_regex_patterns
        
        test_cases = [
            {
                "text": "Email: test@example.com, tel: +34 666 123 456, URL: https://site.com",
                "expected": ["emails", "phone_numbers", "urls_raw"]
            },
            {
                "text": "Coordenadas: 40.7128,-74.0060, IP: 192.168.1.1",
                "expected": ["coordinates", "ip_addresses"]
            },
            {
                "text": "Hashtag: #test, @mencion y 😊",
                "expected": ["hashtags", "mentions", "emojis"]
            }
        ]
        
        all_passed = True
        details = {}
        
        for i, test_case in enumerate(test_cases):
            try:
                result = extract_regex_patterns(test_case["text"])
                
                # Verificar que los patrones esperados tengan datos
                passed = all(
                    len(result.get(pattern_type, [])) > 0 
                    for pattern_type in test_case["expected"]
                )
                all_passed = all_passed and passed
                
                detected_patterns = {
                    pattern_type: len(result.get(pattern_type, [])) 
                    for pattern_type in test_case["expected"]
                }
                
                details[f"test_case_{i+1}"] = {
                    "text": test_case["text"],
                    "expected_patterns": test_case["expected"],
                    "detected_counts": detected_patterns,
                    "passed": passed
                }
                
            except Exception as e:
                all_passed = False
                details[f"test_case_{i+1}"] = f"Error: {str(e)}"
        
        self.add_test_result("regex_basic_patterns", all_passed, details)
        self.print_test_result("regex_basic_patterns", all_passed, details)
    
    def _test_analyze_text_patterns(self):
        """Test para analyze_text_patterns"""
        from regex.regex_extractor import analyze_text_patterns
        
        test_cases = [
            {
                "text": "Precio: 150 mlc, contacto: test@email.com",
                "should_contain": ["referencias monetarias", "emails"]
            },
            {
                "text": "Hoy reunión a las 15:00 #importante",
                "should_contain": ["referencias de fecha", "hashtags"]
            },
            {
                "text": "Texto sin patrones especiales",
                "should_not_contain": ["Patrones:"]
            }
        ]
        
        all_passed = True
        details = {}
        
        for i, test_case in enumerate(test_cases):
            try:
                result = analyze_text_patterns(test_case["text"])
                
                # Verificar contenido esperado
                if "should_contain" in test_case:
                    passed = all(
                        pattern in result 
                        for pattern in test_case["should_contain"]
                    )
                elif "should_not_contain" in test_case:
                    passed = all(
                        pattern not in result 
                        for pattern in test_case["should_not_contain"]
                    )
                else:
                    passed = True
                
                all_passed = all_passed and passed
                
                details[f"test_case_{i+1}"] = {
                    "input": test_case["text"],
                    "output": result,
                    "passed": passed
                }
                
            except Exception as e:
                all_passed = False
                details[f"test_case_{i+1}"] = f"Error: {str(e)}"
        
        self.add_test_result("analyze_text_patterns", all_passed, details)
        self.print_test_result("analyze_text_patterns", all_passed, details)
    
    def _test_load_chat_messages(self):
        """Test para load_chat_messages"""
        from regex.pattern_analyzer import load_chat_messages
        import tempfile
        import os
        
        try:
            # Crear archivo temporal de prueba
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = {
                    "messages": [
                        {"id": 1, "text": "Mensaje de prueba", "date": "2023-01-01T00:00:00Z"}
                    ]
                }
                json.dump(test_data, f)
                temp_file = f.name
            
            # Probar carga
            result = load_chat_messages(temp_file)
            
            # Verificar resultado
            passed = (
                isinstance(result, list) and 
                len(result) == 1 and 
                result[0]["text"] == "Mensaje de prueba"
            )
            
            # Limpiar
            os.unlink(temp_file)
            
            details = {
                "file_loaded": temp_file,
                "messages_loaded": len(result),
                "content_ok": result[0]["text"] if result else "No content"
            }
            
            self.add_test_result("load_chat_messages", passed, details)
            self.print_test_result("load_chat_messages", passed, details)
            
        except Exception as e:
            self.add_test_result("load_chat_messages", False, f"Error: {str(e)}")
            self.print_test_result("load_chat_messages", False, f"Error: {str(e)}")
    
    def _test_save_patterns_summary(self):
        """Test para save_patterns_summary"""
        from regex.pattern_analyzer import save_patterns_summary
        import tempfile
        import os
        
        try:
            # Crear archivo temporal de prueba
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = {
                    "messages": [
                        {"id": 1, "text": "Test 150 mlc", "date": "2023-01-01T00:00:00Z", "chat_name": "test"}
                    ]
                }
                json.dump(test_data, f)
                temp_file = f.name
            
            # Cargar mensajes
            messages = [
                {"id": 1, "text": "Test 150 mlc", "date": "2023-01-01T00:00:00Z", "chat_name": "test"}
            ]
            
            # Probar guardado
            result = save_patterns_summary(temp_file, messages)
            
            # Verificar que se creó el archivo de patrones
            patterns_file = temp_file.replace('.json', '_patterns.json')
            # patterns_file = patterns_file.replace(os.path.basename(patterns_file), 
            #                                     os.path.join('patterns', os.path.basename(patterns_file)))
            
            file_exists = os.path.exists(patterns_file)
            
            # Limpiar
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            if os.path.exists(patterns_file):
                os.unlink(patterns_file)
            if os.path.exists('patterns') and not os.listdir('patterns'):
                os.rmdir('patterns')
            
            details = {
                "input_file": temp_file,
                "patterns_file_created": patterns_file if file_exists else "Not created",
                "result_type": type(result).__name__
            }
            
            self.add_test_result("save_patterns_summary", file_exists, details)
            self.print_test_result("save_patterns_summary", file_exists, details)
            
        except Exception as e:
            self.add_test_result("save_patterns_summary", False, f"Error: {str(e)}")
            self.print_test_result("save_patterns_summary", False, f"Error: {str(e)}")


# Ejemplo de uso
if __name__ == "__main__":
    # Ejecutar tests en modo verbose
    tester = PatternAnalyzerTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()