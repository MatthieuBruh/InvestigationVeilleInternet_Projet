#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface graphique d'annotation de commentaires
Base de données: articles_20min.db
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path


class CommentAnnotatorGUI:
    """Interface graphique pour l'annotation des commentaires"""

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

    # Fichiers de base de données par utilisateur
    USER_DB_FILES = {
        1: "UNIL_IVI_GR4_augustin.db",
        2: "UNIL_IVI_GR4_luca.db",
        3: "UNIL_IVI_GR4_matthieu.db",
        4: "UNIL_IVI_GR4_severin.db"
    }

    # Mapping pour la vérification croisée
    CROSS_CHECK_PAIRS = {
        1: 2,  # Augustin vérifie Luca
        2: 1,  # Luca vérifie Augustin
        3: 4,  # Matthieu vérifie Severin
        4: 3  # Severin vérifie Matthieu
    }

    SCALE_INFO = {
        1: ("Disagreement", "Désaccord au niveau des idées/croyances", "#90EE90"),
        2: ("Negative Actions", "Actions négatives non-violentes", "#FFFFE0"),
        3: ("Negative Character", "Caractérisations et insultes non-violentes", "#FFD700"),
        4: ("Demonizing", "Caractéristiques sous/surhumaines", "#FFA500"),
        5: ("Violence", "Infliction de mal physique", "#FF6347"),
        6: ("Death", "Élimination littérale du groupe", "#000000")
    }

    def __init__(self):
        """Initialise l'application GUI"""
        self.db_path = None
        self.conn = None
        self.cursor = None

        self.user_id = None
        self.mode = None
        self.target_user_id = None
        self.articles = []
        self.current_article_idx = 0
        self.current_comments = []
        self.current_comment_idx = 0

        self.root = tk.Tk()
        self.root.title("Annotation de Commentaires - Discours de Haine")
        self.root.geometry("900x700")

        self.show_user_selection()

    def show_user_selection(self):
        """Affiche l'écran de sélection de l'utilisateur"""
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Sélection de l'utilisateur",
                 font=("Arial", 18, "bold")).pack(pady=20)

        tk.Label(frame, text="Qui êtes-vous ?",
                 font=("Arial", 12)).pack(pady=10)

        for num, name in self.USER_NAMES.items():
            btn = tk.Button(frame, text=f"{num} - {name}",
                            font=("Arial", 12), width=20,
                            command=lambda n=num: self.select_user(n))
            btn.pack(pady=5)

    def select_user(self, user_num):
        """Sélectionne l'utilisateur et connecte à sa base de données"""
        self.user_id = user_num

        # Déterminer le fichier de base de données
        db_file = self.USER_DB_FILES[user_num]
        self.db_path = Path(db_file)

        # Vérifier que le fichier existe
        if not self.db_path.exists():
            messagebox.showerror("Erreur",
                                 f"Base de données non trouvée: {db_file}\n\n"
                                 f"Veuillez vous assurer que le fichier existe dans le dossier actuel.")
            self.root.quit()
            return

        # Connecter à la base de données
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de se connecter à la base de données: {e}")
            self.root.quit()
            return

        # Afficher un message de confirmation
        messagebox.showinfo("Connexion",
                            f"Connecté en tant que: {self.USER_NAMES[user_num]}\n"
                            f"Base de données: {db_file}")

        # Nettoyer la fenêtre
        for widget in self.root.winfo_children():
            widget.destroy()

        self.show_mode_selection()

    def show_mode_selection(self):
        """Affiche l'écran de sélection du mode"""
        frame = tk.Frame(self.root, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text=f"Connecté en tant que: {self.USER_NAMES[self.user_id]}",
                 font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(frame, text="Que souhaitez-vous faire ?",
                 font=("Arial", 12)).pack(pady=20)

        btn1 = tk.Button(frame, text="Annoter mes articles assignés",
                         font=("Arial", 12), width=30,
                         command=lambda: self.select_mode('own'))
        btn1.pack(pady=10)

        target_name = self.USER_NAMES[self.CROSS_CHECK_PAIRS[self.user_id]]
        btn2 = tk.Button(frame, text=f"Vérification croisée (articles de {target_name})",
                         font=("Arial", 12), width=30,
                         command=lambda: self.select_mode('verify'))
        btn2.pack(pady=10)

    def select_mode(self, mode):
        """Sélectionne le mode et charge les articles"""
        self.mode = mode

        if mode == 'own':
            self.target_user_id = self.user_id
        else:
            self.target_user_id = self.CROSS_CHECK_PAIRS[self.user_id]

        # Charger les articles
        all_articles = self.get_articles_with_comments()
        self.articles = self.distribute_articles(all_articles, self.target_user_id)

        if not self.articles:
            messagebox.showinfo("Info", "Aucun article assigné.")
            self.root.quit()
            return

        # Nettoyer la fenêtre
        for widget in self.root.winfo_children():
            widget.destroy()

        self.show_annotation_interface()

    def get_articles_with_comments(self):
        """Récupère tous les articles avec commentaires"""
        query = """
                SELECT DISTINCT a.*
                FROM UNIL_Article a
                         INNER JOIN UNIL_Commentaire c ON a.art_id = c.com_art_id
                WHERE a.art_commentaires_actifs = 1
                ORDER BY a.art_id ASC \
                """
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]

    def distribute_articles(self, articles, user_num):
        """Distribue les articles entre 4 utilisateurs"""
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
        return articles[start_idx:end_idx]

    def get_comments_for_article(self, art_id):
        """Récupère tous les commentaires d'un article de manière plate"""
        query = """
                SELECT *
                FROM UNIL_Commentaire
                WHERE com_art_id = ?
                ORDER BY com_id \
                """
        self.cursor.execute(query, (art_id,))
        all_comments = [dict(row) for row in self.cursor.fetchall()]

        # Filtrer pour ne garder que les commentaires non annotés
        column = self.USER_COLUMNS[self.user_id]
        unannotated = []

        for comment in all_comments:
            if comment[column] is None:
                # Ajouter le commentaire parent si c'est une réponse
                if comment['com_commentaire_parent']:
                    # Trouver le parent
                    parent = next((c for c in all_comments
                                   if c['com_id'] == comment['com_commentaire_parent']), None)
                    comment['parent'] = parent
                else:
                    comment['parent'] = None
                unannotated.append(comment)

        return unannotated

    def save_annotation(self, com_id, score):
        """Sauvegarde une annotation"""
        column = self.USER_COLUMNS[self.user_id]

        try:
            query = f"""
                UPDATE UNIL_Commentaire 
                SET {column} = ?
                WHERE com_id = ?
            """
            self.cursor.execute(query, (score, com_id))
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def show_annotation_interface(self):
        """Affiche l'interface principale d'annotation"""
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame du haut - Info article
        info_frame = tk.Frame(main_frame, relief=tk.RAISED, borderwidth=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.article_label = tk.Label(info_frame, text="", font=("Arial", 10, "bold"),
                                      wraplength=850, justify=tk.LEFT)
        self.article_label.pack(padx=10, pady=5)

        self.progress_label = tk.Label(info_frame, text="", font=("Arial", 9))
        self.progress_label.pack(padx=10, pady=5)

        # Frame du milieu - Commentaire
        comment_frame = tk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        comment_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Zone de texte pour le commentaire avec scrollbar
        self.comment_text = scrolledtext.ScrolledText(comment_frame, wrap=tk.WORD,
                                                      font=("Arial", 11), height=15)
        self.comment_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.comment_text.config(state=tk.DISABLED)

        # Frame des boutons d'annotation
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(buttons_frame, text="Niveau de discours de haine:",
                 font=("Arial", 11, "bold")).pack(pady=5)

        # Créer les boutons 1-6
        score_frame = tk.Frame(buttons_frame)
        score_frame.pack(pady=5)

        for score in range(1, 7):
            name, desc, color = self.SCALE_INFO[score]
            btn = tk.Button(score_frame, text=f"{score}\n{name}",
                            font=("Arial", 9), width=12, height=3,
                            bg=color if color != "#000000" else "#333333",
                            fg="white" if color == "#000000" else "black",
                            command=lambda s=score: self.annotate(s))
            btn.pack(side=tk.LEFT, padx=5)

        # Frame des contrôles
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X)

        tk.Button(control_frame, text="⏭️ Passer", font=("Arial", 10),
                  command=self.skip_comment).pack(side=tk.LEFT, padx=5)

        tk.Button(control_frame, text="❌ Quitter", font=("Arial", 10),
                  command=self.quit_app).pack(side=tk.RIGHT, padx=5)

        # Charger le premier article
        self.load_next_article()

    def load_next_article(self):
        """Charge le prochain article avec des commentaires non annotés"""
        while self.current_article_idx < len(self.articles):
            article = self.articles[self.current_article_idx]
            self.current_comments = self.get_comments_for_article(article['art_id'])

            if self.current_comments:
                # Il y a des commentaires non annotés
                self.current_comment_idx = 0
                self.update_article_info(article)
                self.show_current_comment()
                return
            else:
                # Pas de commentaires non annotés, passer à l'article suivant
                self.current_article_idx += 1

        # Plus d'articles
        messagebox.showinfo("Terminé", "Tous les commentaires ont été annotés !")
        self.quit_app()

    def update_article_info(self, article):
        """Met à jour les informations de l'article"""
        mode_text = "VÉRIFICATION CROISÉE" if self.mode == 'verify' else "VOS ARTICLES"
        info_text = f"{mode_text} - Article {self.current_article_idx + 1}/{len(self.articles)}\n"
        info_text += f"📰 {article['art_titre']}\n"
        info_text += f"📂 {article['art_categorie']} | 📅 {article['art_date']}"

        self.article_label.config(text=info_text)

        total_in_article = len(self.current_comments)
        progress_text = f"💬 Commentaire {self.current_comment_idx + 1}/{total_in_article} de cet article"
        self.progress_label.config(text=progress_text)

    def show_current_comment(self):
        """Affiche le commentaire actuel"""
        if self.current_comment_idx >= len(self.current_comments):
            # Plus de commentaires dans cet article
            self.current_article_idx += 1
            self.load_next_article()
            return

        comment = self.current_comments[self.current_comment_idx]

        # Construire le texte à afficher
        text = ""

        # Si c'est une réponse, afficher le parent
        if comment['parent']:
            text += "─" * 80 + "\n"
            text += "📝 COMMENTAIRE PARENT (pour contexte):\n"
            text += "─" * 80 + "\n"
            text += f"Auteur: {comment['parent']['com_auteur']}\n"
            text += f"Contenu: {comment['parent']['com_contenu']}\n"
            text += "─" * 80 + "\n\n"

        # Afficher le commentaire à annoter
        prefix = "↳ RÉPONSE À ANNOTER" if comment['parent'] else "● COMMENTAIRE À ANNOTER"
        text += prefix + "\n"
        text += "═" * 80 + "\n"
        text += f"ID: {comment['com_id']}\n"
        text += f"Auteur: {comment['com_auteur']}\n"
        text += f"Contenu:\n{comment['com_contenu']}\n"
        text += "═" * 80

        self.comment_text.config(state=tk.NORMAL)
        self.comment_text.delete(1.0, tk.END)
        self.comment_text.insert(1.0, text)
        self.comment_text.config(state=tk.DISABLED)

        # Mettre à jour le progress
        article = self.articles[self.current_article_idx]
        self.update_article_info(article)

    def annotate(self, score):
        """Annote le commentaire actuel avec le score donné"""
        if self.current_comment_idx >= len(self.current_comments):
            return

        comment = self.current_comments[self.current_comment_idx]
        self.save_annotation(comment['com_id'], score)

        # Passer au commentaire suivant
        self.current_comment_idx += 1
        self.show_current_comment()

    def skip_comment(self):
        """Passe le commentaire actuel sans l'annoter"""
        self.current_comment_idx += 1
        self.show_current_comment()

    def quit_app(self):
        """Quitte l'application"""
        if messagebox.askyesno("Quitter", "Êtes-vous sûr de vouloir quitter ?"):
            if self.conn:
                self.conn.close()
            self.root.quit()

    def run(self):
        """Lance l'interface graphique"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
            self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur inattendue: {e}")
        finally:
            if self.conn:
                self.conn.close()


def main():
    """Point d'entrée principal"""
    app = CommentAnnotatorGUI()
    app.run()


if __name__ == "__main__":
    main()