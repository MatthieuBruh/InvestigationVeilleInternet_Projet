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
        # Récupérer tous les commentaires de l'article
        query = """
                SELECT *
                FROM UNIL_Commentaire
                WHERE com_art_id = ?
                ORDER BY com_id \
                """
        self.cursor.execute(query, (art_id,))
        all_comments = [dict(row) for row in self.cursor.fetchall()]

        # Organiser en structure hiérarchique
        comments_dict = {c['com_id']: c for c in all_comments}

        # Ajouter une liste d'enfants à chaque commentaire
        for comment in all_comments:
            comment['children'] = []

        # Construire la hiérarchie
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

        # Utiliser textwrap pour couper le texte proprement
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
        # Si c'est une réponse (level > 0), afficher d'abord le commentaire parent
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

    def annotate_comment_tree(self, comment, level=0, parent_comment=None):
        """
        Annote un commentaire et ses réponses de manière récursive

        Args:
            comment: Commentaire à annoter
            level: Niveau de profondeur dans l'arbre
            parent_comment: Commentaire parent (pour afficher le contexte des réponses)

        Returns:
            bool: True pour continuer, False pour quitter
        """
        # Afficher le commentaire
        self.display_comment(comment, level, parent_comment)

        # Demander l'annotation
        annotation = self.get_user_annotation()

        if annotation == -1:
            return False  # Quitter
        elif annotation == 0:
            print("⏭️  Commentaire passé")
        else:
            print(f"✓ Annoté comme niveau {annotation}")
            # TODO: Sauvegarder l'annotation dans une base de données ou un fichier

        # Annoter les réponses (enfants) en passant le commentaire actuel comme parent
        for child in comment.get('children', []):
            if not self.annotate_comment_tree(child, level + 1, comment):
                return False

        return True

    def select_user(self):
        """
        Demande à l'utilisateur de s'identifier parmi les 4 personnes

        Returns:
            int: Numéro de l'utilisateur (1-4)
        """
        print("\n" + "=" * 80)
        print(" SÉLECTION DE L'UTILISATEUR ".center(80, "="))
        print("=" * 80)
        print("\nVeuillez vous identifier pour éviter les conflits d'annotation:\n")
        print("  1 - Augustin")
        print("  2 - Luca")
        print("  3 - Matthieu")
        print("  4 - Severin")

        while True:
            response = input("\n>>> Qui êtes-vous? (1-4): ").strip()

            if response in ['1', '2', '3', '4']:
                user_num = int(response)
                user_name = f"Pers{user_num}"
                print(f"\n✓ Connecté en tant que: {user_name}")
                return user_num
            else:
                print("❌ Entrée invalide. Veuillez choisir 1, 2, 3 ou 4.")

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

        # Diviser en 4 groupes
        base_count = total // 4
        remainder = total % 4

        # Calculer combien d'articles cet utilisateur doit avoir
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

        # Afficher la distribution pour tous les utilisateurs
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
                print(f"{marker}Pers{i}: {count} articles (#{s_idx + 1} à #{e_idx})")
            else:
                print(f"{marker}Pers{i}: {count} articles (aucun)")

        print(f"\n✓ Vous (Pers{user_num}): {len(user_articles)} articles assignés")

        if user_articles:
            print(f"   Premier article ID: {user_articles[0]['art_id']}")
            print(f"   Dernier article ID: {user_articles[-1]['art_id']}")
        else:
            print(f"   ⚠️  Aucun article à annoter pour vous.")

        return user_articles

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

            # Récupérer tous les articles
            all_articles = self.get_articles_with_comments()

            if not all_articles:
                print("\n❌ Aucun article avec commentaires trouvé.")
                return

            # Distribuer les articles
            articles = self.distribute_articles(all_articles, user_num)

            print(f"\n📊 Nombre d'articles à annoter: {len(articles)}")

            if not articles:
                print("❌ Aucun article assigné à annoter.")
                return

            # Parcourir chaque article assigné
            for idx, article in enumerate(articles, 1):
                print("\n" + "=" * 80)
                print(f"VOTRE ARTICLE {idx}/{len(articles)}")
                print("=" * 80)
                print(f"📰 Titre: {article['art_titre']}")
                print(f"🔗 URL: {article['art_url']}")
                print(f"📅 Date: {article['art_date']}")
                print(f"📂 Catégorie: {article['art_categorie']}")

                if article['art_description']:
                    print(f"📝 Description: {article['art_description'][:200]}...")

                # Récupérer les commentaires
                comments = self.get_comments_for_article(article['art_id'])
                print(f"\n💬 Nombre de commentaires principaux: {len(comments)}")

                input("\n▶️  Appuyez sur Entrée pour commencer l'annotation de cet article...")

                # Annoter chaque commentaire et ses réponses
                should_continue = True
                for comment in comments:
                    if not self.annotate_comment_tree(comment):
                        should_continue = False
                        break

                if not should_continue:
                    print("\n👋 Annotation interrompue par l'utilisateur.")
                    break

                print(f"\n✅ Article {idx} terminé!")

            print("\n" + "=" * 80)
            print(" ANNOTATION TERMINÉE ".center(80, "="))
            print("=" * 80)

        except KeyboardInterrupt:
            print("\n\n⚠️  Interruption par l'utilisateur (Ctrl+C)")
        finally:
            self.conn.close()
            print("\n🔒 Connexion à la base de données fermée.")


def main():
    """Point d'entrée principal"""
    db_path = "articles_20min.db"

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