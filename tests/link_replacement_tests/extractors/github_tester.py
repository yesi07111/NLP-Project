from tests.base_tester import Tester, LinkProcessor

class GitHubTester(Tester):
    """Tester específico para enlaces de GitHub con validaciones completas"""

    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()

    def run_all_tests(self):
        print("🧪 Ejecutando tests de GitHub...")

        test_cases = [
            ("https://github.com/octocat", "Perfil de usuario", "[👤 Perfil de GitHub de octocat]"),
            ("https://github.com/torvalds", "Perfil famoso", "[👤 Perfil de GitHub de torvalds]"),
            ("https://github.com/facebook/react", "Repositorio popular", "[💻 Repositorio de GitHub de facebook/react]"),
            ("https://github.com/vuejs/vue/", "Repositorio con barra final", "[💻 Repositorio de GitHub de vuejs/vue]"),
            ("https://github.com/facebook/react/blob/main/package.json", "Archivo en rama main", "[💻 Archivo de GitHub de facebook/react - Archivo: main/package.json]"),
            ("https://github.com/python/cpython/blob/main/Lib/os.py", "Archivo Python", "[💻 Archivo de GitHub de python/cpython - Archivo: main/Lib/os.py]"),
            ("https://github.com/facebook/react/tree/main/src", "Directorio src", "[📁 Directorio de GitHub de facebook/react - Archivo: main/src]"),
            ("https://github.com/facebook/react/issues", "Lista de issues", "[🐛 Issue de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/issues/12345", "Issue específico", "[🐛 Issue de GitHub de facebook/react - Archivo: 12345]"),
            ("https://github.com/facebook/react/pull/6789", "Pull Request específico", "[🔄 Pull Request de GitHub de facebook/react - Archivo: 6789]"),
            ("https://github.com/vuejs/vue/pulls", "Lista de PRs", "[🔄 Pull Request de GitHub de vuejs/vue]"),
            ("https://github.com/facebook/react/commit/a1b2c3d4", "Commit corto", "[🔗 Commit de GitHub de facebook/react - Archivo: a1b2c3d4]"),
            ("https://github.com/facebook/react/releases", "Lista de releases", "[🎉 Release de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/releases/tag/v18.0.0", "Release específica", "[🎉 Release de GitHub de facebook/react - Archivo: tag/v18.0.0]"),
            ("https://github.com/facebook/react/wiki", "Wiki principal", "[📚 Wiki de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/wiki/Getting-Started", "Página wiki", "[📚 Wiki de GitHub de facebook/react - Archivo: Getting-Started]"),
            ("https://github.com/facebook/react/projects/1", "Proyecto específico", "[📊 Proyecto de GitHub de facebook/react - Archivo: 1]"),
            ("https://github.com/facebook/react/actions", "GitHub Actions", "[⚙️ Actions de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/security", "Seguridad", "[🛡️ Security de GitHub de facebook/react]"),
            ("https://gist.github.com/octocat/abcdef1234567890", "Gist específico", "[📝 Gist de GitHub de octocat - Archivo: abcdef1234567890]"),
            ("https://gist.github.com/torvalds", "Gist de usuario", "[📝 Gists de GitHub de torvalds]"),
            ("https://github.com/facebook/react/compare/main...dev", "Comparación de ramas", "[💻 Repositorio de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/tags", "Tags", "[💻 Repositorio de GitHub de facebook/react]"),
            ("https://github.com/facebook/react/branches", "Ramas", "[💻 Repositorio de GitHub de facebook/react]")
        ]

        for url, description, expected in test_cases:
            try:
                result = self.processor.process_url(url)
                success = result.strip() == expected.strip()

                details = {
                    'URL': url,
                    'Descripción': description,
                    'Resultado': result,
                    'Esperado': expected,
                    'Coincide': "SÍ" if success else "NO"
                }

                self.add_test_result(f"GitHub - {description}", success, details)
                self.print_test_result(f"GitHub - {description}", success, details)

            except Exception as e:
                self.add_test_result(f"GitHub - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"GitHub - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })


if __name__ == "__main__":
    tester = GitHubTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()
