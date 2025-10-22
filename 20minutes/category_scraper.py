import threading
import time
from queue import Queue

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from article_scraper import scrap_article
from utils import get_driver_requirements, accept_cookies

# Configuration des URLs (sans espaces à la fin !)
URLS = {
    "monde": "https://www.20min.ch/fr/monde",
    "suisse": "https://www.20min.ch/fr/suisse",
    "sport": "https://www.20min.ch/fr/sports",
    "economie": "https://www.20min.ch/fr/economie"
}

def scroll_to_load_all(driver, max_scrolls=60, scroll_increment=800, wait_time=1.5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0
    no_change_count = 0

    while scrolls < max_scrolls and no_change_count < 3:
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")
        time.sleep(wait_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            no_change_count += 1
        else:
            no_change_count = 0
        last_height = new_height
        scrolls += 1

def scrape_articles_from_category(url, category):
    options, service = get_driver_requirements()
    driver = webdriver.Chrome(service=service, options=options)

    queue_art = Queue()
    try:
        print(f"Chargement de {category} : {url}")
        driver.get(url)
        accept_cookies(driver)
        # scroll_to_load_all(driver)

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

                # Construire l'URL complète (si elle est relative)
                if href and not href.startswith("http"):
                    href = "https://www.20min.ch" + href

                if title and href and len(title) > 10 and href not in seen_urls:
                    seen_urls.add(href)
                    queue_art.put({"title": title, "url": href})
            except Exception:
                # Ignorer les éléments problématiques
                continue
        return queue_art

    except Exception as e:
        print(f"Erreur lors du scraping de {category} : {e}")
        exit(1)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def worker_thread(article_queue, cat):
    while True:
        try:
            article = article_queue.get(timeout=1)
            if article is None:
                article_queue.task_done()
                break
            try:
                scrap_article(article.get('url'), cat)
                # print("Article done: ", article.get('url'))
            except Exception:
                # print("Article error: ", article.get('url'))
                continue
            article_queue.task_done()
        except:
            break

def process_articles(article_queue, articles_category, num_workers=4):
    threads = []
    for i in range(num_workers):
        thread = threading.Thread(target=worker_thread,args=(article_queue, articles_category))
        thread.start()
        threads.append(thread)

    article_queue.join()

    # Envoyer signal de fin à tous les threads
    for _ in range(num_workers):
        article_queue.put(None)

    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()

# Exécution principale
if __name__ == "__main__":
    for category, url in URLS.items():
        res_articles = scrape_articles_from_category(url, category)
        if res_articles:
            process_articles(res_articles, category)
        else:
            print(f"Aucun article trouvé pour {category}")
    print("Scraping terminé.")