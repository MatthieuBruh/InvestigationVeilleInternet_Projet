from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_comments_count(driver):
    """Retourne le nombre actuel de commentaires chargés"""
    try:
        divs = driver.find_elements(By.CSS_SELECTOR, "div.sc-c28ab467-3.lrona")
        return len(divs)
    except:
        return 0


def scroll_to_load_all_comments(driver, max_attempts=50, scroll_pause=2):
    """
    Scroll progressivement jusqu'à charger tous les commentaires

    Args:
        driver: Instance du webdriver
        max_attempts: Nombre maximum de tentatives de scroll
        scroll_pause: Temps d'attente après chaque scroll (en secondes)

    Returns:
        int: Nombre total de commentaires chargés
    """
    previous_count = 0
    no_change_count = 0
    attempt = 0

    print("Début du chargement des commentaires...")

    while attempt < max_attempts:
        # Scroll jusqu'en bas de la page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Attendre que le contenu se charge
        time.sleep(scroll_pause)

        # Compter les commentaires actuels
        current_count = get_comments_count(driver)

        print(f"Tentative {attempt + 1}: {current_count} commentaires chargés")

        # Si le nombre n'a pas changé
        if current_count == previous_count:
            no_change_count += 1
            # Si ça fait 3 fois qu'il n'y a pas de changement, on arrête
            if no_change_count >= 3:
                print("Tous les commentaires semblent être chargés")
                break
        else:
            no_change_count = 0

        previous_count = current_count
        attempt += 1

    if attempt >= max_attempts:
        print(f"Limite de {max_attempts} tentatives atteinte")

    return current_count


if __name__ == '__main__':
    comments_url = "https://www.20min.ch/fr/comment/103432664"

    # Options du navigateur
    options = Options()
    # options.add_argument("--headless")  # Optionnel : sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

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
        print("Page chargée, attente initiale...")
        time.sleep(5)  # Attente initiale pour le chargement de la page

        # Scroll et chargement de tous les commentaires
        total_comments = scroll_to_load_all_comments(driver, max_attempts=50, scroll_pause=2)

        print(f"\nNombre total de commentaires chargés : {total_comments}")

        # Récupération finale de tous les commentaires
        all_comments = driver.find_elements(By.CSS_SELECTOR, "div.sc-c28ab467-3.lrona")
        print(f"Vérification finale : {len(all_comments)} commentaires trouvés")

        # Ici tu peux ajouter ton code pour extraire les données de chaque commentaire
        # for comment in all_comments:
        #     print(comment.text)

    finally:
        # Fermer le navigateur
        driver.quit()