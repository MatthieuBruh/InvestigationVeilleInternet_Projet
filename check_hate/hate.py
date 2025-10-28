import sqlite3
from detoxify import Detoxify
from datetime import datetime


def analyze_database(db_path='comments_20min.db'):
    """Analyse tous les commentaires de la base de données"""

    print("\n" + "=" * 80)
    print("🗄️  ANALYSE DE LA BASE DE DONNÉES")
    print("=" * 80)
    print(f"📁 Base de données : {db_path}")
    print(f"⏰ Démarrage       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")

    # Connexion à la base de données
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Récupérer tous les commentaires
        cursor.execute("SELECT rowid, contenu FROM comments WHERE contenu IS NOT NULL AND contenu != ''")
        comments = cursor.fetchall()

        total = len(comments)
        print(f"📊 Total de commentaires trouvés : {total}\n")

        if total == 0:
            print("⚠️ Aucun commentaire à analyser.")
            return

        # Charger le modèle
        print("🔄 Chargement du modèle multilingue...")
        model = Detoxify('multilingual')
        print("✅ Modèle chargé avec succès!\n")

        # Statistiques globales
        stats = {
            'total': total,
            'toxique_eleve': 0,
            'toxique_modere': 0,
            'acceptable': 0,
            'menaces': 0,
            'insultes': 0,
            'attaques_identitaires': 0
        }

        # Analyser chaque commentaire
        for i, (rowid, contenu) in enumerate(comments, 1):
            print(f"\n{'#' * 80}")
            print(f"# COMMENTAIRE {i}/{total} (ID: {rowid})")
            print(f"{'#' * 80}")

            print_category_analysis(contenu, model, stats)

            # Pause tous les 5 commentaires (optionnel)
            if i < total and i % 5 == 0:
                response = input(
                    f"\n⏸️  {i}/{total} analysés. Continuer? (Entrée = oui, 'q' = arrêter, 's' = rapport) : ")
                if response.lower() == 'q':
                    print("\n⏹️  Analyse interrompue par l'utilisateur.")
                    break
                elif response.lower() == 's':
                    print_final_report(stats, i)
                    response2 = input("\nContinuer l'analyse? (Entrée = oui, 'q' = arrêter) : ")
                    if response2.lower() == 'q':
                        break

        # Rapport final
        print("\n" + "=" * 80)
        print_final_report(stats, i if 'i' in locals() else total)

        conn.close()

    except sqlite3.Error as e:
        print(f"❌ Erreur de base de données : {e}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def print_category_analysis(text, model, stats=None):
    """Analyse détaillée d'un texte"""

    print(f"\n📝 Texte analysé :")
    # Afficher seulement les 200 premiers caractères si trop long
    display_text = text##[:200] + "..." if len(text) > 200 else text
    print(f"   └─ \"{display_text}\"")
    print("\n" + "-" * 80 + "\n")

    # Prédiction
    results = model.predict(text)

    # Définition des catégories
    categories = {
        'toxicity': {
            'emoji': '☠️',
            'nom': 'TOXICITÉ GÉNÉRALE',
            'description': 'Score global de toxicité',
        },
        'severe_toxicity': {
            'emoji': '💀',
            'nom': 'TOXICITÉ SÉVÈRE',
            'description': 'Contenu très agressif',
        },
        'obscene': {
            'emoji': '🤬',
            'nom': 'OBSCÉNITÉ',
            'description': 'Langage vulgaire/grossier',
        },
        'threat': {
            'emoji': '⚔️',
            'nom': 'MENACE',
            'description': 'Intention de nuire',
        },
        'insult': {
            'emoji': '😠',
            'nom': 'INSULTE',
            'description': 'Attaque personnelle',
        },
        'identity_attack': {
            'emoji': '👥',
            'nom': 'ATTAQUE IDENTITAIRE',
            'description': 'Discrimination',
        }
    }

    # Afficher chaque catégorie (version compacte)
    for key, info in categories.items():
        score = results[key]

        # Barre de progression
        bar_length = 40
        filled = int(bar_length * score)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Niveau
        if score >= 0.75:
            niveau = "🔴"
        elif score >= 0.50:
            niveau = "🟠"
        elif score >= 0.25:
            niveau = "🟡"
        else:
            niveau = "🟢"

        print(f"   {info['emoji']} {info['nom']:25} {score:5.1%} {niveau} [{bar}]")

    print("\n" + "-" * 80)

    # Résumé
    toxicity_score = results['toxicity']

    if toxicity_score >= 0.75:
        verdict = "🚨 HAUTEMENT TOXIQUE"
        if stats: stats['toxique_eleve'] += 1
    elif toxicity_score >= 0.50:
        verdict = "⚠️ MODÉRÉMENT TOXIQUE"
        if stats: stats['toxique_modere'] += 1
    else:
        verdict = "✅ ACCEPTABLE"
        if stats: stats['acceptable'] += 1

    print(f"\n   🏁 Verdict : {verdict} (Toxicité globale: {toxicity_score:.1%})")

    # Alertes
    alerts = []
    if results['threat'] > 0.5:
        alerts.append("⚔️ MENACE")
        if stats: stats['menaces'] += 1
    if results['insult'] > 0.7:
        alerts.append("😠 INSULTE")
        if stats: stats['insultes'] += 1
    if results['identity_attack'] > 0.6:
        alerts.append("👥 DISCRIMINATION")
        if stats: stats['attaques_identitaires'] += 1

    if alerts:
        print(f"   🔔 Alertes : {' | '.join(alerts)}")


def print_final_report(stats, analyzed):
    """Affiche le rapport final des statistiques"""

    print("\n" + "=" * 80)
    print("📈 RAPPORT FINAL D'ANALYSE")
    print("=" * 80)

    print(f"\n📊 Commentaires analysés : {analyzed}/{stats['total']}")
    print(f"   ⏰ Terminé le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n🎯 DISTRIBUTION PAR NIVEAU DE TOXICITÉ")
    print("-" * 80)

    if analyzed > 0:
        print(
            f"   🚨 Hautement toxique    : {stats['toxique_eleve']:4d} ({stats['toxique_eleve'] / analyzed * 100:5.1f}%)")
        print(
            f"   ⚠️  Modérément toxique  : {stats['toxique_modere']:4d} ({stats['toxique_modere'] / analyzed * 100:5.1f}%)")
        print(f"   ✅ Acceptable           : {stats['acceptable']:4d} ({stats['acceptable'] / analyzed * 100:5.1f}%)")

        print("\n🔔 ALERTES SPÉCIFIQUES")
        print("-" * 80)
        print(f"   ⚔️  Menaces détectées         : {stats['menaces']:4d}")
        print(f"   😠 Insultes détectées         : {stats['insultes']:4d}")
        print(f"   👥 Attaques identitaires      : {stats['attaques_identitaires']:4d}")

        print("\n💡 RECOMMANDATIONS")
        print("-" * 80)

        toxic_total = stats['toxique_eleve'] + stats['toxique_modere']
        toxic_percent = toxic_total / analyzed * 100

        if toxic_percent > 30:
            print("   🚨 CRITIQUE : Plus de 30% de contenu toxique détecté")
            print("   → Modération urgente recommandée")
        elif toxic_percent > 15:
            print("   ⚠️ ATTENTION : Niveau de toxicité modéré")
            print("   → Surveillance renforcée suggérée")
        else:
            print("   ✅ BON : Niveau de toxicité acceptable")
            print("   → Maintenir la surveillance habituelle")

        if stats['menaces'] > 0:
            print(f"\n   ⚠️ {stats['menaces']} menace(s) détectée(s) - Examen manuel recommandé")

        if stats['attaques_identitaires'] > 0:
            print(f"   ⚠️ {stats['attaques_identitaires']} attaque(s) identitaire(s) - Possibles implications légales")

    print("\n" + "=" * 80 + "\n")


# Version simple : analyse tout d'un coup
def quick_analysis(db_path='comments_20min.db', limit=None):
    """Analyse rapide sans pause, avec option de limite"""

    print(f"\n🚀 ANALYSE RAPIDE - Base: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT rowid, contenu FROM comments WHERE contenu IS NOT NULL AND contenu != ''"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    comments = cursor.fetchall()

    print(f"📊 Analyse de {len(comments)} commentaires...\n")

    model = Detoxify('multilingual')

    stats = {
        'total': len(comments),
        'toxique_eleve': 0,
        'toxique_modere': 0,
        'acceptable': 0,
        'menaces': 0,
        'insultes': 0,
        'attaques_identitaires': 0
    }

    for i, (rowid, contenu) in enumerate(comments, 1):
        print(f"⏳ Progression: {i}/{len(comments)}", end='\r')

        results = model.predict(contenu)

        # Mise à jour des stats
        if results['toxicity'] >= 0.75:
            stats['toxique_eleve'] += 1
        elif results['toxicity'] >= 0.50:
            stats['toxique_modere'] += 1
        else:
            stats['acceptable'] += 1

        if results['threat'] > 0.5:
            stats['menaces'] += 1
        if results['insult'] > 0.7:
            stats['insultes'] += 1
        if results['identity_attack'] > 0.6:
            stats['attaques_identitaires'] += 1

    print("\n")
    print_final_report(stats, len(comments))

    conn.close()


# Utilisation
if __name__ == "__main__":

    print("\n🔍 ANALYSEUR DE COMMENTAIRES - Détection de toxicité")
    print("\nChoisissez le mode d'analyse :")
    print("1. Analyse détaillée (affiche chaque commentaire)")
    print("2. Analyse rapide (statistiques uniquement)")
    print("3. Test rapide (10 premiers commentaires)")

    choix = input("\nVotre choix (1/2/3) : ")

    if choix == "1":
        analyze_database('comments_20min.db')
    elif choix == "2":
        quick_analysis('comments_20min.db')
    elif choix == "3":
        quick_analysis('comments_20min.db', limit=10)
    else:
        print("❌ Choix invalide")