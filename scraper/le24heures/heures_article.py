import requests
from datetime import datetime
from selenium.webdriver.common.by import By

from heures_comments import scrap_comments
from scraper.dbConfig import get_connection
from scraper.utils import normalize_date, load_cookies, get_driver_requirements
from selenium import webdriver

# ✅ BATCH POUR ARTICLES
_article_batch = []
ARTICLE_BATCH_SIZE = 10


def save_data(art_id, art_titre, art_categorie, art_date, art_description, art_url, art_commentaires_actifs):
    """Sauvegarde en batch pour optimisation"""
    global _article_batch

    art_nom_journal = "24heures.ch"
    art_date_article = str(datetime.now())

    _article_batch.append((
        art_id,
        art_titre,
        art_url,
        art_categorie,
        normalize_date(art_date),
        art_description,
        1 if art_commentaires_actifs else 0,
        art_nom_journal,
        art_date_article
    ))

    # Flush quand le batch est plein
    if len(_article_batch) >= ARTICLE_BATCH_SIZE:
        flush_article_batch()

def save_pdf_details(art_id, art_nom_pdf, art_hash_pdf):
    conn = get_connection()
    try:
        conn.execute("""UPDATE UNIL_Article SET art_nom_pdf = ?, art_hash_pdf = ? WHERE art_id = ?""",
                     (art_nom_pdf, art_hash_pdf, art_id))
        conn.commit()
        print(f"  ✓ {art_id} article dont le PDF a été inséré en BDD.")
    except Exception as e:
        print(f"  ❌ Erreur insertion des détails du PDF de l'articles: {e}")
        conn.rollback()


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
            (art_id, art_titre, art_url, art_categorie, art_date, art_description, art_commentaires_actifs, art_nom_journal, art_date_recolte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                          "/html/body/div[1]/div/div[5]/div[2]/main/article/div[2]/h2/span")
    return val.text


def get_date(dr):
    # Utilise un sélecteur CSS plus flexible
    try:
        time_element = dr.find_element(By.CSS_SELECTOR, "article time[datetime]")
        return time_element.get_attribute("datetime")
    except Exception:
        print("  ⚠️ Date non trouvée")
        return None


def get_description(dr):
    res = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[5]/div[2]/main/article/div[2]/p/span/span")
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
    art_id = get_id(art_url)
    print("ID:", art_id)
    art_title = get_title(dr)
    print("Title:", art_title)
    art_date = get_date(dr)
    print("Date:", art_date)
    art_description = get_description(dr)
    print("Description:", art_description)


def scrap_article(driver, article_url, category):
    driver.get(article_url)
    # load_cookies(driver, f"session_cookies_{category}.pkl")
    driver.refresh()
    process_article(article_url, category, driver)

    """has_comments = process_article(article_url, category, driver)

    if has_comments:
        print(f"\t✓ Commentaires actifs pour {article_url}")
        flush_article_batch()
        pdf_path, pdf_hash = scrap_comments(driver, get_id(article_url), get_url_comments(article_url))
        save_pdf_details(get_id(article_url), pdf_path, pdf_hash)
    else:
        print(f"\t⊘ Commentaires désactivés pour {article_url}")"""

if __name__ == '__main__':
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(options=options)
    scrap_article(driver, "https://www.24heures.ch/climat-la-suisse-se-rechauffe-deux-fois-plus-vite-184660552738", "TEST_CAT")
    print("="*120)
    scrap_article(driver, 'https://www.24heures.ch/argovie-un-chien-policier-arrete-deux-vandales-de-parcometre-896949407030', "TEST_CAT")

    # https://www.24heures.ch/comment/184660552738