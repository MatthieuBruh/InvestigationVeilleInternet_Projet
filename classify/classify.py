#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application d'annotation de commentaires pour l'analyse du discours de haine
Base de données: articles_20min.db
"""

import sqlite3
import sys
from pathlib import Path
import textwrap


class CommentAnnotator:
    """Classe pour gérer l'annotation des commentaires"""

    # Mapping des utilisateurs vers leurs colonnes dans la BDD
    USER_COLUMNS = {
        1: "com_verif_haine_augustin",
        2: "com_verif_haine_luca",
        3: "com_verif_haine_matthieu",
        4: "com_verif_haine_severin"
    }

    USER_NAMES = {
        1: "Augustin",
        2: "Luca",
        3: "Matthieu",
        4: "Severin"
    }

    # Mapping pour la vérification croisée
    CROSS_CHECK_PAIRS = {
        1: 2,  # Augustin vérifie Luca
        2: 1,  # Luca vérifie Augustin
        3: 4,  # Matthieu vérifie Severin
        4: 3  # Severin vérifie Matthieu
    }

    SCALE_LEGEND = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                    ÉCHELLE DE DISCOURS DE HAINE                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ 1 - DISAGREEMENT (Vert)                                                  ║
║     Désaccord au niveau des idées/croyances                               ║
║     Ex: False, incorrect, wrong, challenge, persuade, change minds        ║
║                                                                           ║
║ 2 - NEGATIVE ACTIONS (Jaune clair)                                       ║
║     Actions négatives non-violentes associées au groupe                   ║
║     Ex: Threatened, stole, outrageous act, poor treatment, alienate       ║
║                                                                           ║
║ 3 - NEGATIVE CHARACTER (Jaune)                                           ║
║     Caractérisations et insultes non-violentes                            ║
║     Ex: Stupid, thief, aggressor, fake, crazy                             ║
║                                                                           ║
║ 4 - DEMONIZING AND DEHUMANIZING (Orange)                                 ║
║     Caractéristiques sous-humaines et surhumaines                         ║
║     Ex: Rat, monkey, Nazi, demon, cancer, monster                         ║
║                                                                           ║
║ 5 - VIOLENCE (Rouge)                                                     ║
║     Infliction de mal physique ou métaphorique                            ║
║     Ex: Punched, raped, starved, torturing, mugging                       ║
║                                                                           ║
║ 6 - DEATH (Noir)                                                         ║
║     Élimination littérale du groupe                                       ║
║     Ex: Killed, annihilate, destroy                                       ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, db_path):
        """
        Initialise l'annotateur avec le chemin de la base de données

        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def save_annotation(self, com_id, user_id, score):
        """
        Sauvegarde une annotation dans la colonne appropriée du commentaire

        Args:
            com_id: ID du commentaire
            user_id: ID de l'utilisateur (1-4)
            score: Score de 1 à 6
        """
        column = self.USER_COLUMNS[user_id]

        try:
            query = f"""
                UPDATE UNIL_Commentaire 
                SET {column} = ?
                WHERE com_id = ?
            """
            self.cursor.execute(query, (score, com_id))
            self.conn.commit()
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde: {e}")

    def get_annotation(self, com_id, user_id):
        """
        Récupère l'annotation d'un utilisateur pour un commentaire

        Args:
            com_id: ID du commentaire
            user_id: ID de l'utilisateur

        Returns:
            Score de l'annotation ou None
        """
        column = self.USER_COLUMNS[user_id]

        query = f"""
            SELECT {column}
            FROM UNIL_Commentaire
            WHERE com_id = ?
        """
        self.cursor.execute(query, (com_id,))
        result = self.cursor.fetchone()

        if result and result[0] is not None:
            return result[0]
        return None

    def get_articles_with_comments(self):
        """
        Récupère tous les articles qui ont des commentaires actifs, triés par ID

        Returns:
            Liste de dictionnaires contenant les informations des articles
        """
        query = """
                SELECT DISTINCT a.*
                FROM UNIL_Article a
                         INNER JOIN UNIL_Commentaire c ON a.art_id = c.com_art_id
                WHERE a.art_commentaires_actifs = 1
                ORDER BY a.art_id ASC \
                """
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]

    def get_comments_for_article(self, art_id):
        """
        Récupère tous les commentaires pour un article donné, organisés hiérarchiquement

        Args:
            art_id: ID de l'article

        Returns:
            Liste de commentaires (parents seulement)
        """
        query = """
                SELECT *
                FROM UNIL_Commentaire
                WHERE com_art_id = ?
                ORDER BY com_id \
                """
        self.cursor.execute(query, (art_id,))
        all_comments = [dict(row) for row in self.cursor.fetchall()]

        comments_dict = {c['com_id']: c for c in all_comments}

        for comment in all_comments:
            comment['children'] = []

        root_comments = []
        for comment in all_comments:
            parent_id = comment['com_commentaire_parent']
            if parent_id and parent_id in comments_dict:
                comments_dict[parent_id]['children'].append(comment)
            else:
                root_comments.append(comment)

        return root_comments

    def wrap_text(self, text, width=70, indent=""):
        """
        Formate un texte sur plusieurs lignes avec retour automatique

        Args:
            text: Texte à formater
            width: Largeur maximale par ligne
            indent: Indentation à appliquer à chaque ligne

        Returns:
            Texte formaté sur plusieurs lignes
        """
        if not text:
            return indent + "(vide)"

        wrapper = textwrap.TextWrapper(
            width=width,
            initial_indent=indent,
            subsequent_indent=indent,
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapper.fill(text)

    def display_comment(self, comment, level=0, parent_comment=None):
        """
        Affiche un commentaire avec indentation selon le niveau

        Args:
            comment: Dictionnaire contenant les informations du commentaire
            level: Niveau d'indentation (0 pour commentaire parent)
            parent_comment: Commentaire parent (si c'est une réponse)
        """
        if level > 0 and parent_comment:
            print(f"\n{'─' * 80}")
            print("📝 COMMENTAIRE PARENT (pour contexte):")
            print(f"{'─' * 80}")
            print(f"   ID: {parent_comment['com_id']}")
            print(f"   Auteur: {parent_comment['com_auteur']}")
            print("   Contenu:")
            print(self.wrap_text(parent_comment['com_contenu'], width=75, indent="      "))
            print(f"{'─' * 80}")

        indent = "  " * level
        prefix = "↳ RÉPONSE" if level > 0 else "● COMMENTAIRE"

        print(f"\n{indent}{prefix}")
        print(f"{indent}{'═' * 70}")
        print(f"{indent}ID: {comment['com_id']}")
        print(f"{indent}Auteur: {comment['com_auteur']}")
        print(f"{indent}Contenu:")
        print(self.wrap_text(comment['com_contenu'], width=70, indent=indent + "   "))
        print(f"{indent}{'═' * 70}")

    def get_user_annotation(self):
        """
        Demande à l'utilisateur d'annoter un commentaire

        Returns:
            int: Note de 1 à 6, ou 0 pour passer, ou -1 pour quitter
        """
        while True:
            response = input("\n>>> Évaluation (1-6, S=Passer, Q=Quitter): ").strip().upper()

            if response == 'Q':
                return -1
            elif response == 'S':
                return 0
            elif response in ['1', '2', '3', '4', '5', '6']:
                return int(response)
            else:
                print("❌ Entrée invalide. Utilisez 1-6, S ou Q.")

    def annotate_comment_tree(self, comment, user_id, level=0, parent_comment=None):
        """
        Annote un commentaire et ses réponses de manière récursive

        Args:
            comment: Commentaire à annoter
            user_id: ID de l'utilisateur
            level: Niveau de profondeur dans l'arbre
            parent_comment: Commentaire parent

        Returns:
            bool: True pour continuer, False pour quitter
        """
        # Vérifier si déjà annoté - si oui, passer automatiquement
        existing_annotation = self.get_annotation(comment['com_id'], user_id)

        if existing_annotation is not None:
            # Déjà annoté, passer aux enfants directement
            for child in comment.get('children', []):
                if not self.annotate_comment_tree(child, user_id, level + 1, comment):
                    return False
            return True

        # Afficher le commentaire
        self.display_comment(comment, level, parent_comment)

        # Demander l'annotation
        annotation = self.get_user_annotation()

        if annotation == -1:
            return False
        elif annotation == 0:
            print("⏭️  Commentaire passé")
        else:
            print(f"✓ Annoté comme niveau {annotation}")

            # Sauvegarder l'annotation
            self.save_annotation(comment['com_id'], user_id, annotation)

        # Annoter les réponses
        for child in comment.get('children', []):
            if not self.annotate_comment_tree(child, user_id, level + 1, comment):
                return False

        return True

    def select_user(self):
        """
        Demande à l'utilisateur de s'identifier

        Returns:
            int: Numéro de l'utilisateur (1-4)
        """
        print("\n" + "=" * 80)
        print(" SÉLECTION DE L'UTILISATEUR ".center(80, "="))
        print("=" * 80)
        print("\nVeuillez vous identifier:\n")
        for num, name in self.USER_NAMES.items():
            print(f"  {num} - {name}")

        while True:
            response = input("\n>>> Qui êtes-vous? (1-4): ").strip()

            if response in ['1', '2', '3', '4']:
                user_num = int(response)
                print(f"\n✓ Connecté en tant que: {self.USER_NAMES[user_num]}")
                return user_num
            else:
                print("❌ Entrée invalide. Veuillez choisir 1, 2, 3 ou 4.")

    def select_mode(self, user_num):
        """
        Demande le mode: annotation de ses articles ou vérification croisée

        Returns:
            tuple: (mode, target_user_id) où mode='own' ou 'verify'
        """
        target_user_id = self.CROSS_CHECK_PAIRS[user_num]
        target_name = self.USER_NAMES[target_user_id]

        print("\n" + "=" * 80)
        print(" SÉLECTION DU MODE ".center(80, "="))
        print("=" * 80)
        print("\nQue souhaitez-vous faire?\n")
        print("  1 - Annoter mes articles assignés")
        print(f"  2 - Vérification croisée (annoter les articles de {target_name})")

        while True:
            response = input("\n>>> Votre choix (1-2): ").strip()

            if response == '1':
                print("\n✓ Mode: Annotation de mes articles")
                return 'own', user_num
            elif response == '2':
                print(f"\n✓ Mode: Vérification croisée des articles de {target_name}")
                print(f"💡 Vous annotez dans VOTRE colonne ({self.USER_COLUMNS[user_num]})")
                return 'verify', target_user_id
            else:
                print("❌ Entrée invalide. Veuillez choisir 1 ou 2.")

    def distribute_articles(self, articles, user_num):
        """
        Distribue les articles entre 4 utilisateurs de manière équitable

        Args:
            articles: Liste de tous les articles (triés par ID)
            user_num: Numéro de l'utilisateur (1-4)

        Returns:
            Liste des articles assignés à cet utilisateur
        """
        total = len(articles)
        base_count = total // 4
        remainder = total % 4

        if user_num <= remainder:
            user_article_count = base_count + 1
            start_idx = (user_num - 1) * (base_count + 1)
        else:
            user_article_count = base_count
            start_idx = remainder * (base_count + 1) + (user_num - remainder - 1) * base_count

        end_idx = start_idx + user_article_count
        user_articles = articles[start_idx:end_idx]

        print("\n" + "=" * 80)
        print(" DISTRIBUTION DES ARTICLES ".center(80, "="))
        print("=" * 80)
        print(f"\n📊 Total d'articles avec commentaires: {total}")
        print(f"📦 Articles par personne:")

        for i in range(1, 5):
            if i <= remainder:
                count = base_count + 1
                s_idx = (i - 1) * (base_count + 1)
            else:
                count = base_count
                s_idx = remainder * (base_count + 1) + (i - remainder - 1) * base_count
            e_idx = s_idx + count

            marker = "👉 " if i == user_num else "   "

            if count > 0:
                print(f"{marker}{self.USER_NAMES[i]}: {count} articles (#{s_idx + 1} à #{e_idx})")
            else:
                print(f"{marker}{self.USER_NAMES[i]}: {count} articles (aucun)")

        print(f"\n✓ Vous ({self.USER_NAMES[user_num]}): {len(user_articles)} articles assignés")

        if user_articles:
            print(f"   Premier article ID: {user_articles[0]['art_id']}")
            print(f"   Dernier article ID: {user_articles[-1]['art_id']}")
        else:
            print(f"   ⚠️  Aucun article à annoter pour vous.")

        return user_articles

    def get_annotation_stats(self, user_id, articles):
        """
        Calcule les statistiques d'annotation pour un utilisateur sur ses articles

        Args:
            user_id: ID de l'utilisateur
            articles: Liste des articles à vérifier

        Returns:
            tuple: (total_comments, annotated_comments)
        """
        column = self.USER_COLUMNS[user_id]
        total = 0
        annotated = 0

        for article in articles:
            query = f"""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN {column} IS NOT NULL THEN 1 ELSE 0 END) as annotated
                FROM UNIL_Commentaire
                WHERE com_art_id = ?
            """
            self.cursor.execute(query, (article['art_id'],))
            result = self.cursor.fetchone()
            total += result['total']
            annotated += result['annotated']

        return total, annotated

    def run(self):
        """
        Lance l'application d'annotation
        """
        try:
            print("=" * 80)
            print(" APPLICATION D'ANNOTATION DE COMMENTAIRES ".center(80, "="))
            print("=" * 80)
            print(self.SCALE_LEGEND)

            # Sélection de l'utilisateur
            user_num = self.select_user()

            # Sélection du mode
            mode, target_user_id = self.select_mode(user_num)

            # Récupérer tous les articles
            all_articles = self.get_articles_with_comments()

            if not all_articles:
                print("\n❌ Aucun article avec commentaires trouvé.")
                return

            # Distribuer les articles selon le mode
            articles = self.distribute_articles(all_articles, target_user_id)

            if not articles:
                print("❌ Aucun article assigné.")
                return

            # Afficher les statistiques
            total_comments, annotated_comments = self.get_annotation_stats(user_num, articles)
            print(f"\n📊 Progression: {annotated_comments}/{total_comments} commentaires annotés "
                  f"({100 * annotated_comments // total_comments if total_comments > 0 else 0}%)")

            # Parcourir chaque article
            for idx, article in enumerate(articles, 1):
                print("\n" + "=" * 80)
                if mode == 'verify':
                    print(f"VÉRIFICATION CROISÉE - ARTICLE {idx}/{len(articles)}")
                    print(f"(Articles de {self.USER_NAMES[target_user_id]})")
                else:
                    print(f"VOTRE ARTICLE {idx}/{len(articles)}")
                print("=" * 80)
                print(f"📰 Titre: {article['art_titre']}")
                print(f"🔗 URL: {article['art_url']}")
                print(f"📅 Date: {article['art_date']}")
                print(f"📂 Catégorie: {article['art_categorie']}")

                if article['art_description']:
                    print(f"📝 Description: {article['art_description'][:200]}...")

                comments = self.get_comments_for_article(article['art_id'])
                print(f"\n💬 Nombre de commentaires principaux: {len(comments)}")

                input("\n▶️  Appuyez sur Entrée pour commencer l'annotation de cet article...")

                should_continue = True
                for comment in comments:
                    if not self.annotate_comment_tree(comment, user_num):
                        should_continue = False
                        break

                if not should_continue:
                    print("\n👋 Annotation interrompue par l'utilisateur.")
                    break

                print(f"\n✅ Article {idx} terminé!")

            print("\n" + "=" * 80)
            print(" ANNOTATION TERMINÉE ".center(80, "="))
            print("=" * 80)

            # Statistiques finales
            total_comments, annotated_comments = self.get_annotation_stats(user_num, articles)
            print(f"\n📊 Progression finale: {annotated_comments}/{total_comments} commentaires annotés")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur (Ctrl+C)")
        finally:
            self.conn.close()
            print("\n🔒 Connexion à la base de données fermée.")


def main():
    """Point d'entrée principal"""
    db_path = "UNIL_IVI_GR4.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        annotator = CommentAnnotator(db_path)
        annotator.run()
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        print(f"\n💡 Usage: python {sys.argv[0]} [chemin_base_de_données]")
        print(f"   Par défaut: {db_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()