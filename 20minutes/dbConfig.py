import mariadb

def get_connection():
    try:
        conn = mariadb.connect(
            user="USERNAME",
            password="PASSWORD",
            host="IP_ADDRESS",
            port=3306,
            database="unil_scraper"
        )
        return conn
    except mariadb.Error as e:
        print(f"Erreur de connexion à MariaDB : {e}")
        exit(1)