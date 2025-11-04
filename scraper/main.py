from dbConfig import get_connection, close_connection
from le20minutes.minutes_main import start_scraping as start_scraping_minutes
from lematin.matin_main import start_scraping as start_scraping_matin

def init_database():
    """Initialise la base de données SQLite"""
    print("🔧 Initialisation de la base de données SQLite...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Lire et exécuter le schéma SQL
        with open('db_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
            # SQLite supporte executescript !
            cursor.executescript(sql_script)
        conn.commit()
        print("✓ Tables et index créés avec succès\n")
        # Afficher les statistiques existantes
        cursor.execute("SELECT COUNT(*) FROM UNIL_Article")
        nb_articles = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM UNIL_Commentaire")
        nb_commentaires = cursor.fetchone()[0]
        if nb_articles > 0 or nb_commentaires > 0:
            print(f"📊 Base existante :")
            print(f"  • Articles : {nb_articles}")
            print(f"  • Commentaires : {nb_commentaires}\n")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        return False

if __name__ == '__main__':
    # sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    # sys.stdout = open('logs.txt', 'w')
    # Initialiser la base de données
    if not init_database():
        print("❌ Impossible de démarrer le scraping")
        exit(1)
    try:
        # Lancer le scraping
        print("Commencement")
        start_scraping_minutes()
        start_scraping_matin()
        # TODO : AJOUTER LES SCRAPPER start_scraping()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interruption utilisateur détectée")
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()
    finally:
        # ✅ CRITIQUE : Flush tous les batchs restants
        print("\n💾 Sauvegarde des données restantes...")
        # Fermer proprement la connexion
        close_connection()
        print("\n✅ Programme terminé proprement")