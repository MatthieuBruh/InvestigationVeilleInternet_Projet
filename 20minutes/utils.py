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


def accept_cookies(driver):
    """Accepte les cookies si la bannière apparaît"""
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
    except Exception:
        pass


def save_cookies(driver, filepath):
    """Sauvegarde les cookies de session"""
    os.makedirs("./cookies", exist_ok=True)
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