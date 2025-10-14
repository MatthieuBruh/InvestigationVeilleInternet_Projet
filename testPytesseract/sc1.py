from PIL import Image
import pytesseract

# Si nécessaire, préciser le chemin vers l’exécutable tesseract
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

image = Image.open("./test.jpg")
texte = pytesseract.image_to_string(image, lang="fra")  # “fra” pour le français
print(texte)
