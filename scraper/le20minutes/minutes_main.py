from minutes_article import flush_article_batch
from minutes_category import scrap_categories
from minutes_comments import flush_comment_batch
from scraper.dbConfig import close_connection

URLS = {
    "monde": "https://www.20min.ch/fr/monde",
    "suisse": "https://www.20min.ch/fr/suisse"
}

def start_scraping():
    try:
        # Lancer le scraping
        scrap_categories(URLS)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption utilisateur détectée")
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()
    finally:
        # ✅ CRITIQUE : Flush tous les batchs restants
        print("\n💾 Sauvegarde des données restantes...")
        flush_article_batch()
        flush_comment_batch()
        # Fermer proprement la connexion
        close_connection()
        print("\n✅ Programme terminé proprement")