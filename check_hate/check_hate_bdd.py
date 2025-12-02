import sqlite3
from detoxify import Detoxify
from tqdm import tqdm

# Configuration
DB_PATH = "votre_base_de_donnees.db"  # Remplacez par le chemin de votre BDD

# Seuil de toxicité pour la classification binaire
TOXICITY_THRESHOLD = 0.5  # Score >= 0.5 = haine (1), sinon non haine (0)


def add_columns_if_not_exist(cursor):
    """Ajoute les colonnes Detoxify si elles n'existent pas"""

    columns = [
        ('com_detox_is_haine', 'REAL'),  # Score 0-1 (identique à toxicity)
        ('com_detox_toxicity', 'REAL'),  # Score 0-1
        ('com_detox_severe_toxicity', 'REAL'),  # Score 0-1
        ('com_detox_obscene', 'REAL'),  # Score 0-1
        ('com_detox_threat', 'REAL'),  # Score 0-1
        ('com_detox_insult', 'REAL'),  # Score 0-1
        ('com_detox_identity_attack', 'REAL')  # Score 0-1
    ]

    added = []
    already_exist = []

    for col_name, col_type in columns:
        try:
            cursor.execute(f"""
                ALTER TABLE UNIL_Commentaire 
                ADD COLUMN {col_name} {col_type}
            """)
            added.append(col_name)
        except sqlite3.OperationalError:
            already_exist.append(col_name)

    if added:
        print(f"✅ Colonnes créées: {', '.join(added)}")
    if already_exist:
        print(f"ℹ️  Colonnes existantes: {', '.join(already_exist)}")
    print()


def analyze_comment(model, text):
    """
    Analyse un commentaire avec Detoxify

    Returns:
        dict avec tous les scores ou None si erreur
    """
    if not text or not text.strip():
        return None

    try:
        results = model.predict(text)

        # Extraire tous les scores
        scores = {
            'toxicity': float(results['toxicity']),
            'severe_toxicity': float(results['severe_toxicity']),
            'obscene': float(results['obscene']),
            'threat': float(results['threat']),
            'insult': float(results['insult']),
            'identity_attack': float(results['identity_attack'])
        }

        # com_detox_is_haine = même valeur que toxicity (pas de conversion binaire)
        scores['is_haine'] = scores['toxicity']

        return scores

    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse: {e}")
        return None


def process_comments(db_path, batch_size=100):
    """
    Traite tous les commentaires non encore analysés de la base de données

    Args:
        db_path: Chemin vers la base de données SQLite
        batch_size: Nombre de commentaires à traiter avant de commit
    """

    print("🔧 Initialisation du modèle Detoxify multilingue...")
    model = Detoxify('multilingual')
    print("✅ Modèle chargé\n")

    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ajouter les colonnes si nécessaire
    add_columns_if_not_exist(cursor)
    conn.commit()

    # Compter le nombre total de commentaires à traiter
    # On considère qu'un commentaire est "non analysé" si com_detox_is_haine est NULL
    cursor.execute("""
                   SELECT COUNT(*)
                   FROM UNIL_Commentaire
                   WHERE com_detox_is_haine IS NULL
                     AND com_contenu IS NOT NULL
                     AND com_contenu != ''
                   """)
    total_comments = cursor.fetchone()[0]

    print(f"{'=' * 70}")
    print(f"📊 Statistiques de traitement")
    print(f"{'=' * 70}")
    print(f"Commentaires à analyser: {total_comments}")
    print(f"Seuil de toxicité: {TOXICITY_THRESHOLD}")
    print(f"Taille des batchs: {batch_size}")
    print(f"{'=' * 70}\n")

    if total_comments == 0:
        print("✅ Tous les commentaires ont déjà été analysés !")
        print("ℹ️  Aucun nouveau commentaire à traiter.\n")
        conn.close()
        return

    # Récupérer les commentaires non analysés
    cursor.execute("""
                   SELECT com_id, com_contenu
                   FROM UNIL_Commentaire
                   WHERE com_detox_is_haine IS NULL
                     AND com_contenu IS NOT NULL
                     AND com_contenu != ''
                   """)

    comments = cursor.fetchall()

    # Compteurs
    processed = 0
    errors = 0
    total_toxicity = 0.0

    # Traiter avec une barre de progression
    print("🚀 Démarrage de l'analyse...\n")

    with tqdm(total=total_comments, desc="Progression", unit="comment") as pbar:
        for i, (com_id, com_contenu) in enumerate(comments):

            # Analyser le commentaire
            scores = analyze_comment(model, com_contenu)

            if scores is not None:
                # Mettre à jour la base de données avec tous les scores
                cursor.execute("""
                               UPDATE UNIL_Commentaire
                               SET com_detox_is_haine        = ?,
                                   com_detox_toxicity        = ?,
                                   com_detox_severe_toxicity = ?,
                                   com_detox_obscene         = ?,
                                   com_detox_threat          = ?,
                                   com_detox_insult          = ?,
                                   com_detox_identity_attack = ?
                               WHERE com_id = ?
                               """, (
                                   scores['is_haine'],
                                   scores['toxicity'],
                                   scores['severe_toxicity'],
                                   scores['obscene'],
                                   scores['threat'],
                                   scores['insult'],
                                   scores['identity_attack'],
                                   com_id
                               ))

                processed += 1
                total_toxicity += scores['toxicity']
            else:
                errors += 1

            # Commit par batch pour optimiser les performances
            if (i + 1) % batch_size == 0:
                conn.commit()
                avg_tox = total_toxicity / processed if processed > 0 else 0
                pbar.set_postfix({
                    'Moy. toxicité': f'{avg_tox:.3f}',
                    'Erreurs': errors
                })

            pbar.update(1)

    # Commit final
    conn.commit()
    conn.close()

    # Résumé final
    avg_toxicity = total_toxicity / processed if processed > 0 else 0

    print(f"\n{'=' * 70}")
    print(f"✅ TRAITEMENT TERMINÉ")
    print(f"{'=' * 70}")
    print(f"📊 Résultats:")
    print(f"   • Commentaires traités: {processed}")
    print(f"   • Score toxicité moyen: {avg_toxicity:.3f}")
    print(f"   • ❌ Erreurs: {errors}")
    print(f"{'=' * 70}\n")


def analyze_global_statistics(db_path):
    """
    Affiche des statistiques globales sur tous les commentaires analysés
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Statistiques générales
    cursor.execute("""
                   SELECT COUNT(*)                                                   as total,
                          SUM(CASE WHEN com_detox_is_haine >= 0.5 THEN 1 ELSE 0 END) as toxic,
                          AVG(com_detox_is_haine)                                    as avg_is_haine,
                          AVG(com_detox_toxicity)                                    as avg_toxicity,
                          AVG(com_detox_severe_toxicity)                             as avg_severe_toxicity,
                          AVG(com_detox_obscene)                                     as avg_obscene,
                          AVG(com_detox_threat)                                      as avg_threat,
                          AVG(com_detox_insult)                                      as avg_insult,
                          AVG(com_detox_identity_attack)                             as avg_identity_attack
                   FROM UNIL_Commentaire
                   WHERE com_detox_is_haine IS NOT NULL
                   """)

    result = cursor.fetchone()

    if result[0] == 0:
        print("❌ Aucune donnée analysée à afficher.")
        conn.close()
        return

    total, toxic, avg_haine, avg_tox, avg_sev, avg_obs, avg_thr, avg_ins, avg_ide = result
    non_toxic = total - toxic

    print(f"\n{'=' * 70}")
    print(f"📊 STATISTIQUES GLOBALES")
    print(f"{'=' * 70}")
    print(f"Total de commentaires analysés: {total:,}")
    print(f"\n🎯 Classification (seuil >= 0.5):")
    print(f"   🔴 Toxiques: {toxic:,} ({toxic / total * 100:.1f}%)")
    print(f"   🟢 Non toxiques: {non_toxic:,} ({non_toxic / total * 100:.1f}%)")

    print(f"\n📈 Scores moyens (0.000 à 1.000):")
    categories = [
        ('is_haine (= toxicité)', avg_haine, '☠️'),
        ('Toxicité générale', avg_tox, '☠️'),
        ('Toxicité sévère', avg_sev, '💀'),
        ('Obscénité', avg_obs, '🤬'),
        ('Menace', avg_thr, '⚔️'),
        ('Insulte', avg_ins, '😠'),
        ('Attaque identitaire', avg_ide, '👥')
    ]

    for name, score, emoji in categories:
        bar_length = 30
        filled = int(bar_length * score) if score else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   {emoji} {name:25s}: {score:.3f} [{bar}]")

    print(f"{'=' * 70}\n")

    conn.close()


def find_most_toxic_comments(db_path, limit=5):
    """
    Affiche les commentaires les plus toxiques
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
                   SELECT com_id,
                          com_contenu,
                          com_detox_is_haine,
                          com_detox_severe_toxicity,
                          com_detox_threat,
                          com_detox_insult,
                          com_detox_identity_attack
                   FROM UNIL_Commentaire
                   WHERE com_detox_is_haine IS NOT NULL
                   ORDER BY com_detox_is_haine DESC LIMIT ?
                   """, (limit,))

    results = cursor.fetchall()

    if not results:
        print("ℹ️  Aucun commentaire trouvé.")
        conn.close()
        return

    print(f"\n{'=' * 80}")
    print(f"🔴 TOP {limit} COMMENTAIRES LES PLUS TOXIQUES")
    print(f"{'=' * 80}\n")

    for i, (com_id, contenu, haine, sev, thr, ins, ide) in enumerate(results, 1):
        print(f"🔴 #{i} - ID: {com_id}")
        print(f"   Score is_haine: {haine:.3f}")
        print(f"   Détails: Sévère={sev:.3f} | Menace={thr:.3f} | Insulte={ins:.3f} | Identité={ide:.3f}")
        print(f"   Contenu: {contenu[:150]}{'...' if len(contenu) > 150 else ''}")
        print()

    conn.close()


def analyze_by_category(db_path):
    """
    Analyse les commentaires par catégorie de toxicité
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Compter les commentaires avec scores élevés (>= 0.5) dans chaque catégorie
    cursor.execute("""
                   SELECT SUM(CASE WHEN com_detox_toxicity >= 0.5 THEN 1 ELSE 0 END)        as high_toxicity,
                          SUM(CASE WHEN com_detox_severe_toxicity >= 0.5 THEN 1 ELSE 0 END) as high_severe,
                          SUM(CASE WHEN com_detox_obscene >= 0.5 THEN 1 ELSE 0 END)         as high_obscene,
                          SUM(CASE WHEN com_detox_threat >= 0.5 THEN 1 ELSE 0 END)          as high_threat,
                          SUM(CASE WHEN com_detox_insult >= 0.5 THEN 1 ELSE 0 END)          as high_insult,
                          SUM(CASE WHEN com_detox_identity_attack >= 0.5 THEN 1 ELSE 0 END) as high_identity,
                          COUNT(*)                                                          as total
                   FROM UNIL_Commentaire
                   WHERE com_detox_is_haine IS NOT NULL
                   """)

    result = cursor.fetchone()

    if result[-1] == 0:
        conn.close()
        return

    h_tox, h_sev, h_obs, h_thr, h_ins, h_ide, total = result

    print(f"\n{'=' * 70}")
    print(f"📊 RÉPARTITION PAR CATÉGORIE (score >= 0.5)")
    print(f"{'=' * 70}")

    categories = [
        ('☠️  Toxicité générale', h_tox),
        ('💀 Toxicité sévère', h_sev),
        ('🤬 Obscénité', h_obs),
        ('⚔️  Menace', h_thr),
        ('😠 Insulte', h_ins),
        ('👥 Attaque identitaire', h_ide)
    ]

    for name, count in categories:
        percentage = (count / total * 100) if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * count / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"{name:25s}: {count:5,} ({percentage:5.1f}%) [{bar}]")

    print(f"{'=' * 70}\n")

    conn.close()


def view_sample_comments(db_path, toxic=True, limit=3):
    """
    Affiche des exemples de commentaires toxiques ou non toxiques
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    operator = ">=" if toxic else "<"
    label = "TOXIQUES (score >= 0.5)" if toxic else "NON TOXIQUES (score < 0.5)"
    emoji = "🔴" if toxic else "🟢"

    cursor.execute(f"""
        SELECT 
            com_id, 
            com_contenu,
            com_detox_is_haine,
            com_detox_insult,
            com_detox_threat
        FROM UNIL_Commentaire 
        WHERE com_detox_is_haine IS NOT NULL
        AND com_detox_is_haine {operator} 0.5
        LIMIT ?
    """, (limit,))

    results = cursor.fetchall()

    if not results:
        conn.close()
        return

    print(f"\n{'=' * 80}")
    print(f"{emoji} EXEMPLES DE COMMENTAIRES {label}")
    print(f"{'=' * 80}\n")

    for i, (com_id, contenu, haine, ins, thr) in enumerate(results, 1):
        print(f"{emoji} Exemple {i} - ID: {com_id}")
        print(f"   is_haine: {haine:.3f} | Insulte: {ins:.3f} | Menace: {thr:.3f}")
        print(f"   Contenu: {contenu[:200]}{'...' if len(contenu) > 200 else ''}")
        print()

    conn.close()


if __name__ == "__main__":
    import sys

    # Remplacez par le chemin réel de votre base de données
    db_path = "UNIL_IVI_GR4_LLM.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"\n{'#' * 70}")
    print(f"# 🚀 ANALYSE DE TOXICITÉ DES COMMENTAIRES - DETOXIFY")
    print(f"{'#' * 70}")
    print(f"📁 Base de données: {db_path}\n")

    try:
        # 1. Traiter tous les commentaires non analysés
        # process_comments(db_path)

        # 2. Afficher les statistiques globales
        analyze_global_statistics(db_path)

        # 3. Répartition par catégorie
        analyze_by_category(db_path)

        # 4. Top commentaires toxiques
        find_most_toxic_comments(db_path, limit=5)

        # 5. Exemples de commentaires
        view_sample_comments(db_path, toxic=True, limit=3)
        view_sample_comments(db_path, toxic=False, limit=3)

        print(f"\n{'=' * 70}")
        print(f"✅ Analyse terminée avec succès!")
        print(f"{'=' * 70}\n")

    except Exception as e:
        print(f"\n❌ ERREUR: {e}\n")
        import traceback

        traceback.print_exc()