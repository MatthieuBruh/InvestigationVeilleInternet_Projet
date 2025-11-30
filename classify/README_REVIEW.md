# Application de Révision des Désaccords

## 📋 Description

Application graphique pour la **Phase 3** : résoudre les désaccords entre annotateurs. Tous les désaccords des **deux paires sont mélangés aléatoirement** pour une révision neutre et impartiale.

## 🎯 Objectif

Réviser tous les commentaires où deux annotateurs ne sont pas d'accord. L'application :
- ✅ Charge les désaccords d'Augustin & Luca
- ✅ Charge les désaccords de Matthieu & Severin  
- ✅ **Mélange tout aléatoirement**
- ✅ Sauvegarde dans **une seule colonne** : `com_haine_final`

## 💾 Colonne Unique

Toutes les révisions vont dans :
```sql
ALTER TABLE UNIL_Commentaire ADD COLUMN com_haine_final INT;
```

**Avantage** : Une seule colonne pour l'annotation finale, simple et claire.

## 🚀 Lancement

```bash
python review_disagreements.py merged_database.db
```

**Important** : Utilisez la base de données **fusionnée** contenant les annotations des 4 personnes.

## 📱 Interface

### Écran principal (pas de sélection de paire)

```
┌─────────────────────────────────────────────────────────┐
│ Révision Finale des Désaccords                         │
│ 📊 Désaccord 23/94 | Révisés: 22 | Restants: 72       │
├─────────────────────────────────────────────────────────┤
│ 📰 Titre de l'article                                   │
│ 📂 Catégorie | 📅 Date                                 │
│ 📝 Description...                                       │
│ 🔗 URL de l'article (cliquable)                        │
├─────────────────────────────────────────────────────────┤
│ 📊 ANNOTATIONS EXISTANTES (Désaccord)                  │
│ Annotateur 1: Niveau 2 (Negative Actions)              │
│ Annotateur 2: Niveau 3 (Negative Character)            │
├─────────────────────────────────────────────────────────┤
│ ● COMMENTAIRE À RÉVISER                                │
│ Contenu du commentaire...                              │
├─────────────────────────────────────────────────────────┤
│           [0 - No hate]                                │
│  [1]  [2]  [3]  [4]  [5]  [6]                         │
└─────────────────────────────────────────────────────────┘
```

## 🔀 Mélange Aléatoire

### Pourquoi ?

✅ **Neutralité** : Le réviseur ne sait pas de quelle paire vient le désaccord
✅ **Pas de biais** : Empêche de traiter différemment les deux groupes
✅ **Équité** : Même attention pour tous les désaccords

### Comment ?

L'application :
1. Charge tous les désaccords de la Paire 1 (Augustin & Luca)
2. Charge tous les désaccords de la Paire 2 (Matthieu & Severin)
3. Les mélange avec `random.shuffle()`
4. Les présente dans cet ordre aléatoire

## 🎯 Workflow

```
Phase 1 : Annotation initiale (4 personnes)
    ↓
Phase 2 : Vérification croisée (4 personnes)
    ↓
Fusion des 4 BDD en une seule
    ↓
Phase 3 : Révision des désaccords (1 personne)  ← CETTE APP
    ↓
Analyse finale des données
```

## 📊 Statistiques

### Compter tous les désaccords

```sql
SELECT COUNT(*) as total_desaccords
FROM (
    -- Paire 1
    SELECT com_id FROM UNIL_Commentaire
    WHERE com_verif_haine_augustin IS NOT NULL
      AND com_verif_haine_luca IS NOT NULL
      AND com_verif_haine_augustin != com_verif_haine_luca
    
    UNION
    
    -- Paire 2
    SELECT com_id FROM UNIL_Commentaire
    WHERE com_verif_haine_matthieu IS NOT NULL
      AND com_verif_haine_severin IS NOT NULL
      AND com_verif_haine_matthieu != com_verif_haine_severin
);
```

### Voir les révisions complétées

```sql
SELECT 
    com_id,
    com_contenu,
    com_haine_final as revision_finale
FROM UNIL_Commentaire
WHERE com_haine_final IS NOT NULL;
```

### Progression de la révision

```sql
SELECT 
    COUNT(*) FILTER (WHERE com_haine_final IS NOT NULL) as revises,
    COUNT(*) as total_desaccords,
    ROUND(100.0 * COUNT(*) FILTER (WHERE com_haine_final IS NOT NULL) / COUNT(*), 2) as pourcentage
FROM (
    SELECT com_id, com_haine_final FROM UNIL_Commentaire
    WHERE com_verif_haine_augustin IS NOT NULL
      AND com_verif_haine_luca IS NOT NULL
      AND com_verif_haine_augustin != com_verif_haine_luca
    
    UNION
    
    SELECT com_id, com_haine_final FROM UNIL_Commentaire
    WHERE com_verif_haine_matthieu IS NOT NULL
      AND com_verif_haine_severin IS NOT NULL
      AND com_verif_haine_matthieu != com_verif_haine_severin
);
```

## 🔧 Fonctionnalités

✅ **Mélange automatique** : Les deux paires sont mélangées
✅ **Anonymat complet** : Juste "Annotateur 1" et "Annotateur 2"
✅ **Contexte complet** : Article, URL, description
✅ **Colonne unique** : `com_haine_final` pour toutes les révisions
✅ **Statistiques en direct** : Progression visible
✅ **Reprise possible** : Les révisions déjà faites sont marquées

## 💡 Conseils pour le Réviseur

### Approche

- ✅ **Lisez l'article** si nécessaire (URL cliquable)
- ✅ **Considérez les deux annotations** comme des avis, pas des contraintes
- ✅ **Faites votre propre jugement** indépendant
- ✅ **Votre annotation peut différer** des deux existantes

### Cas typiques

**Désaccord de 1 niveau** (ex: 2 vs 3)
→ Souvent une nuance d'interprétation
→ Choisissez ce qui vous semble le plus approprié

**Désaccord de 2-3 niveaux** (ex: 1 vs 4)
→ Différence importante d'interprétation
→ Relisez attentivement le commentaire et l'article

**Désaccord majeur** (ex: 0 vs 5)
→ Cas rare, nécessite une attention particulière
→ Le contexte de l'article est souvent crucial

## 🎓 Exemple d'Utilisation

```bash
# 1. S'assurer d'avoir la BDD fusionnée
ls merged_database.db

# 2. Lancer l'application
python review_disagreements.py merged_database.db

# 3. L'application charge automatiquement
#    - 47 désaccords de la Paire 1
#    - 52 désaccords de la Paire 2
#    - Total: 99 désaccords mélangés

# 4. Pour chaque désaccord :
#    - Lisez le commentaire
#    - Voyez les 2 annotations
#    - Cliquez sur votre choix (0-6)

# 5. Résultat : 99 désaccords révisés !
#    Tous dans la colonne com_haine_final
```

## 📁 Structure Finale

Après révision, la base de données contient :

| Colonne | Exemple | Description |
|---------|---------|-------------|
| `com_verif_haine_augustin` | 2 | Annotation d'Augustin |
| `com_verif_haine_luca` | 3 | Annotation de Luca |
| `com_verif_haine_matthieu` | - | (pas annoté par lui) |
| `com_verif_haine_severin` | - | (pas annoté par lui) |
| **`com_haine_final`** | **2** | **Annotation finale après révision** |

Ou pour la Paire 2 :

| Colonne | Exemple | Description |
|---------|---------|-------------|
| `com_verif_haine_augustin` | - | (pas annoté par eux) |
| `com_verif_haine_luca` | - | (pas annoté par eux) |
| `com_verif_haine_matthieu` | 4 | Annotation de Matthieu |
| `com_verif_haine_severin` | 2 | Annotation de Severin |
| **`com_haine_final`** | **3** | **Annotation finale après révision** |

## ✅ Avantages du Système

### Par rapport à 2 colonnes séparées

✅ **Plus simple** : Une seule colonne pour les résultats finaux
✅ **Plus clair** : Pas de confusion sur quelle colonne utiliser
✅ **Plus flexible** : Facile d'ajouter d'autres analyses
✅ **Plus neutre** : Le mélange cache l'origine du désaccord

### Pour l'analyse finale

Vous aurez besoin uniquement de :
- `com_haine_final` : Pour les commentaires avec désaccords (révisés)
- Les colonnes individuelles : Pour les commentaires sans désaccords

## 🔄 Que Faire Après ?

Une fois tous les désaccords révisés :

1. **Créer la colonne finale complète** qui combine tout :
```sql
-- Pour les commentaires avec désaccords révisés
UPDATE UNIL_Commentaire 
SET com_haine_consensus = com_haine_final
WHERE com_haine_final IS NOT NULL;

-- Pour les commentaires sans désaccord (Paire 1)
UPDATE UNIL_Commentaire 
SET com_haine_consensus = com_verif_haine_augustin
WHERE com_haine_final IS NULL
  AND com_verif_haine_augustin IS NOT NULL
  AND com_verif_haine_luca IS NOT NULL
  AND com_verif_haine_augustin = com_verif_haine_luca;

-- Pour les commentaires sans désaccord (Paire 2)
UPDATE UNIL_Commentaire 
SET com_haine_consensus = com_verif_haine_matthieu
WHERE com_haine_final IS NULL
  AND com_verif_haine_matthieu IS NOT NULL
  AND com_verif_haine_severin IS NOT NULL
  AND com_verif_haine_matthieu = com_verif_haine_severin;
```

2. **Analyser les résultats** avec `com_haine_consensus` !