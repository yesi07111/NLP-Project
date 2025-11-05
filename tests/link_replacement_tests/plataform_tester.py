from tests.link_replacement_tests.extractors.amazon_tester import AmazonTester, Tester
from tests.link_replacement_tests.extractors.discord_tester import DiscordTester
from tests.link_replacement_tests.extractors.facebook_tester import FacebookTester
from tests.link_replacement_tests.extractors.flickr_tester import FlickrTester
from tests.link_replacement_tests.extractors.likee_tester import LikeeTester
from tests.link_replacement_tests.extractors.linkedIn_tester import LinkedInTester
from tests.link_replacement_tests.extractors.medium_tester import MediumTester
from tests.link_replacement_tests.extractors.pinterest_tester import PinterestTester
from tests.link_replacement_tests.extractors.reddist_tester import RedditTester
from tests.link_replacement_tests.extractors.snapchat_tester import SnapchatTester
from tests.link_replacement_tests.extractors.stackoverflow_tester import StackOverflowTester
from tests.link_replacement_tests.extractors.threads_tester import ThreadsTester
from tests.link_replacement_tests.extractors.tumblr_tester import TumblrTester
from tests.link_replacement_tests.extractors.twitter_tester import TwitterTester
from tests.link_replacement_tests.extractors.whatsapp_tester import WhatsAppTester
from tests.link_replacement_tests.extractors.youtube_tester import YouTubeTester
from tests.link_replacement_tests.extractors.github_tester import GitHubTester
from tests.link_replacement_tests.extractors.gitlab_tester import GitLabTester
from tests.link_replacement_tests.extractors.google_tester import GoogleTester
from tests.link_replacement_tests.extractors.imgur_tester import ImgurTester
from tests.link_replacement_tests.extractors.instagram_tester import InstagramTester

class PlatformTester(Tester):
    """Tester principal que ejecuta todos los testers de plataformas"""
    
    def __init__(self, verbose=False):
        super().__init__(verbose)
        self.platform_testers = [
            AmazonTester(verbose),
            DiscordTester(verbose), 
            FacebookTester(verbose),
            FlickrTester(verbose),
            LikeeTester(verbose),
            LinkedInTester(verbose),
            MediumTester(verbose),
            PinterestTester(verbose),
            RedditTester(verbose),
            SnapchatTester(verbose),
            StackOverflowTester(verbose),
            ThreadsTester(verbose),
            TumblrTester(verbose),
            TwitterTester(verbose),
            WhatsAppTester(verbose),
            YouTubeTester(verbose),
            AmazonTester(verbose),
            DiscordTester(verbose),
            FacebookTester(verbose),
            GitHubTester(verbose),
            GitLabTester(verbose),
            GoogleTester(verbose),
            ImgurTester(verbose),
            InstagramTester(verbose)
        ]
    
    def run_all_tests(self):
        """Ejecuta todos los tests de todas las plataformas"""
        print("🚀 Iniciando tests de todas las plataformas...\n")
        
        for tester in self.platform_testers:
            tester.run_all_tests()
            # Recopilar resultados de cada tester
            for test_result in tester.tests_results:
                self.add_test_result(
                    test_result['name'],
                    test_result['success'],
                    test_result['details']
                )
            
            print(f"\n{'='*60}\n")


if __name__ == "__main__":
    tester = PlatformTester(verbose=False)
    tester.run_all_tests()
    tester.print_summary()
