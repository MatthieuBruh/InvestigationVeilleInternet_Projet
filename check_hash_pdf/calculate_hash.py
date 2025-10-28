# b15d89a0be44b44aa0eb1b71c5c9c408cc9918fc68a16fd56b5cdd723addaf01

import hashlib


def verifier_hash_pdf(chemin_pdf, hash_attendu):
    """
    Vérifie si le hash SHA-256 d'un fichier PDF correspond au hash attendu

    Args:
        chemin_pdf (str): Chemin vers le fichier PDF
        hash_attendu (str): Hash SHA-256 attendu

    Returns:
        bool: True si les hash correspondent, False sinon
    """
    try:
        # Lire le fichier PDF
        with open(chemin_pdf, 'rb') as f:
            pdf_data = f.read()

        # Calculer le hash SHA-256
        hash_calcule = hashlib.sha256(pdf_data).hexdigest()

        # Comparer les hash
        if hash_calcule == hash_attendu:
            print(f"✅ SUCCÈS : Les hash correspondent !")
            print(f"   Fichier : {chemin_pdf}")
            print(f"   Hash    : {hash_calcule}")
            return True
        else:
            print(f"❌ ÉCHEC : Les hash ne correspondent pas !")
            print(f"   Fichier  : {chemin_pdf}")
            print(f"   Attendu  : {hash_attendu}")
            print(f"   Calculé  : {hash_calcule}")
            return False

    except FileNotFoundError:
        print(f"❌ ERREUR : Fichier introuvable : {chemin_pdf}")
        return False
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False


# Utilisation directe
if __name__ == "__main__":
    chemin = "./20min-103441329.pdf"
    hash_ref = "b15d89a0be44b44aa0eb1b71c5c9c408cc9918fc68a16fd56b5cdd723addaf01"
    verifier_hash_pdf(chemin, hash_ref)