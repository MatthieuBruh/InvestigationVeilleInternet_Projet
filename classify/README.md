# Application d'Annotation avec Vérification Croisée
## Version avec colonnes dédiées par utilisateur

## 📋 Structure de la Base de Données

Les annotations sont sauvegardées directement dans la table `UNIL_Commentaire` avec des colonnes dédiées :

```sql
CREATE TABLE UNIL_Commentaire (
    com_id VARCHAR PRIMARY KEY,
    com_auteur VARCHAR,
    com_contenu VARCHAR,
    com_art_id VARCHAR NOT NULL,
    com_commentaire_parent VARCHAR,
    com_verif_haine_luca INT,         -- Annotations de Luca
    com_verif_haine_augustin INT,     -- Annotations d'Augustin
    com_verif_haine_matthieu INT,     -- Annotations de Matthieu
    com_verif_haine_severin INT,      -- Annotations de Severin
    FOREIGN KEY (com_art_id) REFERENCES UNIL_Article(art_id),
    FOREIGN KEY (com_commentaire_parent) REFERENCES UNIL_Commentaire(com_id)
);
```

## 🔄 Principe de Vérification Croisée

### Comment ça fonctionne

1. **Chaque personne écrit TOUJOURS dans SA PROPRE colonne**, que ce soit pour :
   - Annoter ses propres articles
   - Vérifier les articles d'une autre personne

2. **Paires de vérification croisée** :
   - Augustin ↔ Luca
   - Matthieu ↔ Severin

### Exemple concret

**Phase 1 : Annotations initiales**
- Augustin annote les articles 1-25 → écrit dans `com_verif_haine_augustin`
- Luca annote les articles 26-50 → écrit dans `com_verif_haine_luca`
- Matthieu annote les articles 51-75 → écrit dans `com_verif_haine_matthieu`
- Severin annote les articles 76-100 → écrit dans `com_verif_haine_severin`

**Phase 2 : Vérifications croisées**
- Augustin vérifie les articles 26-50 (de Luca) → écrit AUSSI dans `com_verif_haine_augustin`
- Luca vérifie les articles 1-25 (d'Augustin) → écrit AUSSI dans `com_verif_haine_luca`
- Matthieu vérifie les articles 76-100 (de Severin) → écrit AUSSI dans `com_verif_haine_matthieu`
- Severin vérifie les articles 51-75 (de Matthieu) → écrit AUSSI dans `com_verif_haine_severin`

**Résultat** : Chaque commentaire a 2 annotations indépendantes dans 2 colonnes différentes.

## 🎯 Utilisation

### Lancer l'application

```bash
python classify_new.py
```

Ou avec un chemin personnalisé :
```bash
python classify_new.py /chemin/vers/articles_20min.db
```

### Workflow

1. **Identification**
   ```
   Qui êtes-vous? (1-4):
   1 - Augustin
   2 - Luca
   3 - Matthieu
   4 - Severin
   ```

2. **Choix du mode**
   ```
   Que souhaitez-vous faire?
   1 - Annoter mes articles assignés
   2 - Vérification croisée (annoter les articles de [Partenaire])
   ```

3. **Annotation**
   - Seuls les commentaires non encore annotés s'affichent
   - Les commentaires déjà annotés sont automatiquement passés
   - Gain de temps : vous ne voyez que ce qu'il reste à faire !

### Commandes

- **1-6** : Annoter avec un score de l'échelle
- **S** : Passer le commentaire (ne sera pas annoté)
- **Q** : Quitter l'application
- **Ctrl+C** : Interruption d'urgence

## 🚀 Comportement Intelligent

### Passage automatique des commentaires déjà annotés

L'application **passe automatiquement** les commentaires que vous avez déjà annotés :
- ✅ En Mode 1 : passe les commentaires que vous avez déjà annotés
- ✅ En Mode 2 : passe les commentaires que vous avez déjà vérifiés
- ✅ Permet de reprendre facilement là où vous vous êtes arrêté
- ✅ Évite les doublons et fait gagner du temps

## 📊 Analyse des Données

### Voir toutes les annotations

```sql
SELECT 
    com_id,
    com_contenu,
    com_verif_haine_augustin,
    com_verif_haine_luca,
    com_verif_haine_matthieu,
    com_verif_haine_severin
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
   OR com_verif_haine_luca IS NOT NULL
   OR com_verif_haine_matthieu IS NOT NULL
   OR com_verif_haine_severin IS NOT NULL;
```

### Trouver les désaccords (Paire Augustin-Luca)

```sql
SELECT 
    c.com_id,
    c.com_contenu,
    c.com_verif_haine_augustin AS augustin,
    c.com_verif_haine_luca AS luca,
    ABS(c.com_verif_haine_augustin - c.com_verif_haine_luca) AS difference
FROM UNIL_Commentaire c
INNER JOIN UNIL_Article a ON c.com_art_id = a.art_id
WHERE c.com_verif_haine_augustin IS NOT NULL
  AND c.com_verif_haine_luca IS NOT NULL
  AND c.com_verif_haine_augustin != c.com_verif_haine_luca
ORDER BY difference DESC;
```

### Trouver les désaccords (Paire Matthieu-Severin)

```sql
SELECT 
    c.com_id,
    c.com_contenu,
    c.com_verif_haine_matthieu AS matthieu,
    c.com_verif_haine_severin AS severin,
    ABS(c.com_verif_haine_matthieu - c.com_verif_haine_severin) AS difference
FROM UNIL_Commentaire c
INNER JOIN UNIL_Article a ON c.com_art_id = a.art_id
WHERE c.com_verif_haine_matthieu IS NOT NULL
  AND c.com_verif_haine_severin IS NOT NULL
  AND c.com_verif_haine_matthieu != c.com_verif_haine_severin
ORDER BY difference DESC;
```

### Taux d'accord (Augustin-Luca)

```sql
SELECT 
    COUNT(*) AS total_double_annotations,
    SUM(CASE WHEN com_verif_haine_augustin = com_verif_haine_luca THEN 1 ELSE 0 END) AS accords,
    ROUND(100.0 * SUM(CASE WHEN com_verif_haine_augustin = com_verif_haine_luca THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_accord
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
  AND com_verif_haine_luca IS NOT NULL;
```

### Progression par personne

```sql
SELECT 
    'Augustin' AS personne,
    COUNT(*) AS commentaires_annotes
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
UNION ALL
SELECT 
    'Luca',
    COUNT(*)
FROM UNIL_Commentaire
WHERE com_verif_haine_luca IS NOT NULL
UNION ALL
SELECT 
    'Matthieu',
    COUNT(*)
FROM UNIL_Commentaire
WHERE com_verif_haine_matthieu IS NOT NULL
UNION ALL
SELECT 
    'Severin',
    COUNT(*)
FROM UNIL_Commentaire
WHERE com_verif_haine_severin IS NOT NULL;
```

### Distribution des scores par personne

```sql
SELECT 
    'Augustin' AS personne,
    com_verif_haine_augustin AS score,
    COUNT(*) AS count
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
GROUP BY com_verif_haine_augustin
UNION ALL
SELECT 
    'Luca',
    com_verif_haine_luca,
    COUNT(*)
FROM UNIL_Commentaire
WHERE com_verif_haine_luca IS NOT NULL
GROUP BY com_verif_haine_luca
ORDER BY personne, score;
```

## ✅ Avantages de ce Système

1. **Simple** : Chaque personne écrit toujours dans sa propre colonne
2. **Indépendant** : Les annotateurs ne voient pas les scores des autres
3. **Flexible** : On peut modifier ses annotations à tout moment
4. **Traçable** : On sait qui a annoté quoi
5. **Analysable** : Facile de calculer les accords et désaccords

## 💡 Conseils

- ✅ Complétez d'abord TOUTES vos annotations initiales (Mode 1)
- ✅ Puis faites la vérification croisée (Mode 2)
- ✅ Ne consultez pas les annotations de votre partenaire avant de finir
- ✅ En cas de doute, choisissez le score qui vous semble le plus approprié
- ✅ Vous pouvez quitter et reprendre : l'application reprend automatiquement où vous étiez
- ✅ Utilisez S uniquement si vous voulez vraiment passer un commentaire (il restera non annoté)

## 🔧 Fonctionnalités

- ✅ **Sauvegarde automatique** après chaque annotation
- ✅ **Passage automatique** : les commentaires déjà annotés sont automatiquement passés
- ✅ **Statistiques de progression** : affichage du nombre de commentaires annotés
- ✅ **Affichage du contexte** : les réponses montrent le commentaire parent
- ✅ **Retour à la ligne automatique** : texte formaté sur plusieurs lignes
- ✅ **Reprise facile** : relancez l'application, elle reprend où vous vous êtes arrêté