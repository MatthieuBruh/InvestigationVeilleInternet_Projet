from queue import Queue
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import (
    InvalidSessionIdException,
    WebDriverException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraper.le24heures.heures_article import scrap_article, flush_article_batch
from scraper.le24heures.heures_comments import flush_comment_batch
from scraper.dbConfig import get_connection
from scraper.utils import get_driver_requirements, save_cookies, accept_cookies_24heures


def scrape_articles_from_category(url, category):
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(options=options)
    queue_art = Queue()
    try:
        print(f"\n{'=' * 60}")
        print(f"📰 Catégorie : {category.upper()}")
        print(f"{'=' * 60}")
        print(f"Chargement de {url}")
        driver.get(url)
        accept_cookies_24heures(driver)
        save_cookies(driver, f"session_cookies_{category}.pkl")

        # Attendre que le contenu soit chargé
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Teaser_link__aPG04"))
        )

        # Extraire TOUS les liens d'articles
        elements = driver.find_elements(By.CLASS_NAME, "Teaser_link__aPG04")
        print(f"→ {len(elements)} articles trouvés dans {category}")

        seen_urls = set()
        for index, elem in enumerate(elements, 1):
            try:
                title = "Art_number" + str(index)# elem.text.strip()
                href = elem.get_attribute("href")
                if href and not href.startswith("http"):
                    href = "https://www.24heures.ch" + href
                if title and href and len(title) > 10 and href not in seen_urls:
                    seen_urls.add(href)
                    queue_art.put({"title": title, "url": href})
            except Exception:
                continue
        print(f"→ {queue_art.qsize()} articles uniques à traiter\n")
        return queue_art
    except Exception as e:
        print(f"❌ Erreur lors du scraping de {category} : {e}")
        print(e)
        return None
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def recreate_driver(cat):
    """Recrée un driver Chrome propre"""
    print(f"\n🔄 Recréation du driver Chrome...")
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(options=options)
    # ✅ Configurer les timeouts
    driver.set_page_load_timeout(90)
    driver.implicitly_wait(10)
    try:
        driver.get("https://www.24heures.ch/")
        accept_cookies_24heures(driver)
        save_cookies(driver, f"session_cookies_{cat}.pkl")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'initialisation du driver : {e}")
    print("✓ Driver recréé\n")
    return driver


def worker_thread(article_queue, cat):
    driver = recreate_driver(cat)
    cpt = 0
    processed = 0
    failed = 0
    consecutive_errors = 0  # ✅ Compteur d'erreurs consécutives
    while True:
        try:
            article = article_queue.get(timeout=1)
            if article is None:
                article_queue.task_done()
                break
            try:
                print(
                    f"[{processed + failed + 1}/{article_queue.qsize() + processed + failed + 1}] Traitement : {article.get('url')}")
                scrap_article(driver, article.get('url'), cat)
                processed += 1
                consecutive_errors = 0  # Reset le compteur en cas de succès
                # Petite pause entre articles
                sleep(2)
            except InvalidSessionIdException as e:
                # Session perdue → recréer le driver immédiatement
                print(f"  ⚠️ Session driver perdue, recréation...")
                try:
                    driver.quit()
                except:
                    pass
                driver = recreate_driver(cat)
                failed += 1
                consecutive_errors += 1
            except (TimeoutException, WebDriverException) as e:
                print(f"  ❌ Erreur driver/timeout : {e}")
                failed += 1
                consecutive_errors += 1
            except Exception as e:
                print(f"  ❌ Erreur : {e}")
                failed += 1
                consecutive_errors += 1
            article_queue.task_done()
            cpt += 1
            # ✅ Si trop d'erreurs consécutives → recréer le driver
            if consecutive_errors >= 3:
                print(f"\n⚠️ 3 erreurs consécutives détectées, recréation du driver...")
                # Flush avant de recréer
                flush_article_batch()
                flush_comment_batch()
                # Commit
                conn = get_connection()
                conn.commit()
                try:
                    driver.quit()
                except:
                    pass
                sleep(10)
                driver = recreate_driver(cat)
                consecutive_errors = 0
            # ✅ Checkpoint tous les 10 articles
            if cpt % 10 == 0:
                print(f"\n💾 Checkpoint - Sauvegarde (après {cpt} articles)")
                flush_article_batch()
                flush_comment_batch()
                conn = get_connection()
                conn.commit()
                print("✓ Données sauvegardées\n")
            # ✅ Réinitialisation périodique tous les 20 articles
            if cpt % 20 == 0:
                print(f"\n⏸️ Pause - Réinitialisation du driver (après {cpt} articles)")
                # Flush avant de fermer
                flush_article_batch()
                flush_comment_batch()
                conn = get_connection()
                conn.commit()
                try:
                    driver.close()
                    driver.quit()
                except:
                    pass
                sleep(15)  # Pause plus longue
                driver = recreate_driver(cat)
                print("▶️ Reprise du scraping\n")
        except Exception as e:
            print(f"❌ Erreur fatale dans worker_thread : {e}")
            break
    # ✅ Nettoyage final
    print("\n💾 Sauvegarde finale...")
    flush_article_batch()
    flush_comment_batch()
    try:
        conn = get_connection()
        conn.commit()
    except:
        pass
    try:
        driver.quit()
    except:
        pass
    print(f"\n📊 Résumé {cat} :")
    print(f"  ✓ Succès : {processed}")
    print(f"  ✗ Échecs : {failed}")
    print(f"  Total : {processed + failed}")

def scrap_categories(URLS):
    print("\n" + "=" * 60)
    print("🚀 DÉBUT DU SCRAPING")
    print("=" * 60)
    for category, url in URLS.items():
        res_articles = scrape_articles_from_category(url, category)
        if res_articles and not res_articles.empty():
            worker_thread(res_articles, category)
            # ✅ Flush final après chaque catégorie
            print(f"\n💾 Finalisation de la catégorie {category}...")
            flush_article_batch()
            flush_comment_batch()
            try:
                conn = get_connection()
                conn.commit()
                print(f"✓ Catégorie {category} sauvegardée\n")
            except Exception as e:
                print(f"⚠️ Erreur commit : {e}")
        else:
            print(f"⚠️ Aucun article trouvé pour {category}\n")
    print("\n" + "=" * 60)
    print("✅ SCRAPING TERMINÉ")
    print("=" * 60)