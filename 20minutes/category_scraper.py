from queue import Queue
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from articles_scraper import scrap_article, flush_article_batch
from comments_scraper import flush_comment_batch
from utils import get_driver_requirements, accept_cookies, save_cookies

# Configuration des URLs
URLS = {
    "monde": "https://www.20min.ch/fr/monde",
    "suisse": "https://www.20min.ch/fr/suisse",
    "sport": "https://www.20min.ch/fr/sports",
    "economie": "https://www.20min.ch/fr/economie"
}

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
        accept_cookies(driver)
        save_cookies(driver, f"session_cookies_{category}.pkl")

        # Attendre que le contenu soit chargé
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href^='/fr/story/']"))
        )

        # Extraire TOUS les liens d'articles
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='/fr/story/']")
        print(f"→ {len(elements)} articles trouvés dans {category}")

        seen_urls = set()
        for elem in elements:
            try:
                title = elem.text.strip()
                href = elem.get_attribute("href")

                if href and not href.startswith("http"):
                    href = "https://www.20min.ch" + href

                if title and href and len(title) > 10 and href not in seen_urls:
                    seen_urls.add(href)
                    queue_art.put({"title": title, "url": href})

            except Exception:
                continue

        print(f"→ {queue_art.qsize()} articles uniques à traiter\n")
        return queue_art

    except Exception as e:
        print(f"❌ Erreur lors du scraping de {category} : {e}")
        return None

    finally:
        try:
            driver.quit()
        except Exception:
            pass


def worker_thread(article_queue, cat):
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(options=options)
    cpt = 0
    processed = 0
    failed = 0

    while True:
        try:
            article = article_queue.get(timeout=1)

            if article is None:
                article_queue.task_done()
                break

            try:
                has_error = False
                print(
                    f"[{processed + failed + 1}/{article_queue.qsize() + processed + failed + 1}] Traitement : {article.get('url')}")
                scrap_article(driver, article.get('url'), cat)
                processed += 1

            except Exception as e:
                print(f"  ❌ Erreur : {e}")
                failed += 1
                has_error = True

            article_queue.task_done()
            cpt += 1

            # Réinitialisation périodique du driver
            if cpt % 20 == 0 or has_error:
                print(f"\n⏸️ Pause - Réinitialisation du driver (après {cpt} articles)")

                # Flush avant de fermer
                flush_article_batch()
                flush_comment_batch()

                driver.close()
                driver.quit()
                sleep(10)

                options, service = get_driver_requirements()
                driver = webdriver.Chrome(options=options)
                driver.get("https://www.20min.ch/fr")
                accept_cookies(driver)
                save_cookies(driver, f"session_cookies_{cat}.pkl")
                print("▶️ Reprise du scraping\n")

        except:
            break

    # Nettoyage final
    try:
        driver.quit()
    except:
        pass

    print(f"\n📊 Résumé {cat} :")
    print(f"  ✓ Succès : {processed}")
    print(f"  ✗ Échecs : {failed}")
    print(f"  Total : {processed + failed}")


def start_scraping():
    print("\n" + "=" * 60)
    print("🚀 DÉBUT DU SCRAPING")
    print("=" * 60)

    for category, url in URLS.items():
        if category == "monde":
            continue
        res_articles = scrape_articles_from_category(url, category)

        if res_articles and not res_articles.empty():
            worker_thread(res_articles, category)

            # ✅ CRITIQUE : Flush les batchs après chaque catégorie
            print(f"\n💾 Finalisation de la catégorie {category}...")
            flush_article_batch()
            flush_comment_batch()
            print(f"✓ Catégorie {category} terminée\n")

        else:
            print(f"⚠️ Aucun article trouvé pour {category}\n")

    print("\n" + "=" * 60)
    print("✅ SCRAPING TERMINÉ")
    print("=" * 60)