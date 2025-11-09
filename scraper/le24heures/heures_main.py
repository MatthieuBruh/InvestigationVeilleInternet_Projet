from heures_article import flush_article_batch
from heures_category import scrap_categories
from heures_comments import flush_comment_batch
from scraper.dbConfig import close_connection

URLS = {
    "monde": "https://www.24heures.ch/monde",
    "suisse": "https://www.24heures.ch/suisse"
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