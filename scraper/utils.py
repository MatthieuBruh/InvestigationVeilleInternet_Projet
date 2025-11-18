import base64
import datetime
import hashlib
import os
import pickle
import time
from typing import Tuple

from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def normalize_date(art_date):
    """Normalise une date ISO en format SQL"""
    if not art_date:
        return None
    try:
        dt = datetime.datetime.fromisoformat(art_date.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def hash_md5(data):
    """Génère un hash MD5"""
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def load_page(dr, url):
    """Charge une page avec gestion d'erreur"""
    try:
        dr.get(url)
        time.sleep(3)
        return True
    except WebDriverException:
        return False


def get_driver_requirements() -> Tuple[Options, Service]:
    """Configure les options du driver Chrome"""
    options = Options()
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

    service = Service("/usr/bin/chromedriver")

    return options, service


def accept_cookies_20min_matin(driver):
    """Accepte les cookies si la bannière apparaît"""
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
    except Exception:
        pass

def accept_cookies_24heures(driver):
    """Accepte les cookies si la bannière apparaît"""
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
    except:
        pass
    time.sleep(2)
    try:
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "tp-close tp-active"))
        )
        close_button.click()
    except:
        pass

def save_cookies(driver, filepath):
    """Sauvegarde les cookies de session"""
    os.makedirs("cookies", exist_ok=True)
    with open(f"./cookies/{filepath}", "wb") as file:
        pickle.dump(driver.get_cookies(), file)


def load_cookies(driver, filepath):
    """Charge les cookies de session"""
    cookie_path = f"./cookies/{filepath}"
    if os.path.exists(cookie_path):
        with open(cookie_path, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        return True
    return False


def sauvegarder_page_pdf(driver, chemin_fichier):
    """
    Sauvegarde la page actuelle en PDF et retourne le hash
    """
    # Calculer la hauteur de la page pour capturer tout le contenu
    hauteur_totale = driver.execute_script("return document.body.scrollHeight")

    # Configuration de l'impression
    print_options = {
        'landscape': True,
        'displayHeaderFooter': True,
        'printBackground': True,
        'preferCSSPageSize': True,
        'paperWidth': 8.27,  # A4 en pouces
        'paperHeight': 11.69,
    }

    # Exécuter la commande d'impression via Chrome DevTools
    result = driver.execute_cdp_cmd("Page.printToPDF", print_options)

    # Décoder le PDF
    pdf_data = base64.b64decode(result['data'])

    # Calculer le hash SHA-256
    hash_sha256 = hashlib.sha256(pdf_data).hexdigest()

    # Sauvegarder le PDF
    with open("./pdf/" + chemin_fichier, 'wb') as f:
        f.write(pdf_data)

    print(f"\tPDF sauvegardé : {chemin_fichier}")
    print(f"\tHash SHA-256 : {hash_sha256}")

    return chemin_fichier, hash_sha256


def sauvegarder_page_avec_modal_pdf(driver, chemin_fichier, modal_element):
    """
    Sauvegarde toute la page avec le modal scrollé au premier plan
    SANS modifier la page
    """
    from PIL import Image
    import io

    # Récupérer les dimensions du modal
    hauteur_visible = driver.execute_script("return arguments[0].clientHeight;", modal_element)
    hauteur_totale = driver.execute_script("return arguments[0].scrollHeight;", modal_element)
    scroll_actuel = driver.execute_script("return arguments[0].scrollTop;", modal_element)

    print(f"\tHauteur visible du modal: {hauteur_visible}px, Hauteur totale: {hauteur_totale}px")

    screenshots = []
    scroll_position = 0

    # Remettre le scroll du modal en haut
    driver.execute_script("arguments[0].scrollTop = 0;", modal_element)
    time.sleep(0.5)

    # Prendre des screenshots de TOUTE LA PAGE en scrollant le modal
    while scroll_position < hauteur_totale:
        # Screenshot de la page entière (pas juste le modal)
        png = driver.get_screenshot_as_png()
        screenshots.append(Image.open(io.BytesIO(png)))

        # Scroller le modal (pas la page)
        scroll_position += hauteur_visible - 100  # Overlap pour continuité
        driver.execute_script(f"arguments[0].scrollTop = {scroll_position};", modal_element)
        time.sleep(0.4)

    # Restaurer la position de scroll du modal
    driver.execute_script(f"arguments[0].scrollTop = {scroll_actuel};", modal_element)

    # Combiner tous les screenshots
    if screenshots:
        total_height = sum(img.height for img in screenshots)
        max_width = max(img.width for img in screenshots)

        combined = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for img in screenshots:
            combined.paste(img, (0, y_offset))
            y_offset += img.height

        # Sauvegarder en PDF
        combined.save("./pdf/" + chemin_fichier, "PDF", resolution=100.0)

        # Calculer le hash
        img_bytes = io.BytesIO()
        combined.save(img_bytes, format='PDF')
        hash_sha256 = hashlib.sha256(img_bytes.getvalue()).hexdigest()

        print(f"\tPDF sauvegardé : {chemin_fichier}")
        print(f"\tHash SHA-256 : {hash_sha256}")

        return chemin_fichier, hash_sha256

    return None, None