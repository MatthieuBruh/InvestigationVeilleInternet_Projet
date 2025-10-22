import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

from comments_scraper import scrap_comments
from dbConfig import get_connection
from utils import normalize_date, get_driver_requirements, accept_cookies, load_page


def save_data(art_id, art_titre, art_categorie, art_date, art_description, art_url, art_commentaires_actifs):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        art_nom_journal = "20minutes"
        cursor.execute("""
                       INSERT IGNORE INTO UNIL_Article (art_id, art_titre, art_url, art_categorie,art_date, art_description, art_commentaires_actifs, art_nom_journal)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?);""", (art_id, art_titre, art_url, art_categorie, normalize_date(art_date), art_description, art_commentaires_actifs, art_nom_journal))
        conn.commit()
    except Exception as e:
        exit(2)
    finally:
        cursor.close()
        conn.close()

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

def process_data(art_url, categorie, dr):
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

def setup():
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrap_article(article_url, categorie):
    driver = setup()
    load_page(driver, article_url)
    accept_cookies(driver)
    process_data(article_url, categorie, driver)
    if has_comments_section(article_url):
        scrap_comments(driver, get_id(article_url), get_url_comments(article_url))
    driver.quit()

#if __name__ == '__main__':
    #scrap_article("https://www.20min.ch/fr/story/trafic-ferroviaire-l-abonnement-demi-tarif-pourrait-bientot-disparaitre-103433886")