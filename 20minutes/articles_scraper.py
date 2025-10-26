import requests
from selenium.webdriver.common.by import By

from comments_scraper import scrap_comments
from dbConfig import get_connection
from utils import normalize_date, load_cookies

# ✅ BATCH POUR ARTICLES
_article_batch = []
ARTICLE_BATCH_SIZE = 10


def save_data(art_id, art_titre, art_categorie, art_date, art_description, art_url, art_commentaires_actifs):
    """Sauvegarde en batch pour optimisation"""
    global _article_batch

    art_nom_journal = "20minutes_old"

    _article_batch.append((
        art_id,
        art_titre,
        art_url,
        art_categorie,
        normalize_date(art_date),
        art_description,
        1 if art_commentaires_actifs else 0,
        art_nom_journal
    ))

    # Flush quand le batch est plein
    if len(_article_batch) >= ARTICLE_BATCH_SIZE:
        flush_article_batch()


def flush_article_batch():
    """Insère tous les articles en attente en une seule requête"""
    global _article_batch

    if not _article_batch:
        return

    conn = get_connection()

    try:
        conn.executemany("""
                         INSERT
                         OR IGNORE INTO UNIL_Article 
            (art_id, art_titre, art_url, art_categorie, art_date, art_description, art_commentaires_actifs, art_nom_journal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                         """, _article_batch)

        conn.commit()

        print(f"  ✓ {len(_article_batch)} article(s) insérés en batch")
        _article_batch = []

    except Exception as e:
        print(f"  ❌ Erreur batch articles: {e}")
        conn.rollback()
        _article_batch = []


def get_id(art_url):
    return art_url.strip().split("-")[-1]


def get_title(dr):
    val = dr.find_element(By.XPATH,
                          "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[2]/h2")
    return val.text.split(":")[1].strip()


def get_date(dr):
    res = dr.find_element(By.XPATH,
                          "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[1]/div/time")
    return res.get_attribute("datetime")


def get_description(dr):
    res = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[2]/div/div/div[3]/div[3]/article/header/div[3]/p")
    return res.text


def get_url_comments(art_url):
    return "https://www.20min.ch/fr/comment/" + get_id(art_url)


def has_comments_section(comments_url) -> bool:
    try:
        response = requests.get(comments_url, timeout=4)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"  ⚠️ Erreur requête commentaires: {e}")
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
    load_cookies(driver, f"session_cookies_{category}.pkl")
    driver.refresh()

    has_comments = process_article(article_url, category, driver)

    if has_comments:
        print(f"\t✓ Commentaires actifs pour {article_url}")
        flush_article_batch()
        scrap_comments(driver, get_id(article_url), get_url_comments(article_url))
    else:
        print(f"\t⊘ Commentaires désactivés pour {article_url}")