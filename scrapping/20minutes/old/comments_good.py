from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException
)
import time
from typing import List, Tuple, Optional


class CommentScraper:
    """Scraper pour extraire les commentaires de 20min.ch"""

    def __init__(self, url: str, headless: bool = False):
        """
        Initialise le scraper

        Args:
            url: URL de la page de commentaires
            headless: Si True, lance le navigateur en mode sans interface
        """
        self.url = url
        self.driver = self._init_driver(headless)

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        """
        Initialise et configure le driver Chrome

        Args:
            headless: Mode sans interface graphique

        Returns:
            Instance du driver Chrome configuré
        """
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            raise RuntimeError(f"Impossible d'initialiser le driver Chrome: {e}")

    def load_page(self, initial_wait: int = 5) -> bool:
        """
        Charge la page des commentaires

        Args:
            initial_wait: Temps d'attente initial en secondes

        Returns:
            True si le chargement a réussi, False sinon
        """
        try:
            print(f"📄 Chargement de la page: {self.url}")
            self.driver.get(self.url)
            time.sleep(initial_wait)
            print("✅ Page chargée avec succès")
            return True
        except WebDriverException as e:
            print(f"❌ Erreur lors du chargement de la page: {e}")
            return False

    def get_all_articles(self) -> List:
        """
        Récupère tous les articles de la page

        Returns:
            Liste des éléments article
        """
        try:
            articles = self.driver.find_elements(By.TAG_NAME, "article")
            return articles
        except Exception as e:
            print(f"⚠️ Erreur lors de la récupération des articles: {e}")
            return []

    def filter_comment_articles(self, articles: List) -> List:
        """
        Filtre les articles pour ne garder que ceux qui contiennent des commentaires

        Args:
            articles: Liste de tous les articles

        Returns:
            Liste filtrée des articles de commentaires
        """
        comment_articles = []
        for article in articles:
            try:
                # Vérifier si l'article contient des boutons (typique d'un commentaire)
                if article.find_elements(By.TAG_NAME, "button"):
                    comment_articles.append(article)
            except (StaleElementReferenceException, NoSuchElementException):
                continue
            except Exception as e:
                print(f"⚠️ Erreur lors du filtrage d'un article: {e}")
                continue

        return comment_articles

    def scroll_to_load_all_comments(
            self,
            max_attempts: int = 200,
            scroll_pause: float = 2.0
    ) -> int:
        """
        Scroll progressivement pour charger tous les commentaires

        Args:
            max_attempts: Nombre maximum de tentatives de scroll
            scroll_pause: Temps d'attente après chaque scroll (secondes)

        Returns:
            Nombre total d'articles chargés
        """
        previous_count = 0
        no_change_count = 0
        attempt = 0

        print("\n🔄 Début du chargement des commentaires principaux...")

        try:
            while attempt < max_attempts:
                # Scroll jusqu'en bas
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)

                # Compter les articles actuels
                current_count = len(self.get_all_articles())
                print(f"Tentative {attempt + 1}: {current_count} articles chargés")

                # Vérifier si le nombre a changé
                if current_count == previous_count:
                    no_change_count += 1
                    if no_change_count >= 3:
                        print("✅ Tous les commentaires principaux semblent être chargés")
                        break
                else:
                    no_change_count = 0

                previous_count = current_count
                attempt += 1

            if attempt >= max_attempts:
                print(f"⚠️ Limite de {max_attempts} tentatives atteinte")

            return previous_count

        except WebDriverException as e:
            print(f"❌ Erreur lors du scroll: {e}")
            return previous_count

    def extract_comment_data(self, article) -> Tuple[str, str]:
        """
        Extrait le pseudo et le contenu d'un article

        Args:
            article: Élément article à analyser

        Returns:
            Tuple (pseudo, contenu)
        """
        pseudo = "[Pseudo non trouvé]"
        contenu = "[Contenu non trouvé]"

        try:
            pseudo = article.find_element(
                By.CSS_SELECTOR,
                ".sc-d8c6148a-2.IIQUY"
            ).text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction du pseudo: {e}")

        try:
            contenu = article.find_element(
                By.CSS_SELECTOR,
                ".sc-5be4c02d-0.gDVcQV"
            ).text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction du contenu: {e}")

        return pseudo, contenu

    def is_reply_button(self, button) -> bool:
        """
        Détermine si un bouton est un bouton de réponses

        Args:
            button: Élément bouton à analyser

        Returns:
            True si c'est un bouton de réponses, False sinon
        """
        try:
            if not (button.is_displayed() and button.is_enabled()):
                return False

            button_text = button.text.lower()

            # Vérifier les indicateurs de bouton de réponses
            return (
                    'réponse' in button_text or
                    'reply' in button_text or
                    'antwort' in button_text or
                    any(char.isdigit() for char in button_text)
            )
        except (StaleElementReferenceException, NoSuchElementException):
            return False
        except Exception:
            return False

    def click_reply_button_and_extract(self, article, index: int) -> Tuple[bool, int]:
        """
        Cherche et clique sur le bouton de réponses, puis extrait les réponses

        Args:
            article: Article de commentaire
            index: Numéro du commentaire

        Returns:
            Tuple (bouton_trouvé, nombre_de_réponses)
        """
        try:
            all_buttons = article.find_elements(By.TAG_NAME, "button")
        except Exception as e:
            print(f"⚠️ Impossible de récupérer les boutons: {e}")
            return False, 0

        for button in all_buttons:
            try:
                if not self.is_reply_button(button):
                    continue

                button_text = button.text
                print(f"🔽 Bouton de réponses trouvé: '{button_text}'")

                # Cliquer sur le bouton
                try:
                    button.click()
                    time.sleep(0.8)
                except Exception as e:
                    print(f"   ⚠️ Erreur lors du clic: {e}")
                    continue

                # Récupérer les réponses (articles imbriqués)
                try:
                    nested_articles = article.find_elements(By.TAG_NAME, "article")
                    num_replies = len(nested_articles)

                    if num_replies > 0:
                        print(f"   ↳ {num_replies} réponse(s) trouvée(s):\n")

                        # Afficher chaque réponse
                        for reply_idx, reply_article in enumerate(nested_articles, 1):
                            self.display_reply(reply_article, reply_idx)

                        return True, num_replies
                    else:
                        return True, 0

                except Exception as e:
                    print(f"   ⚠️ Erreur lors de l'extraction des réponses: {e}")
                    return True, 0

            except (StaleElementReferenceException, NoSuchElementException):
                continue
            except Exception as e:
                print(f"⚠️ Erreur lors du traitement d'un bouton: {e}")
                continue

        return False, 0

    def display_comment(self, pseudo: str, contenu: str, index: int):
        """
        Affiche un commentaire de manière formatée

        Args:
            pseudo: Pseudo de l'auteur
            contenu: Contenu du commentaire
            index: Numéro du commentaire
        """
        print(f"\n{'=' * 80}")
        print(f"📝 COMMENTAIRE #{index}")
        print(f"{'=' * 80}")
        print(f"👤 Pseudo: {pseudo}")
        content_preview = contenu[:200] + '...' if len(contenu) > 200 else contenu
        print(f"💬 Contenu: {content_preview}")

    def display_reply(self, reply_article, reply_idx: int):
        """
        Affiche une réponse de manière formatée

        Args:
            reply_article: Article de la réponse
            reply_idx: Numéro de la réponse
        """
        reply_pseudo, reply_contenu = self.extract_comment_data(reply_article)
        print(f"   {'─' * 76}")
        print(f"   💬 RÉPONSE #{reply_idx}")
        print(f"   👤 Pseudo: {reply_pseudo}")
        content_preview = reply_contenu[:150] + '...' if len(reply_contenu) > 150 else reply_contenu
        print(f"   💬 Contenu: {content_preview}")

    def process_all_comments(self) -> Tuple[int, int, int]:
        """
        Traite tous les commentaires et leurs réponses

        Returns:
            Tuple (nombre_commentaires, nombre_réponses, total)
        """
        print("\n💬 Traitement des commentaires et de leurs réponses...")

        # Récupérer et filtrer les articles
        all_articles = self.get_all_articles()
        comment_articles = self.filter_comment_articles(all_articles)

        total_comments = len(comment_articles)
        total_replies = 0
        comments_with_replies = 0
        buttons_clicked = 0

        print(f"   Traitement de {total_comments} articles de commentaires...\n")

        for index, article in enumerate(comment_articles, 1):
            try:
                # Scroll jusqu'à l'article
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        article
                    )
                    time.sleep(0.3)
                except Exception as e:
                    print(f"⚠️ Impossible de scroller vers le commentaire {index}: {e}")

                # Extraire et afficher les données du commentaire
                pseudo, contenu = self.extract_comment_data(article)
                self.display_comment(pseudo, contenu, index)

                # Chercher et cliquer sur le bouton de réponses
                button_found, num_replies = self.click_reply_button_and_extract(article, index)

                if button_found:
                    buttons_clicked += 1
                    if num_replies > 0:
                        total_replies += num_replies
                        comments_with_replies += 1
                else:
                    print("   (Pas de réponses)")

            except StaleElementReferenceException:
                print(f"⚠️ L'article {index} n'est plus accessible (élément obsolète)")
                continue
            except Exception as e:
                print(f"⚠️ Erreur sur l'article {index}: {e}")
                continue

        # Afficher le résumé
        self.display_summary(buttons_clicked, comments_with_replies)

        return total_comments, total_replies, total_comments + total_replies

    def display_summary(self, buttons_clicked: int, comments_with_replies: int):
        """
        Affiche le résumé du traitement

        Args:
            buttons_clicked: Nombre de boutons cliqués
            comments_with_replies: Nombre de commentaires avec réponses
        """
        print(f"\n{'=' * 80}")
        print(f"✅ TRAITEMENT TERMINÉ")
        print(f"{'=' * 80}")
        print(f"   📊 {buttons_clicked} bouton(s) de réponses cliqué(s)")
        print(f"   💬 {comments_with_replies} commentaire(s) avec des réponses")

    def display_final_results(self, comments: int, replies: int, total: int):
        """
        Affiche les résultats finaux

        Args:
            comments: Nombre de commentaires
            replies: Nombre de réponses
            total: Total
        """
        print(f"\n{'=' * 80}")
        print(f"✨ RÉSULTAT FINAL")
        print(f"{'=' * 80}")
        print(f"   📝 Articles de commentaires : {comments}")
        print(f"   💬 Réponses détectées : {replies}")
        print(f"   📊 TOTAL : {total}")

        # Vérification alternative
        try:
            all_articles_final = self.driver.find_elements(By.TAG_NAME, "article")
            print(f"   🔍 Total articles sur la page (vérification): {len(all_articles_final)}")
        except Exception:
            pass

    def run(self) -> Optional[Tuple[int, int, int]]:
        """
        Execute le scraping complet

        Returns:
            Tuple (commentaires, réponses, total) ou None en cas d'erreur
        """
        try:
            # Charger la page
            if not self.load_page():
                return None

            # Scroller pour charger tous les commentaires
            comments_loaded = self.scroll_to_load_all_comments()
            print(f"\n✅ {comments_loaded} articles chargés")

            # Traiter tous les commentaires
            results = self.process_all_comments()

            # Afficher les résultats finaux
            self.display_final_results(*results)

            return results

        except Exception as e:
            print(f"❌ Erreur critique lors du scraping: {e}")
            return None

    def close(self):
        """Ferme le navigateur"""
        try:
            if self.driver:
                self.driver.quit()
                print("\n🔒 Navigateur fermé")
        except Exception as e:
            print(f"⚠️ Erreur lors de la fermeture du navigateur: {e}")


def main():
    """Fonction principale"""
    comments_url = "https://www.20min.ch/fr/comment/103433427"

    scraper = None
    try:
        # Initialiser le scraper
        scraper = CommentScraper(comments_url, headless=False)

        # Lancer le scraping
        results = scraper.run()

        if results:
            comments, replies, total = results
            print(f"\n✅ Scraping terminé avec succès!")
        else:
            print(f"\n❌ Le scraping a échoué")

    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
    finally:
        # Toujours fermer le navigateur
        if scraper:
            scraper.close()


if __name__ == '__main__':
    main()