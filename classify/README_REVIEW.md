# Application de Révision des Désaccords

## 📋 Description

Application graphique pour la **troisième phase d'annotation** : résoudre les désaccords entre annotateurs. Cette application affiche uniquement les commentaires où deux annotateurs d'une même paire ont donné des scores différents.

## 🎯 Objectif

Quand Augustin et Luca (ou Matthieu et Severin) ne sont pas d'accord sur l'annotation d'un commentaire, une troisième personne révise le commentaire et donne son verdict final.

## 👥 Paires d'Annotateurs

### Paire 1 : Augustin & Luca
- Colonnes comparées : `com_verif_haine_augustin` vs `com_verif_haine_luca`
- Colonne de révision : `com_verif_haine_review_pair1`

### Paire 2 : Matthieu & Severin
- Colonnes comparées : `com_verif_haine_matthieu` vs `com_verif_haine_severin`
- Colonne de révision : `com_verif_haine_review_pair2`

## 🚀 Lancement

### Commande

```bash
python review_disagreements.py merged_database.db
```

**Note** : Utilisez la base de données **fusionnée** qui contient toutes les annotations des 4 personnes.

## 📱 Interface

### 1. Sélection de la paire

```
┌────────────────────────────────┐
│  Révision des Désaccords      │
│                                │
│  Quelle paire réviser ?       │
│                                │
│  [Paire 1: Augustin & Luca]   │
│  [Paire 2: Matthieu & Severin]│
└────────────────────────────────┘
```

### 2. Interface de révision

```
┌─────────────────────────────────────────────────────────┐
│ Révision Paire: Augustin & Luca                        │
│ 📊 Désaccord 15/47 | Révisés: 14 | Restants: 33       │
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
│                                                         │
│ ● COMMENTAIRE À RÉVISER                                │
│ ════════════════════════════════════                   │
│ Contenu du commentaire...                              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Votre annotation finale:                               │
│                                                         │
│           [0 - No hate]                                │
│                                                         │
│  [1]  [2]  [3]  [4]  [5]  [6]                         │
├─────────────────────────────────────────────────────────┤
│ [⏭️ Passer]                          [❌ Quitter]      │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Workflow

### Phase 1 : Préparation
1. Tous les annotateurs terminent leur annotation initiale
2. Tous les annotateurs terminent leur vérification croisée
3. Vous fusionnez toutes les BDD individuelles en une seule

### Phase 2 : Révision des désaccords
1. Lancez `review_disagreements.py merged_database.db`
2. Choisissez une paire à réviser
3. Pour chaque désaccord :
   - Lisez le commentaire
   - Voyez les 2 annotations existantes
   - Donnez votre annotation finale (0-6)

### Phase 3 : Résultat
- L'annotation finale est sauvegardée dans `com_verif_haine_review_pair1` ou `com_verif_haine_review_pair2`
- Ces colonnes serviront de référence finale pour l'analyse

## 📊 Informations Affichées

Pour chaque désaccord, vous voyez :

✅ **Info article** : Titre, catégorie, date, description, URL cliquable
✅ **Les 2 annotations** : Niveau et nom (ex: "Niveau 2 - Negative Actions")
✅ **Commentaire complet** : Avec commentaire parent si c'est une réponse
✅ **Statistiques** : Progression (combien de désaccords révisés/restants)

## 💾 Nouvelles Colonnes Créées

L'application ajoute automatiquement ces colonnes à la table `UNIL_Commentaire` :

```sql
ALTER TABLE UNIL_Commentaire ADD COLUMN com_verif_haine_review_pair1 INT;
ALTER TABLE UNIL_Commentaire ADD COLUMN com_verif_haine_review_pair2 INT;
```

## 📈 Statistiques Utiles

### Compter les désaccords par paire

**Paire 1** :
```sql
SELECT COUNT(*) as desaccords
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
  AND com_verif_haine_luca IS NOT NULL
  AND com_verif_haine_augustin != com_verif_haine_luca;
```

**Paire 2** :
```sql
SELECT COUNT(*) as desaccords
FROM UNIL_Commentaire
WHERE com_verif_haine_matthieu IS NOT NULL
  AND com_verif_haine_severin IS NOT NULL
  AND com_verif_haine_matthieu != com_verif_haine_severin;
```

### Voir les désaccords résolus

```sql
SELECT 
    com_id,
    com_contenu,
    com_verif_haine_augustin as augustin,
    com_verif_haine_luca as luca,
    com_verif_haine_review_pair1 as revision
FROM UNIL_Commentaire
WHERE com_verif_haine_review_pair1 IS NOT NULL;
```

### Distribution des désaccords par écart

```sql
SELECT 
    ABS(com_verif_haine_augustin - com_verif_haine_luca) as ecart,
    COUNT(*) as nombre
FROM UNIL_Commentaire
WHERE com_verif_haine_augustin IS NOT NULL
  AND com_verif_haine_luca IS NOT NULL
  AND com_verif_haine_augustin != com_verif_haine_luca
GROUP BY ecart
ORDER BY ecart;
```

## 🔧 Fonctionnalités

✅ **Détection automatique** : Trouve tous les désaccords
✅ **Pas de nom** : Les annotateurs sont anonymes (Annotateur 1 / 2)
✅ **Contexte complet** : Article, description, URL cliquable
✅ **Passage automatique** : Les désaccords déjà révisés sont comptés mais peuvent être modifiés
✅ **Sauvegarde auto** : Chaque annotation est sauvegardée immédiatement

## 💡 Conseils

- ✅ Lisez l'article complet si nécessaire (lien cliquable)
- ✅ Considérez le contexte de l'article
- ✅ Votre annotation finale peut être différente des 2 annotations existantes
- ✅ Vous pouvez quitter et reprendre : les désaccords déjà révisés sont marqués
- ✅ Utilisez "Passer" si vous voulez revenir sur un cas difficile plus tard

## ⚠️ Important

### Qui fait la révision ?

La révision des désaccords devrait idéalement être faite par :
- Une **personne neutre** (pas dans la paire)
- Ou une **discussion en groupe** pour les cas difficiles
- Ou le **chef de projet** pour une décision finale

### Ordre recommandé

1. Révisez d'abord les **petits écarts** (différence de 1 niveau)
2. Ensuite les **grands écarts** (différence de 2-3 niveaux)
3. Les **très grands écarts** (4+ niveaux) nécessitent souvent une discussion

## 🎓 Exemple d'Utilisation

```bash
# 1. Fusionner les bases de données
python merge_databases.py

# 2. Lancer la révision
python review_disagreements.py merged_database.db

# 3. Sélectionner "Paire 1: Augustin & Luca"

# 4. Réviser chaque désaccord
#    - Lisez le commentaire
#    - Voyez : Annotateur 1: Niveau 2, Annotateur 2: Niveau 3
#    - Cliquez sur votre choix (0-6)

# 5. Résultat : 47 désaccords révisés !
```

## 📁 Structure Finale

Après la révision, chaque commentaire avec désaccord aura :

| Colonne | Valeur | Signification |
|---------|--------|---------------|
| `com_verif_haine_augustin` | 2 | Annotation d'Augustin |
| `com_verif_haine_luca` | 3 | Annotation de Luca |
| `com_verif_haine_review_pair1` | 2 | **Annotation finale** (après révision) |

Cette annotation finale sera utilisée pour l'analyse et les résultats finaux du projet.
