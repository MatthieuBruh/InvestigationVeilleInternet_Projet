import time
from typing import List, Tuple

from selenium.common.exceptions import (NoSuchElementException, StaleElementReferenceException, WebDriverException)
from selenium.webdriver.common.by import By

from dbConfig import get_connection
from utils import hash_md5, sauvegarder_page_pdf

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
        articles = dr.find_elements(By.CSS_SELECTOR, ".sc-12787c8d-3.hxavaW")
        return articles
    except Exception:
        return []

def extract_comment_data(article) -> Tuple[str, str]:
    pseudo, contenu = "", ""
    try:
        pseudo = article.find_element(By.CSS_SELECTOR, ".sc-12787c8d-8.jjVQBd").text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except Exception:
        pass
    try:
        contenu = article.find_element(By.CSS_SELECTOR, ".sc-12787c8d-11.jrZiNw").text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except Exception:
        pass
    return pseudo, contenu

def process_answers(dr, art_id, comment, hash_comment):
    try:
        answers = comment.find_elements(By.CSS_SELECTOR, ".sc-12787c8d-3.beRDi")
    except:
        return False, 0
    if len(answers) <= 0:
        return False, 0
    for index, answer in enumerate(answers, 1):
        try:
            try:
                dr.execute_script("arguments[0].scrollIntoView({block: 'center'});", answer)
                time.sleep(0.3)
            except Exception:
                continue
            try:
                reply_pseudo, reply_contenu = extract_comment_data(answer)
                hash_id_reply = hash_md5(reply_pseudo + reply_contenu)
                #print("Réponse: ", art_id, hash_id_reply, reply_pseudo, reply_contenu, hash_comment)
                save_comment(art_id, hash_id_reply, reply_pseudo, reply_contenu, hash_comment)
            except Exception:
                continue
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return True, len(answers)

def process_comments(dr, art_id) -> Tuple[int, int, int]:
    comments = get_all_comments(dr)
    total_comments = len(comments)
    total_replies = 0
    comments_with_replies = 0
    for index, commentaire in enumerate(comments, 1):
        try:
            try:
                dr.execute_script("arguments[0].scrollIntoView({block: 'center'});", commentaire)
                time.sleep(0.3)
            except Exception:
                continue
            try:
                pseudo, contenu = extract_comment_data(commentaire)
                com_hash_id = hash_md5(pseudo + contenu)
                # print("Commentaire: ", art_id, com_hash_id, pseudo, contenu)
                save_comment(art_id, com_hash_id, pseudo, contenu)
                has_answers, num_replies = process_answers(dr, art_id, commentaire, com_hash_id)
                if has_answers and num_replies > 0:
                    flush_comment_batch()
                    total_replies += num_replies
                    comments_with_replies += 1
            except Exception:
                continue
        except StaleElementReferenceException:
            continue
        except Exception:
            continue
    return total_comments, total_replies, comments_with_replies

def load_all_articles(dr, max_attempts: int = 200, scroll_pause: float = 2.0):
    previous_count = 0
    no_change_count = 0
    attempt = 0
    try:
        while attempt < max_attempts:
            dr.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            current_count = len(get_all_comments(dr))
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
            previous_count = current_count
            attempt += 1
        return previous_count
    except WebDriverException:
        return previous_count


def scrap_comments(driver, art_id, art_comments_url):
    driver.get(art_comments_url)
    load_all_articles(driver)
    pdf_path, pdf_hash = sauvegarder_page_pdf(driver, "lematin-" + art_id + '.pdf')
    total_com, total_rep, com_with_rep = process_comments(driver, art_id)
    # Flush après chaque article avec commentaires
    flush_comment_batch()
    print(f"    → {total_com} commentaires, {total_rep} réponses")
    return pdf_path, pdf_hash