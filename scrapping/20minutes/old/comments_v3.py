from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import time

# Configuration
ARTICLE_URL = "https://www.20min.ch/fr/comment/103433427"
# CHROMEDRIVER_PATH = r"C:\Users\augus\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe"

# Créer la base SQLite
conn = sqlite3.connect("../comments_20min.db")
cursor = conn.cursor()
cursor.execute("""
               CREATE TABLE IF NOT EXISTS comments
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   pseudo
                   TEXT,
                   contenu
                   TEXT,
                   timestamp
                   TEXT
               )
               """)
conn.commit()


def scrape_comments_with_selenium(url):
    """Scrape les commentaires via Selenium"""
    # service = Service(CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Optionnel : sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 💡 Ajout de headers réalistes et désactivation de la détection Selenium
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    try:
        print("Chargement de la page...")
        driver.get(url)

        # ⏳ Attendre que la section des commentaires soit chargée
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sc-5be4c02d-2.jeSlbI")))

        # 📜 Scroller pour charger plus de commentaires (si pagination infinie)
        def scroll_to_load_all_comments(driver, max_scrolls=100, scroll_increment=800, wait_time=2):
            """
            Scrolle progressivement vers le bas pour charger tous les commentaires.
            Sarrête quand la hauteur de la page ne change plus (fin atteinte)."""

            last_height = driver.execute_script("return document.body.scrollHeight")
            scrolls = 0
            no_change_count = 0  # Compteur pour détecter stagnation

            while scrolls < max_scrolls and no_change_count < 3:
                # Scroller d'un incrément fixe (ex: 800px)
                driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
                time.sleep(wait_time)

                # Vérifier la nouvelle hauteur
                new_height = driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    no_change_count += 1  # Pas de changement → on approche de la fin
                else:
                    no_change_count = 0  # Nouveau contenu chargé

                last_height = new_height
                scrolls += 1

            print(f"Scroll terminé après {scrolls} défilements.")

        # Lancer le scrolling pour charger tous les commentaires
        scroll_to_load_all_comments(driver)

        def expand_all_replies(driver):
            try:
                # On cherche tous les boutons avec la classe spécifique
                reply_buttons = driver.find_elements(By.CSS_SELECTOR, "button.sc-fabbaaec-0.dLNZIc")
                print(f"{len(reply_buttons)} boutons 'réponses à afficher' trouvés.")

                for i, button in enumerate(reply_buttons):
                    try:
                        # Faire défiler jusqu’au bouton pour qu’il soit visible
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.5)  # Petit délai pour stabiliser le scroll

                        # Cliquer uniquement s’il est cliquable
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(button))
                        button.click()
                        print(f" → Clic {i + 1}/{len(reply_buttons)} effectué.")
                        time.sleep(1)  # Attendre le chargement des réponses
                    except Exception as e:
                        print(f"   ⚠ Impossible de cliquer sur le bouton {i + 1}: {e}")
                        continue

                print("Tous les boutons de réponses ont été traités.")
            except Exception as e:
                print(f"Erreur lors de l'expansion des réponses : {e}")

        expand_all_replies(driver)

        # 🔍 Extraire les commentaires
        comment_elements = driver.find_elements(By.CSS_SELECTOR, ".sc-5be4c02d-2.jeSlbI")
        answer_elements = driver.find_elements(By.CSS_SELECTOR, ".sc-5be4c02d-2.fOupCr")
        comments = []

        for elem in comment_elements:
            try:
                pseudo = elem.find_element(By.CSS_SELECTOR, ".sc-d8c6148a-2.IIQUY").text.strip()
            except:
                pseudo = "Anonyme"

            try:
                contenu = elem.find_element(By.CSS_SELECTOR, ".sc-5be4c02d-0.gDVcQV").text.strip()
            except:
                contenu = "[Contenu non disponible]"

            # Pas de timestamp visible → on met la date actuelle ou "N/A"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            comments.append({
                "pseudo": pseudo,
                "contenu": contenu,
                "timestamp": timestamp
            })
        for elem in answer_elements:
            try:
                pseudo = elem.find_element(By.CSS_SELECTOR, ".sc-d8c6148a-2.IIQUY").text.strip()
            except:
                pseudo = "Anonyme"

            try:
                contenu = elem.find_element(By.CSS_SELECTOR, ".sc-5be4c02d-0.gDVcQV").text.strip()
            except:
                contenu = "[Contenu non disponible]"

            # Pas de timestamp visible → on met la date actuelle ou "N/A"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            comments.append({
                "pseudo": pseudo,
                "contenu": contenu,
                "timestamp": timestamp
            })

        return comments

    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return []

    finally:
        driver.quit()


def save_to_db(comments):
    """Sauvegarde les commentaires dans la base de données"""
    for c in comments:
        cursor.execute("""
                       INSERT INTO comments (pseudo, contenu, timestamp)
                       VALUES (?, ?, ?)
                       """, (c["pseudo"], c["contenu"], c["timestamp"]))
    conn.commit()
    print(f"{len(comments)} commentaires sauvegardés.")


# Exécution principale
if __name__ == '__main__':
    print("Récupération des commentaires via Selenium...")
    comments = scrape_comments_with_selenium(ARTICLE_URL)
    if comments:
        save_to_db(comments)
    else:
        print("Aucun commentaire récupéré.")

    conn.close()