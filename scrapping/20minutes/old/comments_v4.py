from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_comments_count(driver):
    """Retourne le nombre actuel de commentaires principaux chargés"""
    try:
        # Compter les articles avec l'une des deux classes
        articles_jeSlbI = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.jeSlbI")
        articles_fOupCr = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.fOupCr")
        return len(articles_jeSlbI) + len(articles_fOupCr)
    except:
        return 0


def scroll_to_load_all_comments(driver, max_attempts=50, scroll_pause=2):
    """
    Scroll progressivement jusqu'à charger tous les commentaires principaux

    Args:
        driver: Instance du webdriver
        max_attempts: Nombre maximum de tentatives de scroll
        scroll_pause: Temps d'attente après chaque scroll (en secondes)

    Returns:
        int: Nombre total de commentaires principaux chargés
    """
    previous_count = 0
    no_change_count = 0
    attempt = 0

    print("🔄 Début du chargement des commentaires principaux...")

    while attempt < max_attempts:
        # Scroll jusqu'en bas de la page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Attendre que le contenu se charge
        time.sleep(scroll_pause)

        # Compter les commentaires actuels
        current_count = get_comments_count(driver)

        print(f"Tentative {attempt + 1}: {current_count} commentaires principaux chargés")

        # Si le nombre n'a pas changé
        if current_count == previous_count:
            no_change_count += 1
            # Si ça fait 3 fois qu'il n'y a pas de changement, on arrête
            if no_change_count >= 3:
                print("✅ Tous les commentaires principaux semblent être chargés")
                break
        else:
            no_change_count = 0

        previous_count = current_count
        attempt += 1

    if attempt >= max_attempts:
        print(f"⚠️ Limite de {max_attempts} tentatives atteinte")

    return current_count


def process_all_comments_and_replies(driver):
    """
    Parcourt tous les commentaires (articles) et clique sur les boutons de réponses s'ils existent

    Returns:
        tuple: (nombre de commentaires, nombre de réponses, total)
    """
    print("\n💬 Traitement des commentaires et de leurs réponses...")

    # Récupérer tous les articles de commentaires (les deux classes)
    articles_jeSlbI = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.jeSlbI")
    articles_fOupCr = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.fOupCr")
    all_articles = articles_jeSlbI + articles_fOupCr

    total_comments = len(all_articles)
    total_replies = 0
    comments_with_replies = 0

    print(f"   Traitement de {total_comments} commentaires...")
    print(f"   ({len(articles_jeSlbI)} jeSlbI + {len(articles_fOupCr)} fOupCr)")

    for index, article in enumerate(all_articles, 1):
        try:
            # Scroll jusqu'au commentaire pour le rendre visible
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
            time.sleep(0.2)

            # Chercher un bouton de réponses dans cet article
            try:
                reply_button = article.find_element(By.CSS_SELECTOR, "button.sc-fabbaaec-0.dLNZIc")

                # Si le bouton existe et est cliquable
                if reply_button.is_displayed() and reply_button.is_enabled():
                    # Cliquer sur le bouton
                    reply_button.click()
                    time.sleep(0.5)  # Attendre que les réponses se chargent

                    # Compter les réponses dans cet article
                    replies = article.find_elements(By.CSS_SELECTOR, "div.sc-5be4c02d-1.fysers")
                    num_replies = len(replies)

                    if num_replies > 0:
                        total_replies += num_replies
                        comments_with_replies += 1
                        print(f"   Commentaire {index}/{total_comments}: {num_replies} réponse(s) chargée(s)")

            except:
                # Pas de bouton de réponses dans ce commentaire
                pass

        except Exception as e:
            print(f"   ⚠️ Erreur sur le commentaire {index}: {str(e)}")
            continue

    print(f"\n✅ Traitement terminé:")
    print(f"   {comments_with_replies} commentaire(s) avec des réponses")

    return total_comments, total_replies, total_comments + total_replies


if __name__ == '__main__':
    comments_url = "https://www.20min.ch/fr/comment/103433427"

    # Options du navigateur
    options = Options()
    # options.add_argument("--headless")  # Optionnel : sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Ajout de headers réalistes et désactivation de la détection Selenium
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Démarrage du navigateur
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(comments_url)
        print("📄 Page chargée, attente initiale...")
        time.sleep(5)

        # ÉTAPE 1 : Scroll pour charger tous les commentaires principaux
        comments_loaded = scroll_to_load_all_comments(driver, max_attempts=50, scroll_pause=2)
        print(f"\n✅ {comments_loaded} commentaires principaux chargés")

        # ÉTAPE 2 : Parcourir chaque commentaire et cliquer sur les boutons de réponses
        comments_count, replies_count, total = process_all_comments_and_replies(driver)

        # Résultat final
        print(f"\n✨ Résultat final :")
        print(f"   📝 Commentaires principaux : {comments_count}")
        print(f"   💬 Réponses : {replies_count}")
        print(f"   📊 TOTAL : {total}")

        # Tu peux maintenant extraire les données si nécessaire
        # articles_jeSlbI = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.jeSlbI")
        # articles_fOupCr = driver.find_elements(By.CSS_SELECTOR, "article.sc-5be4c02d-2.fOupCr")
        # all_articles = articles_jeSlbI + articles_fOupCr
        # for article in all_articles:
        #     print(article.text)
        #     replies = article.find_elements(By.CSS_SELECTOR, "div.sc-5be4c02d-1.fysers")
        #     for reply in replies:
        #         print("  →", reply.text)

    finally:
        # Fermer le navigateur
        driver.quit()