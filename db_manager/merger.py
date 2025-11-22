import sqlite3
import os


def verify_compatibility(master_db, person_dbs):
    """
    Vérifie que les bases ont les mêmes com_id

    Returns:
        bool: True si toutes les bases sont compatibles, False sinon
    """

    conn_master = sqlite3.connect(master_db)
    cursor_master = conn_master.cursor()

    cursor_master.execute("SELECT com_id FROM UNIL_Commentaire ORDER BY com_id")
    master_ids = set(row[0] for row in cursor_master.fetchall())
    conn_master.close()

    print(f"Base master : {len(master_ids)} commentaires")

    all_compatible = True

    for person_name, person_db_path in person_dbs.items():
        if not os.path.exists(person_db_path):
            print(f"\n⚠️  {person_name}: fichier introuvable")
            all_compatible = False
            continue

        conn_person = sqlite3.connect(person_db_path)
        cursor_person = conn_person.cursor()

        cursor_person.execute("SELECT com_id FROM UNIL_Commentaire ORDER BY com_id")
        person_ids = set(row[0] for row in cursor_person.fetchall())
        conn_person.close()

        # Vérifier les différences
        only_in_master = master_ids - person_ids
        only_in_person = person_ids - master_ids

        print(f"\n{person_name}:")
        print(f"  - Commentaires : {len(person_ids)}")
        print(f"  - Manquants dans {person_name} : {len(only_in_master)}")
        print(f"  - En trop dans {person_name} : {len(only_in_person)}")

        # Marquer comme incompatible s'il y a des différences
        if only_in_master or only_in_person:
            all_compatible = False
            print(f"  ❌ INCOMPATIBLE")

            if only_in_master:
                print(f"    Exemples manquants : {list(only_in_master)[:5]}")
            if only_in_person:
                print(f"    Exemples en trop : {list(only_in_person)[:5]}")
        else:
            print(f"  ✓ Compatible")

    print(f"\n{'=' * 50}")
    if all_compatible:
        print("✓ TOUTES LES BASES SONT COMPATIBLES")
    else:
        print("❌ ATTENTION : INCOMPATIBILITÉS DÉTECTÉES")
    print(f"{'=' * 50}\n")

    return all_compatible

def merge_databases(master_db, person_dbs, output_db=None):
    """
    Fusionne plusieurs bases de données SQLite.

    Args:
        master_db: chemin vers la base principale
        person_dbs: dict {'nom_personne': 'chemin_db', ...}
        output_db: chemin de sortie (si None, écrase master_db)
    """

    if output_db is None:
        output_db = master_db
    elif output_db != master_db:
        # Copier la base master vers output
        import shutil
        shutil.copy2(master_db, output_db)

    conn_master = sqlite3.connect(output_db)
    cursor_master = conn_master.cursor()

    # Pour chaque personne
    for person_name, person_db_path in person_dbs.items():
        print(f"\n=== Fusion des données de {person_name} ===")

        if not os.path.exists(person_db_path):
            print(f"⚠️  Base {person_db_path} introuvable, ignorée")
            continue

        conn_person = sqlite3.connect(person_db_path)
        cursor_person = conn_person.cursor()

        # Obtenir la colonne correspondante (ex: com_verif_haine_luca)
        column_name = f"com_verif_haine_{person_name.lower()}"

        # Vérifier que la colonne existe
        cursor_master.execute("PRAGMA table_info(UNIL_Commentaire)")
        columns = [row[1] for row in cursor_master.fetchall()]

        if column_name not in columns:
            print(f"⚠️  Colonne {column_name} introuvable dans la base master")
            continue

        # Récupérer les données de la personne
        cursor_person.execute(f"""
            SELECT com_id, {column_name}
            FROM UNIL_Commentaire
            WHERE {column_name} IS NOT NULL
        """)

        updates = cursor_person.fetchall()
        print(f"   {len(updates)} lignes à mettre à jour")

        # Mettre à jour dans la base master
        updated_count = 0
        for com_id, value in updates:
            cursor_master.execute(f"""
                UPDATE UNIL_Commentaire
                SET {column_name} = ?
                WHERE com_id = ?
            """, (value, com_id))

            if cursor_master.rowcount > 0:
                updated_count += 1

        print(f"   ✓ {updated_count} lignes mises à jour")

        conn_person.close()

    conn_master.commit()
    conn_master.close()
    print(f"\n✓ Fusion terminée : {output_db}")


# Utilisation
if __name__ == "__main__":
    master_db = "UNIL_IVI_GR4.db"

    person_dbs = {
        'luca': 'UNIL_IVI_GR4_luca.db',
        'augustin': 'UNIL_IVI_GR4_augustin.db',
        'matthieu': 'UNIL_IVI_GR4_matthieu.db',
        'severin': 'UNIL_IVI_GR4_severin.db'
    }

    # Vérifier avant de fusionner
    if verify_compatibility(master_db, person_dbs):
        print("Lancement de la fusion...\n")
        merge_databases(master_db, person_dbs, output_db="UNIL_IVI_GR4_Merged.db")
    else:
        print("⚠️  Fusion annulée en raison d'incompatibilités")
        print("Veuillez vérifier que toutes les bases proviennent de la même source")