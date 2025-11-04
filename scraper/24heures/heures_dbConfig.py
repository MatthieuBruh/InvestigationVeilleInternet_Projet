import sqlite3

# Cache de connexion global
_connection_cache = None


def get_connection():
    """Retourne une connexion SQLite réutilisable et optimisée"""
    global _connection_cache
    if _connection_cache is None:
        try:
            _connection_cache = sqlite3.connect('articles_24heures.db')
            cursor = _connection_cache.cursor()

            # ✅ Optimisations critiques SQLite
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = -64000")  # 64MB de cache
            cursor.execute("PRAGMA temp_store = MEMORY")
            cursor.execute("PRAGMA mmap_size = 30000000000")
            cursor.execute("PRAGMA foreign_keys = ON")  # IMPORTANT pour les FK

            print("✓ Connexion SQLite établie et optimisée")

        except sqlite3.Error as e:
            print(f"❌ Erreur de connexion à SQLite : {e}")
            exit(1)

    return _connection_cache


def close_connection():
    """Ferme la connexion cachée"""
    global _connection_cache
    if _connection_cache is not None:
        _connection_cache.close()
        _connection_cache = None
        print("✓ Connexion SQLite fermée")


def reset_connection():
    """Force la réinitialisation de la connexion"""
    close_connection()
    return get_connection()