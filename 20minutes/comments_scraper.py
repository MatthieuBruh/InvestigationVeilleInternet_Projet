import time
from typing import List, Tuple

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException, StaleElementReferenceException, WebDriverException)
from selenium.webdriver.common.by import By

from dbConfig import get_connection
from utils import hash_md5, get_driver_requirements, load_page, accept_cookies


def save_answer(art_id, com_id, com_author, com_content, com_ref_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT IGNORE INTO UNIL_Commentaire (com_id, com_auteur, com_contenu, com_art_id, com_commentaire_parent)
                       VALUES (?, ?, ?, ?, ?);""", (com_id, com_author, com_content, art_id, com_ref_id))
        conn.commit()
    except Exception:
        exit(2)
    finally:
        cursor.close()
        conn.close()

def save_comment(art_id, com_id, com_author, com_content):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
                       INSERT
                       IGNORE INTO UNIL_Commentaire (com_id, com_auteur, com_contenu, com_art_id)
                           VALUES (?, ?, ?, ?);""", (com_id, com_author, com_content, art_id))
        conn.commit()
    except Exception:
        exit(2)
    finally:
        cursor.close()
        conn.close()

def get_all_comments(dr) -> List:
    try:
        articles = dr.find_elements(By.TAG_NAME, "article")
        return articles
    except Exception as e:
        print(f"Erreur lors de la récupération des articles: {e}")
        return []

def extract_comment_data(article) -> Tuple[str, str]:
    pseudo, contenu = "", ""
    try:
        pseudo = article.find_element(By.CSS_SELECTOR,".sc-d8c6148a-2.IIQUY").text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except Exception as e:
        print(f"Erreur lors de l'extraction du pseudo: {e}")
    try:
        contenu = article.find_element(By.CSS_SELECTOR, ".sc-5be4c02d-0.gDVcQV").text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        pass
    except Exception as e:
        print(f"Erreur lors de l'extraction du contenu: {e}")
    return pseudo, contenu

def is_reply_button(button) -> bool:
    try:
        if not (button.is_displayed() and button.is_enabled()):
            return False
        button_text = button.text.lower()
        return 'réponse' in button_text
    except (StaleElementReferenceException, NoSuchElementException):
        return False
    except Exception:
        return False

def process_answers(art_id, comment, hash_comment):
    try:
        all_buttons = comment.find_elements(By.TAG_NAME, "button")
    except Exception as e:
        return False, 0

    for button in all_buttons:
        try:
            if not is_reply_button(button):
                continue
            button_text = button.text
            print(f"Bouton de réponses trouvé: '{button_text}'")
            # Cliquer sur le bouton
            try:
                button.click()
                time.sleep(0.8)
            except Exception as e:
                print(f"Erreur lors du clic: {e}")
                continue
            # Récupérer les réponses (articles imbriqués)
            try:
                nested_articles = comment.find_elements(By.TAG_NAME, "article")
                num_replies = len(nested_articles)
                if num_replies > 0:
                    # Afficher chaque réponse
                    for reply_idx, reply_article in enumerate(nested_articles, 1):
                        reply_pseudo, reply_contenu = extract_comment_data(reply_article)
                        hash_id_reply = hash_md5(reply_pseudo + reply_contenu)
                        save_answer(art_id, hash_id_reply, reply_pseudo, reply_contenu, hash_comment)
                    return True, num_replies
                else:
                    return True, 0
            except Exception as e:
                print(f"Erreur lors de l'extraction des réponses: {e}")
                return True, 0

        except (StaleElementReferenceException, NoSuchElementException):
            continue
        except Exception as e:
            print(f"Erreur lors du traitement d'un bouton: {e}")
            continue
    return False, 0

def process_comments(dr, art_id) -> Tuple[int, int, int]:
    comments = get_all_comments(dr)
    total_comments = len(comments)
    total_replies = 0
    comments_with_replies = 0
    buttons_clicked = 0
    print(f"   Traitement de {total_comments} de commentaires...\n")
    for index, article in enumerate(comments, 1):
        try:
            try:
                dr.execute_script("arguments[0].scrollIntoView({block: 'center'});",article)
                time.sleep(0.3)
            except Exception as e:
                # print(f"Impossible de scroller vers le commentaire {index}: {e}")
                continue
            # Extraire les données du commentaire
            try:
                pseudo, contenu = extract_comment_data(article)
                com_hash_id = hash_md5(pseudo + contenu)
                save_comment(art_id, com_hash_id, pseudo, contenu)
            except Exception as e:
                continue
            # Chercher et cliquer sur le bouton de réponses
            button_found, num_replies = process_answers(art_id, article, com_hash_id)
            if button_found:
                buttons_clicked += 1
                if num_replies > 0:
                    total_replies += num_replies
                    comments_with_replies += 1
        except StaleElementReferenceException:
            print(f"Le commentaire {index} n'est plus accessible (élément obsolète)")
            continue
        except Exception as e:
            print(f"Erreur sur le commentaire {index}: {e}")
            continue

def load_all_articles(dr, max_attempts: int = 200,scroll_pause: float = 2.0):
    previous_count = 0
    no_change_count = 0
    attempt = 0
    try:
        while attempt < max_attempts:
            # Scroll jusqu'en bas
            dr.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            # Compter les commentaires ("balises article")
            current_count = len(get_all_comments(dr))
            # Vérifier si le nombre a changé
            if current_count == previous_count:
                no_change_count += 1
                if no_change_count >= 3:
                    break
            else:
                no_change_count = 0
            previous_count = current_count
            attempt += 1

        return previous_count

    except WebDriverException as e:
        print(f"Erreur lors du scroll: {e}")
        return previous_count

def scrap_comments(driver, art_id, art_comments_url):
    load_page(driver, art_comments_url)
    accept_cookies(driver)
    load_all_articles(driver)
    process_comments(driver, art_id)
    driver.quit()

#if __name__ == '__main__':
    #scrap_comments("103433427", "https://www.20min.ch/fr/comment/103433427")