import requests
from selenium.webdriver.common.by import By

from comments_scraper import scrap_comments
from dbConfig import get_connection
from utils import normalize_date, load_cookies


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
        # print(e)
        pass
    finally:
        cursor.close()
        conn.close()

def get_id(art_url):
    return art_url.strip().split("-")[-1]

def get_title(dr):
    val = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[2]/h2")
    return val.text.split(":")[1].strip()

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
        response = requests.get(comments_url, timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException as e:
        print("Erreur lors de la requête :", e)
        return False

def process_article(art_url, categorie, dr):
    art_title = get_title(dr)
    art_date = get_date(dr)
    art_description = get_description(dr)
    art_comments_url = get_url_comments(art_url)
    art_has_comments = has_comments_section(art_comments_url)
    save_data(get_id(art_url), art_title, categorie, art_date, art_description, art_url, art_has_comments)
    return art_has_comments


def scrap_article(driver, article_url, category):
    driver.get(article_url)
    load_cookies(driver, "session_cookies_" + category + ".pkl")
    driver.refresh()
    has_comments = process_article(article_url, category, driver)
    if has_comments:
        print("\tCommentaires actifs pour l'article", article_url)
        scrap_comments(driver, get_id(article_url), get_url_comments(article_url))
    else:
        print("\tCommentaires désactivé pour l'article", article_url)