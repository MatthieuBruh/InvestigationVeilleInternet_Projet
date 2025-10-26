-- Table UNIL_Article
CREATE TABLE IF NOT EXISTS UNIL_Article (
  art_id VARCHAR PRIMARY KEY,
  art_titre VARCHAR,
  art_url VARCHAR,
  art_categorie VARCHAR,
  art_date VARCHAR,
  art_description VARCHAR,
  art_commentaires_actifs INTEGER,
  art_nom_journal VARCHAR
);

-- Table UNIL_Commentaire
CREATE TABLE IF NOT EXISTS UNIL_Commentaire (
    com_id VARCHAR PRIMARY KEY,
    com_auteur VARCHAR,
    com_contenu VARCHAR,
    com_art_id VARCHAR NOT NULL,
    com_commentaire_parent VARCHAR,
    FOREIGN KEY (com_art_id) REFERENCES UNIL_Article(art_id),
    FOREIGN KEY (com_commentaire_parent) REFERENCES UNIL_Commentaire(com_id)
);