import time
from typing import List, Tuple

from selenium.common.exceptions import (NoSuchElementException, StaleElementReferenceException, WebDriverException)
from selenium.webdriver.common.by import By

from scraper.dbConfig import get_connection
from scraper.utils import hash_md5, sauvegarder_page_avec_modal_pdf

# ✅ BATCH POUR COMMENTAIRES
_comment_batch = []
COMMENT_BATCH_SIZE = 20

def save_comment(art_id, com_id, com_author, com_content, com_ref_id=None):
    """Sauvegarde en batch (commentaire ou réponse)"""
    global _comment_batch

    _comment_batch.append((
        com_id,
        com_author,
        com_content,
        art_id,
        com_ref_id
    ))

    # Flush quand le batch est plein
    if len(_comment_batch) >= COMMENT_BATCH_SIZE:
        flush_comment_batch()

def flush_comment_batch():
    """Insère tous les commentaires en attente"""
    global _comment_batch

    if not _comment_batch:
        return

    conn = get_connection()

    try:
        conn.executemany("""
                         INSERT
                         OR IGNORE INTO UNIL_Commentaire
            (com_id, com_auteur, com_contenu, com_art_id, com_commentaire_parent)
            VALUES (?, ?, ?, ?, ?)
                         """, _comment_batch)
        conn.commit()
        print(f"    ✓ {len(_comment_batch)} commentaire(s) insérés en batch")
        _comment_batch = []

    except Exception as e:
        print(f"    ❌ Erreur batch commentaires: {e}")
        conn.rollback()
        _comment_batch = []

def get_all_comments(dr) -> List:
    try:
        comments = dr.find_elements(By.CSS_SELECTOR,"ul.comment-list > section.CommentItem_root__C_rfr")
        return comments
    except Exception as e:
        print(e)
        return []


def extract_comment_data(cmt, is_comment = True) -> Tuple[str, str, list]:
    """Extrait le pseudo, le contenu et les réponses d'un commentaire."""

    def safe_get_text(by, selector, default=""):
        try:
            return cmt.find_element(by, selector).text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            return default

    def safe_get_elements(by, selector):
        try:
            return cmt.find_elements(by, selector)
        except (NoSuchElementException, StaleElementReferenceException):
            return []

    pseudo = safe_get_text(By.CLASS_NAME, "CommentItem_nickname__iDUQA")
    contenu = safe_get_text(By.CSS_SELECTOR, ".CommentItem_text__rsEMC p")
    if is_comment:
        reponses = safe_get_elements(By.CLASS_NAME, "CommentItem_root__C_rfr")
    else:
        reponses = []

    return pseudo, contenu, reponses

def process_answers(dr, art_id, com_hash, reponses):
    for index, reponse in enumerate(reponses, 1):
        try:
            dr.execute_script("arguments[0].scrollIntoView({block: 'center'});", reponse)
            time.sleep(0.3)
        except Exception:
            continue
        try:
            pseudo, contenu, reponses = extract_comment_data(reponse, False)
            hash_id_reply = hash_md5(pseudo + contenu)
            save_comment(art_id, hash_id_reply, pseudo, contenu, com_hash)
        except (StaleElementReferenceException, NoSuchElementException):
            continue
        except Exception:
            continue

def process_comments(dr, art_id) -> Tuple[int, int, int]:
    comments = get_all_comments(dr)
    total_comments = len(comments)
    total_replies = 0
    comments_with_replies = 0
    for index, comment in enumerate(comments, 1):
        try:
            try:
                dr.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment)
                time.sleep(0.3)
            except Exception:
                continue
            try:
                pseudo, contenu, reponses = extract_comment_data(comment)
                com_hash_id = hash_md5(pseudo + contenu)
                save_comment(art_id, com_hash_id, pseudo, contenu)
            except Exception:
                continue
            if len(reponses) > 0:
                flush_comment_batch()
                process_answers(dr, art_id, com_hash_id, reponses)
                total_replies += len(reponses)
                comments_with_replies += 1
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return total_comments, total_replies, comments_with_replies

def load_all_comments(dr, max_attempts: int = 200, scroll_pause: float = 2.0):
    """modal_comments = dr.find_element(By.XPATH, "/html/body/div[1]/div/div[5]/div[2]/main/div[3]/div/div[2]/div")"""
    attempt = 0
    try:
        while attempt < max_attempts:
            bouton = dr.find_element(By.CSS_SELECTOR, "button.Button_-secondary__QOaqE:nth-child(2)")
            dr.execute_script("arguments[0].scrollIntoView({block: 'center'});", bouton)
            time.sleep(scroll_pause)
            bouton.click()
            time.sleep(scroll_pause)
            attempt += 1
    except WebDriverException:
        return

def scrap_comments(driver, art_id):
    load_all_comments(driver)
    modal_comment = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[5]/div[2]/main/div[3]/div/div[2]/div")
    pdf_path, pdf_hash = sauvegarder_page_avec_modal_pdf(driver, "24heures-" + art_id + '.pdf', modal_comment)
    total_com, total_rep, com_with_rep = process_comments(driver, art_id)
    # Flush après chaque article avec commentaires
    flush_comment_batch()
    print(f"    → {total_com} commentaires, {total_rep} réponses")
    return pdf_path, pdf_hash