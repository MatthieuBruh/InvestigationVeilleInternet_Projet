# Interface Graphique d'Annotation de Commentaires

## 🖥️ Description

Interface graphique intuitive pour annoter des commentaires selon l'échelle de discours de haine (1-6). Alternative à la version console pour une expérience plus visuelle et conviviale.

## ✨ Fonctionnalités

- ✅ **Interface graphique moderne** avec tkinter
- ✅ **Navigation visuelle** : boutons clairs pour chaque niveau
- ✅ **Affichage optimisé** : zone de texte scrollable pour les longs commentaires
- ✅ **Couleurs distinctives** : chaque niveau a sa couleur (vert → noir)
- ✅ **Passage automatique** : les commentaires déjà annotés sont ignorés
- ✅ **Progression en temps réel** : affichage du nombre de commentaires restants
- ✅ **Contexte des réponses** : le commentaire parent s'affiche automatiquement

## 🚀 Lancement

### Prérequis

1. Python 3.6+ avec tkinter (inclus par défaut dans la plupart des installations Python)
2. Votre fichier de base de données personnel dans le dossier actuel :
   - `UNIL_IVI_GR4_augustin.db` pour Augustin
   - `UNIL_IVI_GR4_luca.db` pour Luca
   - `UNIL_IVI_GR4_matthieu.db` pour Matthieu
   - `UNIL_IVI_GR4_severin.db` pour Severin

### Commande

```bash
python classify_gui.py
```

**Important** : L'application sélectionne automatiquement le bon fichier de base de données selon l'utilisateur choisi. Chaque personne travaille sur son propre fichier, ce qui évite les conflits !

## 📁 Organisation des Fichiers

### Structure recommandée

```
mon_dossier/
├── classify_gui.py
├── UNIL_IVI_GR4_augustin.db
├── UNIL_IVI_GR4_luca.db
├── UNIL_IVI_GR4_matthieu.db
└── UNIL_IVI_GR4_severin.db
```

### Sélection automatique

Quand vous sélectionnez votre nom, l'application :
1. ✅ Ouvre automatiquement VOTRE fichier de base de données
2. ✅ Affiche un message de confirmation
3. ✅ Vérifie que le fichier existe
4. ✅ Vous empêche de modifier les fichiers des autres

### Fusion finale

Une fois que tout le monde a terminé, les fichiers individuels seront fusionnés avec un script Python dédié (déjà préparé).

## 📱 Interface

### 1. Sélection de l'utilisateur
Écran d'accueil avec 4 boutons :
```
┌─────────────────────────────────┐
│  Qui êtes-vous ?               │
│                                 │
│  [1 - Augustin]                │
│  [2 - Luca]                    │
│  [3 - Matthieu]                │
│  [4 - Severin]                 │
└─────────────────────────────────┘
```

### 2. Sélection du mode
Choix entre annotation initiale ou vérification croisée :
```
┌─────────────────────────────────────────┐
│  Connecté en tant que: Augustin        │
│  Que souhaitez-vous faire ?            │
│                                         │
│  [Annoter mes articles assignés]       │
│  [Vérification croisée (Luca)]         │
└─────────────────────────────────────────┘
```

### 3. Interface d'annotation principale

```
┌────────────────────────────────────────────────────────────┐
│ VOS ARTICLES - Article 5/25                                │
│ 📰 Titre de l'article                                      │
│ 📂 Politique | 📅 2024-01-15                              │
│ 💬 Commentaire 3/12 de cet article                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ● COMMENTAIRE À ANNOTER                                  │
│  ════════════════════════════════════════                 │
│  ID: com_12345                                            │
│  Auteur: Jean Dupont                                      │
│  Contenu:                                                 │
│  Je ne suis pas d'accord avec cette politique...         │
│  ════════════════════════════════════════                 │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Niveau de discours de haine:                             │
│                                                            │
│  [1]         [2]          [3]         [4]        [5]  [6] │
│  Disagree    Negative     Negative    Demonizing Violence │
│              Actions      Character                   Death│
│  (Vert)      (Jaune clair)(Jaune)     (Orange)   (Rouge)(Noir)│
│                                                            │
├────────────────────────────────────────────────────────────┤
│  [⏭️ Passer]                              [❌ Quitter]    │
└────────────────────────────────────────────────────────────┘
```

## 🎨 Codes Couleur

L'interface utilise des couleurs pour faciliter l'identification rapide :

| Niveau | Catégorie | Couleur |
|--------|-----------|---------|
| **1** | Disagreement | 🟢 Vert clair |
| **2** | Negative Actions | 🟡 Jaune très clair |
| **3** | Negative Character | 🟡 Jaune or |
| **4** | Demonizing | 🟠 Orange |
| **5** | Violence | 🔴 Rouge tomate |
| **6** | Death | ⚫ Noir |

## 🎯 Utilisation

### Annoter un commentaire

1. **Lisez** le commentaire affiché
2. **Cliquez** sur le bouton correspondant au niveau (1-6)
3. Le commentaire suivant s'affiche automatiquement

### Passer un commentaire

Cliquez sur **⏭️ Passer** si vous ne voulez pas annoter ce commentaire (il restera non annoté)

### Navigation

- L'application charge automatiquement le prochain article quand tous les commentaires d'un article sont annotés
- Les commentaires déjà annotés sont automatiquement ignorés
- Vous pouvez quitter et reprendre : l'application reprend où vous étiez

## 💡 Avantages de la version GUI

### Par rapport à la version console :

✅ **Plus rapide** : cliquer sur un bouton vs taper un chiffre
✅ **Plus visuel** : les couleurs aident à mémoriser l'échelle
✅ **Moins d'erreurs** : impossible de taper un mauvais caractère
✅ **Meilleur contexte** : zone de texte plus grande et scrollable
✅ **Progression claire** : affichage permanent de la progression

### Fichiers de base de données séparés :

✅ **Pas de conflits** : chaque personne a son propre fichier
✅ **Travail en parallèle** : tout le monde peut annoter en même temps
✅ **Sécurité** : impossible d'écraser le travail des autres
✅ **Simplicité** : pas besoin de coordination pour les sessions
✅ **Fusion facile** : un script dédié combine tous les fichiers à la fin

### Fonctionnalités identiques :

✅ Passage automatique des commentaires déjà annotés
✅ Affichage du commentaire parent pour les réponses
✅ Sauvegarde automatique dans la base de données
✅ Support des deux modes (annotation + vérification)
✅ Distribution équitable des articles entre les 4 personnes

## 🔧 Raccourcis Clavier

L'interface GUI supporte également le clavier pour une annotation encore plus rapide :

- **1-6** : Annoter avec le niveau correspondant
- **S** : Passer le commentaire
- **Q** : Quitter (avec confirmation)

## ⚠️ Notes Techniques

### Sur Windows
L'interface devrait fonctionner directement si Python est installé.

### Sur macOS
Tkinter est inclus avec Python. Si vous avez un problème :
```bash
brew install python-tk
```

### Sur Linux
Si tkinter n'est pas installé :
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

## 🆚 Quelle Version Choisir ?

### Version Console (`classify_new.py`)
👍 Parfait si vous :
- Préférez le terminal
- Travaillez sur un serveur distant (SSH)
- Voulez une interface minimaliste

### Version GUI (`classify_gui.py`)
👍 Parfait si vous :
- Préférez les interfaces graphiques
- Voulez annoter plus rapidement
- Appréciez les repères visuels (couleurs)
- Travaillez sur votre ordinateur local

**Les deux versions sauvegardent dans la même base de données et sont totalement compatibles !**

Vous pouvez alterner entre les deux versions sans problème.

## 🐛 Résolution de Problèmes

### "Base de données non trouvée"
- Vérifiez que votre fichier de BDD est dans le même dossier que `classify_gui.py`
- Le nom doit être exactement : `UNIL_IVI_GR4_[votre_prenom].db` (en minuscules)
- Exemples corrects :
  - ✅ `UNIL_IVI_GR4_luca.db`
  - ❌ `UNIL_IVI_GR4_Luca.db` (L majuscule incorrect)
  - ❌ `luca.db` (nom incomplet)

### L'interface ne se lance pas
- Vérifiez que tkinter est installé : `python -c "import tkinter"`
- Essayez la version console en attendant

### Les couleurs ne s'affichent pas correctement
- Normal selon le système d'exploitation
- Les niveaux restent identifiables par leur numéro et texte

### L'application freeze
- Appuyez sur Ctrl+C dans le terminal
- Relancez l'application
- Vos annotations sont sauvegardées automatiquement