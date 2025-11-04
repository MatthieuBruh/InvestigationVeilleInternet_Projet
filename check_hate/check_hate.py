# Load model directly
'''import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("Hate-speech-CNERG/new-counterspeech-score")
model = AutoModelForSequenceClassification.from_pretrained("Hate-speech-CNERG/new-counterspeech-score")

# Exemple de texte
text = "Il faut renvoyer ces sales nègres pro hamas, qu'ils aillent se faire buter chez ces singes"

inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
outputs = model(**inputs)

# Obtenir les prédictions
predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
predicted_class = torch.argmax(predictions, dim=-1).item()

# Les labels sont: 0 = NON_HATE, 1 = HATE
labels = ["NON_HATE", "HATE"]
print(f"Prédiction: {labels[predicted_class]}")
print(f"Confiance: {predictions[0][predicted_class].item():.4f}")

from transformers import pipeline


# Créer le pipeline
classifier = pipeline("text-classification",
                     model="Hate-speech-CNERG/new-counterspeech-score")

# Analyser un texte
result = classifier("J'aime al vie")
print(result)

from detoxify import Detoxify

# Utiliser le modèle multilingue
model = Detoxify('multilingual')

# Tester sur plusieurs langues
results = model.predict("Il faut être psychologiquement atteint pour aller là-bas.")

print(results)'''

from detoxify import Detoxify


def print_category_analysis(text):
    """Analyse détaillée avec explication de chaque catégorie"""

    print("\n" + "=" * 80)
    print("🔍 ANALYSE DÉTAILLÉE DU TEXTE")
    print("=" * 80)

    print(f"\n📝 Texte analysé :")
    print(f"   └─ \"{text}\"")
    print("\n" + "-" * 80 + "\n")

    # Prédiction
    model = Detoxify('multilingual')
    results = model.predict(text)

    # Définition des catégories avec emoji, nom et explication
    categories = {
        'toxicity': {
            'emoji': '☠️',
            'nom': 'TOXICITÉ GÉNÉRALE',
            'description': 'Score global de toxicité (impoli, irrespectueux, désagréable)',
            'exemples': 'Commentaires méchants, propos blessants'
        },
        'severe_toxicity': {
            'emoji': '💀',
            'nom': 'TOXICITÉ SÉVÈRE',
            'description': 'Contenu très agressif qui repousserait fortement les gens',
            'exemples': 'Haine extrême, violence verbale intense'
        },
        'obscene': {
            'emoji': '🤬',
            'nom': 'OBSCÉNITÉ',
            'description': 'Langage vulgaire, grossier ou sexuellement explicite',
            'exemples': 'Gros mots, insultes crues, contenu sexuel'
        },
        'threat': {
            'emoji': '⚔️',
            'nom': 'MENACE',
            'description': 'Intention de nuire physiquement, financièrement ou autrement',
            'exemples': '"Je vais te frapper", "Tu vas le payer"'
        },
        'insult': {
            'emoji': '😠',
            'nom': 'INSULTE',
            'description': 'Attaque personnelle, commentaire offensant ou dégradant',
            'exemples': '"Tu es stupide", "Quel idiot"'
        },
        'identity_attack': {
            'emoji': '👥',
            'nom': 'ATTAQUE IDENTITAIRE',
            'description': 'Discrimination basée sur race, religion, genre, orientation, etc.',
            'exemples': 'Racisme, sexisme, homophobie, xénophobie'
        }
    }

    # Afficher chaque catégorie
    for key, info in categories.items():
        score = results[key]

        print(f"{info['emoji']} {info['nom']}")
        print("-" * 80)

        # Barre de progression
        bar_length = 50
        filled = int(bar_length * score)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Couleur textuelle selon le score
        if score >= 0.75:
            niveau = "🔴 ÉLEVÉ"
            color_bar = f"\033[91m{bar}\033[0m"  # Rouge
        elif score >= 0.50:
            niveau = "🟠 MODÉRÉ"
            color_bar = f"\033[93m{bar}\033[0m"  # Jaune
        elif score >= 0.25:
            niveau = "🟡 FAIBLE"
            color_bar = f"\033[93m{bar}\033[0m"  # Jaune
        else:
            niveau = "🟢 TRÈS FAIBLE"
            color_bar = f"\033[92m{bar}\033[0m"  # Vert

        print(f"   Score    : {score:.1%} {niveau}")
        print(f"   Barre    : [{bar}]")
        print(f"   📖 Info  : {info['description']}")
        print(f"   💭 Ex.   : {info['exemples']}")
        print()

    print("-" * 80)

    # Résumé global
    print("\n📊 RÉSUMÉ")
    print("-" * 80)

    # Trouver la catégorie dominante
    max_key = max(results, key=results.get)
    max_score = results[max_key]
    max_info = categories[max_key]

    print(f"   🎯 Catégorie principale : {max_info['emoji']} {max_info['nom']}")
    print(f"   📈 Score maximum        : {max_score:.1%}")
    print()

    # Évaluation globale
    toxicity_score = results['toxicity']

    if toxicity_score >= 0.75:
        verdict = "🚨 CONTENU HAUTEMENT TOXIQUE - Action recommandée"
    elif toxicity_score >= 0.50:
        verdict = "⚠️ CONTENU MODÉRÉMENT TOXIQUE - Vérification suggérée"
    elif toxicity_score >= 0.25:
        verdict = "⚡ CONTENU LÉGÈREMENT TOXIQUE - Surveillance"
    else:
        verdict = "✅ CONTENU ACCEPTABLE"

    print(f"   🏁 Verdict global       : {verdict}")

    # Alertes spécifiques
    print(f"\n   🔔 Alertes spécifiques  :")
    alerts = []

    if results['threat'] > 0.5:
        alerts.append("      • MENACE détectée - Priorité élevée")
    if results['severe_toxicity'] > 0.5:
        alerts.append("      • TOXICITÉ SÉVÈRE - Nécessite attention")
    if results['identity_attack'] > 0.6:
        alerts.append("      • DISCRIMINATION détectée - Possibles implications légales")
    if results['insult'] > 0.7:
        alerts.append("      • INSULTES répétées")
    if results['obscene'] > 0.7:
        alerts.append("      • LANGAGE VULGAIRE excessif")

    if alerts:
        for alert in alerts:
            print(alert)
    else:
        print("      • Aucune alerte critique")

    print("\n" + "=" * 80 + "\n")


# Exemples d'utilisation
if __name__ == "__main__":

    exemples = ["La gauche écolo va revenir à la charge avec leur caisse unique. Caisse unique avec primes calculées selon le revenu. Cela aura pour conséquence que les mêmes vont payer pour pouvoir fiancer encore d'avantage d'assistés qui ne paieront rien. Regardez en France le désastre de leur Caisse maladie unique. Manque de médecins, Manque d'hôpitaux. Système de santé délabrée. La Caisse unique c'est une chose. Mais grand jamais, Non et Non à un impôt déguisé qui plume les assurés et fait payer les primes selon le revenu-fortune de l'assuré. Non à cette nouvelle arnaque des gauchos et partie des droitards-centristes. "]

    for i, texte in enumerate(exemples, 1):
        print(f"\n{'#' * 80}")
        print(f"# EXEMPLE {i}/{len(exemples)}")
        print(f"{'#' * 80}")
        print_category_analysis(texte)

        if i < len(exemples):
            input("\n⏸️  Appuyez sur Entrée pour voir l'exemple suivant...\n")