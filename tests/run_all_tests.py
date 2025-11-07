#!/usr/bin/env python3
"""
Script para ejecutar los tests.
Puede usarse desde la linea de comandos.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pattern_analyzer_tester import PatternAnalyzerTester

def main():
    """
    Funcion principal que ejecuta los tests.
    """

    # ------------------------------
    # Configuración de los grupos disponibles
    # ------------------------------
    available_groups = {
        "regex": "regex",     # Grupo de pruebas de expresiones regulares
        "link-r": "link-r",   # Grupo de pruebas de reemplazo de enlaces
        # Aquí se pueden agregar más grupos fácilmente, ej:
        # "parser": "parser",
        # "extractor": "extractor",
    }

    # ------------------------------
    # Parseo de argumentos
    # ------------------------------
    args = sys.argv[1:]
    verbose = "-v" in args or "--verbose" in args

    # Determinar inclusiones y exclusiones
    include_groups = set()
    exclude_groups = set()

    for arg in args:
        if arg.startswith("--no-"):
            group = arg[5:]
            if group in available_groups:
                exclude_groups.add(group)
        elif arg.startswith("--"):
            group = arg[2:]
            if group in available_groups:
                include_groups.add(group)

    # ------------------------------
    # Determinar qué grupos ejecutar
    # ------------------------------
    if include_groups:
        groups_to_run = include_groups
    elif exclude_groups:
        groups_to_run = set(available_groups.keys()) - exclude_groups
    else:
        groups_to_run = set(available_groups.keys())  # Ningún flag → correr todos

    print("Iniciando tests de patrones de texto...")
    if verbose:
        print("Modo verbose activado - mostrando detalles")
    print(f"Grupos disponibles: {', '.join(available_groups.keys())}")
    print(f"Grupos a ejecutar: {', '.join(groups_to_run)}\n")

    # ------------------------------
    # Ejecución de tests por grupo
    # ------------------------------
    for group in groups_to_run:
        print(f"🔹 Ejecutando grupo de tests: {group}")
        if group == "regex":
            tester = PatternAnalyzerTester(verbose=verbose)
            tester.run_all_tests()
            tester.print_summary()
        elif group == "link-r":
            from link_replacement_tests.plataform_tester import PlatformTester
            tester = PlatformTester(verbose=verbose)
            tester.run_all_tests()
            tester.print_summary()
        else:
            print(f"⚠️ Grupo '{group}' aún no implementado.\n")

if __name__ == "__main__":
    main()
