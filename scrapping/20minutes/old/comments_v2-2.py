from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_comments_count(driver):
    """Retourne le nombre actuel de commentaires principaux chargés"""
    try:
        divs = driver.find_elements(By.CSS_SELECTOR, "div.sc-c28ab467-3.lrona")
        return len(divs)
    except:
        return 0


def get_replies_count(driver):
    """Retourne le nombre actuel de réponses chargées"""
    try:
        replies = driver.find_elements(By.CSS_SELECTOR, "div.sc-5be4c02d-1.fysers")
        return len(replies)
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


def click_all_reply_buttons(driver):
    """
    Clique sur tous les boutons de réponses pour afficher toutes les réponses
    Utilise un set pour tracker les boutons déjà cliqués

    Returns:
        int: Nombre de boutons cliqués
    """
    print("\n💬 Chargement des réponses aux commentaires...")

    # Remonter en haut de la page
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    clicked_buttons = set()  # Pour tracker les boutons déjà cliqués
    clicked_count = 0
    previous_replies_count = get_replies_count(driver)
    no_change_count = 0

    while no_change_count < 3:  # S'arrête après 3 itérations sans nouveau clic
        # Trouver tous les boutons de réponses
        reply_buttons = driver.find_elements(By.CSS_SELECTOR, "button.sc-fabbaaec-0.dLNZIc")

        if not reply_buttons:
            print("   Aucun bouton de réponse trouvé")
            break

        buttons_clicked_this_round = 0

        for i, button in enumerate(reply_buttons):
            try:
                # Créer un identifiant unique pour le bouton
                button_id = id(button)

                # Si on a déjà cliqué sur ce bouton, on passe
                if button_id in clicked_buttons:
                    continue

                # Vérifier si le bouton est visible et cliquable
                if button.is_displayed() and button.is_enabled():
                    # Scroll jusqu'au bouton
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                    time.sleep(0.3)

                    # Cliquer sur le bouton
                    button.click()
                    clicked_buttons.add(button_id)
                    clicked_count += 1
                    buttons_clicked_this_round += 1
                    time.sleep(0.5)
            except Exception as e:
                continue

        print(f"   → {buttons_clicked_this_round} nouveau(x) bouton(s) cliqué(s) (total: {clicked_count})")

        # Vérifier si le nombre de réponses a changé
        time.sleep(1)
        current_replies_count = get_replies_count(driver)

        if current_replies_count == previous_replies_count and buttons_clicked_this_round == 0:
            no_change_count += 1
        else:
            no_change_count = 0

        previous_replies_count = current_replies_count

        # Si aucun nouveau bouton cliqué, on arrête
        if buttons_clicked_this_round == 0:
            no_change_count += 1

    return clicked_count


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

        # ÉTAPE 1 : Scroll et chargement de tous les commentaires principaux
        comments_count = scroll_to_load_all_comments(driver, max_attempts=50, scroll_pause=2)
        print(f"\n✅ {comments_count} commentaires principaux chargés")

        # ÉTAPE 2 : Cliquer sur tous les boutons de réponses
        buttons_clicked = click_all_reply_buttons(driver)
        print(f"\n✅ {buttons_clicked} bouton(s) de réponses cliqué(s)")

        # ÉTAPE 3 : Compter le total final
        time.sleep(2)

        final_comments = get_comments_count(driver)
        final_replies = get_replies_count(driver)
        total = final_comments + final_replies

        print(f"\n✨ Résultat final :")
        print(f"   📝 Commentaires principaux : {final_comments}")
        print(f"   💬 Réponses : {final_replies}")
        print(f"   📊 TOTAL : {total}")

    finally:
        # Fermer le navigateur
        driver.quit()