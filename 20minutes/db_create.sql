-- DROP DATABASE unil_scraper;

CREATE DATABASE IF NOT EXISTS unil_scraper CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE unil_scraper;

-- Table UNIL_Article
CREATE TABLE IF NOT EXISTS UNIL_Article (
  art_id VARCHAR(255) PRIMARY KEY,
  art_titre VARCHAR(255),
  art_url VARCHAR(2048),
  art_categorie VARCHAR(255),
  art_date DATETIME,
  art_description TEXT,
  art_commentaires_actifs BOOLEAN,
  art_nom_journal VARCHAR(255)
);

-- Table UNIL_Commentaire
CREATE TABLE IF NOT EXISTS UNIL_Commentaire (
    com_id INT AUTO_INCREMENT PRIMARY KEY,
    com_auteur VARCHAR(255),    
    com_contenu TEXT,
    com_art_id VARCHAR(255) NOT NULL,
    com_commentaire_parent INT,
    CONSTRAINT fk_commentaire_article 
        FOREIGN KEY (com_art_id) 
        REFERENCES UNIL_Article(art_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_commentaire_reponse 
        FOREIGN KEY (com_commentaire_parent) 
        REFERENCES UNIL_Commentaire(com_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);