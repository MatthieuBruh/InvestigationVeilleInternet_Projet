from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import requests


def save_data(art_id, art_title, art_category, art_date, art_description, art_url, art_has_comments):
    # TODO : faire la persistence en BDD
    return

def get_id(art_url):
    return art_url.strip().split("-")[-1]

def get_title(dr):
    val = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[2]/h2")
    return val.text.split(":")[1].strip()

def get_categorie(dr):
    res = dr.find_element(By.XPATH,
                          "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[2]/h2")
    return res.text.split(":")[0].strip()

def get_date(dr):
    res = dr.find_element(By.XPATH,"/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[1]/div/time")
    return res.get_attribute("datetime")

def get_description(dr):
    res = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[3]/p")
    return res.text

def get_url_comments(art_url):
    return "https://www.20min.ch/fr/comment/" + get_id(art_url)

def has_comments_section(comments_url)-> bool:
    try:
        response = requests.get(comments_url, timeout=10)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        print("Erreur lors de la requête :", e)
        return False

def process_data(art_url, dr):
    art_title = get_title(dr)
    # print(f"Title : {art_title}")
    art_category = get_categorie(dr)
    # print(f"Category : {art_category}")
    art_date = get_date(dr)
    # print(f"Date : {art_date}")
    art_description = get_description(dr)
    # print(f"Description : {art_description}")

    art_comments_url = get_url_comments(art_url)
    art_has_comments = has_comments_section(art_comments_url)

    save_data(get_id(art_url), art_title, art_category, art_date, art_description, art_url, art_has_comments)

def load_page(dr, art_url):
    try:
        dr.get(art_url)
        time.sleep(5)
        return True
    except WebDriverException as e:
        return False

def setup():
    # Options du navigateur (sans interface graphique)
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Démarrage du navigateur
    driver = webdriver.Chrome(options=options)
    return driver

def scrap_article(article_url):
    driver = setup()
    driver.get(article_url)
    time.sleep(5)
    process_data(article_url, driver)
    driver.quit()

if __name__ == '__main__':
    scrap_article("https://www.20min.ch/fr/story/canton-de-fribourg-villa-en-feu-les-habitants-arrivent-a-echapper-aux-flammes-103433416")