from tests.base_tester import Tester, LinkProcessor

class GitLabTester(Tester):
    """Tester específico para enlaces de GitLab"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.processor = LinkProcessor()
    
    def run_all_tests(self):
        """Ejecuta todos los tests de GitLab"""
        print("🧪 Ejecutando tests de GitLab...")
        
        test_cases = [
            # Perfiles de usuario/grupo
            ("https://gitlab.com/johndoe", "Perfil de usuario", "[👤 Perfil de GitLab de johndoe]"),
            ("https://gitlab.com/gitlab-org", "Perfil de organización", "[👤 Perfil de GitLab de gitlab-org]"),
            ("https://gitlab.com/mygroup", "Perfil de grupo", "[👤 Perfil de GitLab de mygroup]"),
            ("https://gitlab.com/groups/mygroup", "Grupo de proyectos", "[👥 Grupo de GitLab de mygroup]"),
            
            # Proyectos principales
            ("https://gitlab.com/gitlab-org/gitlab", "Proyecto principal", "[💻 Proyecto de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/johndoe/my-project", "Proyecto personal", "[💻 Proyecto de GitLab de johndoe/my-project]"),
            
            # Archivos específicos
            ("https://gitlab.com/gitlab-org/gitlab/-/blob/main/README.md", "Archivo en main", "[💻 Archivo de GitLab de gitlab-org/gitlab - Archivo: main/README.md]"),
            ("https://gitlab.com/johndoe/my-project/-/blob/master/app.py", "Archivo en master", "[💻 Archivo de GitLab de johndoe/my-project - Archivo: master/app.py]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/blob/develop/CONTRIBUTING.md", "Archivo en develop", "[💻 Archivo de GitLab de gitlab-org/gitlab - Archivo: develop/CONTRIBUTING.md]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/blob/main/lib/gitlab.rb", "Archivo en subdirectorio", "[💻 Archivo de GitLab de gitlab-org/gitlab - Archivo: main/lib/gitlab.rb]"),
            
            # Directorios
            ("https://gitlab.com/gitlab-org/gitlab/-/tree/main/lib", "Directorio lib", "[📁 Directorio de GitLab de gitlab-org/gitlab - Archivo: main/lib]"),
            ("https://gitlab.com/johndoe/my-project/-/tree/master/src", "Directorio src", "[📁 Directorio de GitLab de johndoe/my-project - Archivo: master/src]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/tree/develop/spec", "Directorio spec", "[📁 Directorio de GitLab de gitlab-org/gitlab - Archivo: develop/spec]"),
            
            # Issues
            ("https://gitlab.com/gitlab-org/gitlab/-/issues", "Lista de issues", "[🐛 Issue de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/issues/12345", "Issue específico", "[🐛 Issue de GitLab de gitlab-org/gitlab - Archivo: 12345]"),
            ("https://gitlab.com/johndoe/my-project/-/issues/1", "Issue de proyecto personal", "[🐛 Issue de GitLab de johndoe/my-project - Archivo: 1]"),
            
            # Merge Requests
            ("https://gitlab.com/gitlab-org/gitlab/-/merge_requests", "Lista de MRs", "[🔄 Merge Request de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/merge_requests/67890", "Merge Request específico", "[🔄 Merge Request de GitLab de gitlab-org/gitlab - Archivo: 67890]"),
            ("https://gitlab.com/johndoe/my-project/-/merge_requests/2", "MR de proyecto personal", "[🔄 Merge Request de GitLab de johndoe/my-project - Archivo: 2]"),
            
            # Commits
            ("https://gitlab.com/gitlab-org/gitlab/-/commit/a1b2c3d4e5f67890123456789abcdef01234567", "Commit específico", "[🔗 Commit de GitLab de gitlab-org/gitlab - Archivo: a1b2c3d4e5f67890123456789abcdef01234567]"),
            ("https://gitlab.com/johndoe/my-project/-/commit/1234567890abcdef", "Commit corto", "[🔗 Commit de GitLab de johndoe/my-project - Archivo: 1234567890abcdef]"),
            
            # Tags y Releases
            ("https://gitlab.com/gitlab-org/gitlab/-/tags", "Lista de tags", "[🏷️ Tags de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/tags/v15.0.0", "Tag específico", "[🏷️ Tag de GitLab de gitlab-org/gitlab - Archivo: v15.0.0]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/releases", "Releases", "[🎉 Releases de GitLab de gitlab-org/gitlab]"),
            
            # Wiki
            ("https://gitlab.com/gitlab-org/gitlab/-/wikis", "Wiki principal", "[📚 Wiki de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/wikis/home", "Página de wiki", "[📚 Wiki de GitLab de gitlab-org/gitlab - Archivo: home]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/wikis/installation", "Página específica de wiki", "[📚 Wiki de GitLab de gitlab-org/gitlab - Archivo: installation]"),
            
            # Snippets
            ("https://gitlab.com/gitlab-org/gitlab/-/snippets", "Lista de snippets", "[📝 Snippet de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/snippets/12345", "Snippet específico", "[📝 Snippet de GitLab de gitlab-org/gitlab - Archivo: 12345]"),
            ("https://gitlab.com/snippets/12345", "Snippet global", "[📝 Snippet de GitLab - Archivo: 12345]"),
            
            # Pipelines y Jobs
            ("https://gitlab.com/gitlab-org/gitlab/-/pipelines", "Pipelines", "[⚙️ Pipeline de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/pipelines/12345", "Pipeline específico", "[⚙️ Pipeline de GitLab de gitlab-org/gitlab - Archivo: 12345]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/jobs", "Jobs", "[🔧 Job de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/jobs/12345", "Job específico", "[🔧 Job de GitLab de gitlab-org/gitlab - Archivo: 12345]"),
            
            # Settings
            ("https://gitlab.com/gitlab-org/gitlab/-/settings", "Settings del proyecto", "[⚙️ Settings de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/settings/repository", "Settings de repositorio", "[⚙️ Settings de GitLab de gitlab-org/gitlab - Archivo: repository]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/settings/ci_cd", "Settings de CI/CD", "[⚙️ Settings de GitLab de gitlab-org/gitlab - Archivo: ci_cd]"),
            
            # Activity
            ("https://gitlab.com/gitlab-org/gitlab/-/activity", "Actividad del proyecto", "[📊 Actividad de GitLab de gitlab-org/gitlab]"),
            
            # Graphs
            ("https://gitlab.com/gitlab-org/gitlab/-/graphs/main", "Gráficos de commits", "[📈 Gráficos de GitLab de gitlab-org/gitlab - Archivo: main]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/network/main", "Network graph", "[🕸️ Network de GitLab de gitlab-org/gitlab - Archivo: main]"),
            
            # Compare
            ("https://gitlab.com/gitlab-org/gitlab/-/compare?from=main&to=develop", "Comparar ramas", "[🔄 Comparar de GitLab de gitlab-org/gitlab]"),
            
            # Archivos raw
            ("https://gitlab.com/gitlab-org/gitlab/-/raw/main/README.md", "Archivo raw", "[💻 Archivo de GitLab de gitlab-org/gitlab - Archivo: main/README.md]"),
            
            # Badges
            ("https://gitlab.com/gitlab-org/gitlab/-/badges/main/pipeline.svg", "Badge de pipeline", "[🛡️ Badge de GitLab de gitlab-org/gitlab - Archivo: main/pipeline.svg]"),
            
            # Miembros
            ("https://gitlab.com/gitlab-org/gitlab/-/project_members", "Miembros del proyecto", "[👥 Miembros de GitLab de gitlab-org/gitlab]"),
            
            # Milestones
            ("https://gitlab.com/gitlab-org/gitlab/-/milestones", "Milestones", "[🎯 Milestone de GitLab de gitlab-org/gitlab]"),
            ("https://gitlab.com/gitlab-org/gitlab/-/milestones/1", "Milestone específico", "[🎯 Milestone de GitLab de gitlab-org/gitlab - Archivo: 1]"),
            
            # Labels
            ("https://gitlab.com/gitlab-org/gitlab/-/labels", "Labels", "[🏷️ Labels de GitLab de gitlab-org/gitlab]"),
            
            # Boards
            ("https://gitlab.com/gitlab-org/gitlab/-/boards", "Boards", "[📋 Boards de GitLab de gitlab-org/gitlab]"),
            
            # Servicios de integración
            ("https://gitlab.com/gitlab-org/gitlab/-/services", "Servicios", "[🔌 Servicios de GitLab de gitlab-org/gitlab]"),
            
            # Deploy keys
            ("https://gitlab.com/gitlab-org/gitlab/-/deploy_keys", "Deploy keys", "[🔑 Deploy Keys de GitLab de gitlab-org/gitlab]"),
            
            # Protected branches
            ("https://gitlab.com/gitlab-org/gitlab/-/protected_branches", "Ramas protegidas", "[🔒 Ramas Protegidas de GitLab de gitlab-org/gitlab]"),
            
            # Webhooks
            ("https://gitlab.com/gitlab-org/gitlab/-/hooks", "Webhooks", "[🪝 Webhooks de GitLab de gitlab-org/gitlab]"),
            
            # Import/export
            ("https://gitlab.com/gitlab-org/gitlab/-/import", "Importar proyecto", "[📥 Importar de GitLab de gitlab-org/gitlab]"),
            
            # Analytics
            ("https://gitlab.com/gitlab-org/gitlab/-/analytics", "Analíticas", "[📊 Analíticas de GitLab de gitlab-org/gitlab]"),
            
            # CI lint
            ("https://gitlab.com/gitlab-org/gitlab/-/ci/lint", "CI Lint", "[✅ CI Lint de GitLab de gitlab-org/gitlab]"),
            
            # Runners
            ("https://gitlab.com/gitlab-org/gitlab/-/runners", "Runners", "[🏃 Runners de GitLab de gitlab-org/gitlab]"),
            
            # Packages
            ("https://gitlab.com/gitlab-org/gitlab/-/packages", "Packages", "[📦 Packages de GitLab de gitlab-org/gitlab]"),
            
            # Container Registry
            ("https://gitlab.com/gitlab-org/gitlab/container_registry", "Container Registry", "[🐳 Container Registry de GitLab de gitlab-org/gitlab]"),
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
                
                self.add_test_result(f"GitLab - {description}", success, details)
                self.print_test_result(f"GitLab - {description}", success, details)
                
            except Exception as e:
                self.add_test_result(f"GitLab - {description}", False, {
                    'URL': url,
                    'Error': str(e),
                    'Descripción': description
                })
                self.print_test_result(f"GitLab - {description}", False, {
                    'URL': url,
                    'Error': str(e)
                })

# Para ejecutar los tests individualmente
if __name__ == "__main__":
    tester = GitLabTester(verbose=True)
    tester.run_all_tests()
    tester.print_summary()