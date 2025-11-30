#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application de révision des désaccords d'annotation
Revue finale des commentaires où les annotateurs ne sont pas d'accord
"""

import sqlite3
import tkinter as tk
from tkinter import messagebox, scrolledtext
from pathlib import Path
import random


class DisagreementReviewGUI:
    """Interface graphique pour la révision des désaccords"""

    # Colonne unique pour toutes les révisions finales
    FINAL_COLUMN = 'com_haine_final'

    SCALE_INFO = {
        0: ("No hate", "Pas de haine dans ce message", "#FFFFFF"),
        1: ("Disagreement", "Désaccord au niveau des idées/croyances", "#90EE90"),
        2: ("Negative Actions", "Actions négatives non-violentes", "#FFFFE0"),
        3: ("Negative Character", "Caractérisations et insultes non-violentes", "#FFD700"),
        4: ("Demonizing", "Caractéristiques sous/surhumaines", "#FFA500"),
        5: ("Violence", "Infliction de mal physique", "#FF6347"),
        6: ("Death", "Élimination littérale du groupe", "#000000")
    }

    def __init__(self, db_path):
        """Initialise l'application de révision"""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de données non trouvée: {db_path}")

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Ajouter la colonne de révision finale si elle n'existe pas
        self.ensure_final_column()

        self.disagreements = []
        self.current_idx = 0

        self.root = tk.Tk()
        self.root.title("Révision des Désaccords - Annotation Finale")
        self.root.geometry("1000x800")

        # Charger tous les désaccords
        self.load_all_disagreements()

    def ensure_final_column(self):
        """Ajoute la colonne finale si elle n'existe pas"""
        try:
            self.cursor.execute(f"""
                ALTER TABLE UNIL_Commentaire 
                ADD COLUMN {self.FINAL_COLUMN} INT
            """)
            self.conn.commit()
            print(f"✓ Colonne {self.FINAL_COLUMN} ajoutée")
        except sqlite3.OperationalError:
            # La colonne existe déjà
            pass

    def load_all_disagreements(self):
        """Charge tous les désaccords des deux paires et les mélange"""
        all_disagreements = []

        # Paire 1: Augustin & Luca
        disagreements_pair1 = self.get_disagreements_for_pair(
            'com_verif_haine_augustin',
            'com_verif_haine_luca'
        )
        all_disagreements.extend(disagreements_pair1)

        # Paire 2: Matthieu & Severin
        disagreements_pair2 = self.get_disagreements_for_pair(
            'com_verif_haine_matthieu',
            'com_verif_haine_severin'
        )
        all_disagreements.extend(disagreements_pair2)

        if not all_disagreements:
            messagebox.showinfo("Info",
                                "Aucun désaccord trouvé.\n"
                                "Tous les commentaires ont la même annotation !")
            self.root.quit()
            return

        # Mélanger aléatoirement les désaccords
        random.shuffle(all_disagreements)
        self.disagreements = all_disagreements

        # Afficher l'interface
        self.show_review_interface()

    def get_disagreements_for_pair(self, col1, col2):
        """
        Récupère tous les commentaires où les deux annotateurs ne sont pas d'accord

        Args:
            col1: Première colonne d'annotation
            col2: Deuxième colonne d'annotation

        Returns:
            Liste de dictionnaires avec commentaire, article et annotations
        """
        query = f"""
        SELECT 
            c.*,
            a.art_id, a.art_titre, a.art_url, a.art_categorie, 
            a.art_date, a.art_description,
            c.{col1} as annotation1,
            c.{col2} as annotation2,
            c.{self.FINAL_COLUMN} as final_annotation
        FROM UNIL_Commentaire c
        INNER JOIN UNIL_Article a ON c.com_art_id = a.art_id
        WHERE c.{col1} IS NOT NULL 
          AND c.{col2} IS NOT NULL
          AND c.{col1} != c.{col2}
        ORDER BY a.art_id, c.com_id
        """

        self.cursor.execute(query)
        results = [dict(row) for row in self.cursor.fetchall()]

        # Ajouter le commentaire parent si nécessaire
        for result in results:
            if result['com_commentaire_parent']:
                parent_query = """
                               SELECT * \
                               FROM UNIL_Commentaire \
                               WHERE com_id = ? \
                               """
                self.cursor.execute(parent_query, (result['com_commentaire_parent'],))
                parent = self.cursor.fetchone()
                result['parent'] = dict(parent) if parent else None
            else:
                result['parent'] = None

        return results

    def save_review(self, com_id, score):
        """Sauvegarde l'annotation de révision finale"""
        try:
            query = f"""
                UPDATE UNIL_Commentaire 
                SET {self.FINAL_COLUMN} = ?
                WHERE com_id = ?
            """
            self.cursor.execute(query, (score, com_id))
            self.conn.commit()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {e}")

    def show_review_interface(self):
        """Affiche l'interface principale de révision"""
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame du haut - Info
        info_frame = tk.Frame(main_frame, relief=tk.RAISED, borderwidth=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(info_frame, text="Révision Finale des Désaccords",
                 font=("Arial", 12, "bold"), fg="darkblue").pack(padx=10, pady=5)

        self.stats_label = tk.Label(info_frame, text="", font=("Arial", 10))
        self.stats_label.pack(padx=10, pady=5)

        self.article_label = tk.Label(info_frame, text="", font=("Arial", 10, "bold"),
                                      wraplength=950, justify=tk.LEFT, anchor="w")
        self.article_label.pack(padx=10, pady=5, fill=tk.X)

        self.url_label = tk.Label(info_frame, text="", font=("Arial", 9, "underline"),
                                  fg="blue", cursor="hand2")
        self.url_label.pack(padx=10, pady=2, anchor="w")
        self.url_label.bind("<Button-1>", self.open_article_url)
        self.current_url = ""

        # Frame du milieu - Annotations existantes
        annotations_frame = tk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2, bg="#FFF8DC")
        annotations_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(annotations_frame, text="📊 ANNOTATIONS EXISTANTES (Désaccord)",
                 font=("Arial", 11, "bold"), bg="#FFF8DC").pack(padx=10, pady=5)

        self.annotations_label = tk.Label(annotations_frame, text="",
                                          font=("Arial", 10), bg="#FFF8DC")
        self.annotations_label.pack(padx=10, pady=5)

        # Frame du milieu - Commentaire
        comment_frame = tk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=2)
        comment_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.comment_text = scrolledtext.ScrolledText(comment_frame, wrap=tk.WORD,
                                                      font=("Arial", 11), height=12)
        self.comment_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.comment_text.config(state=tk.DISABLED)

        # Frame des boutons d'annotation
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(buttons_frame, text="Votre annotation finale:",
                 font=("Arial", 11, "bold")).pack(pady=5)

        # Première ligne: 0 (No hate)
        score_frame_top = tk.Frame(buttons_frame)
        score_frame_top.pack(pady=5)

        name, desc, color = self.SCALE_INFO[0]
        btn0 = tk.Button(score_frame_top, text=f"{0}\n{name}",
                         font=("Arial", 9, "bold"), width=15, height=3,
                         bg=color, fg="black",
                         command=lambda: self.annotate(0))
        btn0.pack()

        # Deuxième ligne: 1-6
        score_frame_bottom = tk.Frame(buttons_frame)
        score_frame_bottom.pack(pady=5)

        for score in range(1, 7):
            name, desc, color = self.SCALE_INFO[score]
            btn = tk.Button(score_frame_bottom, text=f"{score}\n{name}",
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

        # Charger le premier désaccord
        self.show_current_disagreement()

    def open_article_url(self, event):
        """Ouvre l'URL de l'article dans le navigateur"""
        import webbrowser
        if self.current_url:
            webbrowser.open(self.current_url)

    def show_current_disagreement(self):
        """Affiche le désaccord actuel"""
        if self.current_idx >= len(self.disagreements):
            messagebox.showinfo("Terminé",
                                "Tous les désaccords ont été révisés !\n"
                                "Merci pour votre travail.")
            self.quit_app()
            return

        item = self.disagreements[self.current_idx]

        # Statistiques
        total = len(self.disagreements)
        reviewed = sum(1 for d in self.disagreements if d['final_annotation'] is not None)
        remaining = total - reviewed

        stats_text = f"📊 Désaccord {self.current_idx + 1}/{total} | "
        stats_text += f"Révisés: {reviewed} | Restants: {remaining}"
        self.stats_label.config(text=stats_text)

        # Info article
        info_text = f"📰 {item['art_titre']}\n"
        info_text += f"📂 {item['art_categorie']} | 📅 {item['art_date']}"

        if item['art_description'] and item['art_description'].strip():
            description = item['art_description']
            if len(description) > 200:
                description = description[:200] + "..."
            info_text += f"\n📝 {description}"

        self.article_label.config(text=info_text)

        # URL
        if item['art_url']:
            self.current_url = item['art_url']
            self.url_label.config(text=f"🔗 {item['art_url']}")
        else:
            self.current_url = ""
            self.url_label.config(text="")

        # Annotations existantes
        ann1 = item['annotation1']
        ann2 = item['annotation2']

        ann_text = f"Annotateur 1: Niveau {ann1} ({self.SCALE_INFO[ann1][0]})     "
        ann_text += f"Annotateur 2: Niveau {ann2} ({self.SCALE_INFO[ann2][0]})"

        if item['final_annotation'] is not None:
            ann_text += f"\n⚠️ Déjà révisé: Niveau {item['final_annotation']}"

        self.annotations_label.config(text=ann_text)

        # Commentaire
        text = ""

        if item['parent']:
            text += "─" * 80 + "\n"
            text += "📝 COMMENTAIRE PARENT (pour contexte):\n"
            text += "─" * 80 + "\n"
            text += f"Auteur: {item['parent']['com_auteur']}\n"
            text += f"Contenu: {item['parent']['com_contenu']}\n"
            text += "─" * 80 + "\n\n"

        prefix = "↳ RÉPONSE À RÉVISER" if item['parent'] else "● COMMENTAIRE À RÉVISER"
        text += prefix + "\n"
        text += "═" * 80 + "\n"
        text += f"ID: {item['com_id']}\n"
        text += f"Auteur: {item['com_auteur']}\n"
        text += f"Contenu:\n{item['com_contenu']}\n"
        text += "═" * 80

        self.comment_text.config(state=tk.NORMAL)
        self.comment_text.delete(1.0, tk.END)
        self.comment_text.insert(1.0, text)
        self.comment_text.config(state=tk.DISABLED)

    def annotate(self, score):
        """Enregistre l'annotation de révision"""
        if self.current_idx >= len(self.disagreements):
            return

        item = self.disagreements[self.current_idx]
        self.save_review(item['com_id'], score)

        # Mettre à jour l'item dans la liste
        self.disagreements[self.current_idx]['final_annotation'] = score

        # Passer au suivant
        self.current_idx += 1
        self.show_current_disagreement()

    def skip_comment(self):
        """Passe le commentaire actuel sans l'annoter"""
        self.current_idx += 1
        self.show_current_disagreement()

    def quit_app(self):
        """Quitte l'application"""
        if messagebox.askyesno("Quitter", "Êtes-vous sûr de vouloir quitter ?"):
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
    import sys

    db_path = "UNIL_IVI_GR4_Merged.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        app = DisagreementReviewGUI(db_path)
        app.run()
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        print(f"\n💡 Usage: python review_disagreements.py [chemin_base_de_données]")
        print(f"   Par défaut: {db_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()