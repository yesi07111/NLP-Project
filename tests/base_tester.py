from link_processor.main import LinkProcessor

class Tester:
    """
    Clase base para realizar tests. Maneja resultados de forma generica y proporciona resumenes.
    """
    
    def __init__(self, verbose=False):
        """
        Inicializa el tester.
        
        Args:
            verbose: Si es True, muestra detalles de cada test. Por defecto False.
        """
        self.verbose = verbose
        self.tests_results = []  # Lista de tuplas (nombre_test, exito, detalles)
    
    def add_test_result(self, test_name, success, details=None):
        """
        Agrega un resultado de test a la lista.
        
        Args:
            test_name: Nombre identificador del test
            success: Booleano que indica si el test paso correctamente
            details: Informacion adicional sobre el test (opcional)
        """
        self.tests_results.append({
            'name': test_name,
            'success': success,
            'details': details
        })
    
    def print_test_result(self, test_name, success, details=None):
        """
        Imprime el resultado de un test individual.
        
        Args:
            test_name: Nombre del test
            success: Si el test fue exitoso
            details: Detalles adicionales para mostrar en modo verbose
        """
        emoji = "✅" if success else "❌"
        print(f"{emoji} {test_name}")
        
        if self.verbose and details:
            # Si estamos en modo verbose, mostramos los detalles
            if isinstance(details, str):
                print(f"   📝 {details}")
            elif isinstance(details, dict):
                for key, value in details.items():
                    print(f"   📝 {key}: {value}")
            print()  # Linea en blanco para separar
    
    def run_all_tests(self):
        """
        Metodo abstracto que debe ser implementado por las clases hijas.
        Aqui se ejecutaran todos los tests especificos.
        """
        raise NotImplementedError("Las subclases deben implementar este metodo")
    
    def print_summary(self):
        """
        Imprime un resumen final de todos los tests ejecutados.
        """
        total_tests = len(self.tests_results)
        passed_tests = sum(1 for test in self.tests_results if test['success'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*50)
        print("RESUMEN FINAL DE TESTS")
        print("="*50)
        
        # Mostrar todos los resultados individuales si verbose
        if self.verbose:
            print("Resultados resumidos de los tests:")
            for test in self.tests_results:
                emoji = "✅" if test['success'] else "❌"
                print(f"{emoji} {test['name']}")
        
        print("-" * 50)
        print(f"Total: {total_tests} tests")
        print(f"✅ Exitosos: {passed_tests}")
        print(f"❌ Fallidos: {failed_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"📊 Tasa de exito: {success_rate:.1f}%")
        
        # Indicar el estado general
        if failed_tests == 0:
            print("🎉 ¡Todos los tests pasaron correctamente!")
        else:
            print(f"💡 {failed_tests} test(s) necesitan atención")
        
        print("="*50)