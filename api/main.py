from flask import Flask, request, jsonify, session
import os
import google.generativeai as genai
import requests
from secrets import token_hex

app = Flask(__name__)

# Génère une clé secrète temporaire pour les sessions à chaque démarrage
app.secret_key = token_hex(16)

# Configuration de l'API Gemini avec une clé provenant des variables d'environnement
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    raise Exception("GEMINI_API_KEY n'est pas configuré. Assurez-vous de l'avoir défini dans les variables d'environnement.")

def download_image(url):
    """Télécharge une image depuis une URL et l'enregistre localement."""
    response = requests.get(url)
    if response.status_code == 200:
        image_path = "temp_image.jpg"
        with open(image_path, "wb") as f:
            f.write(response.content)
        return image_path
    else:
        raise Exception("Échec du téléchargement de l'image.")

@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if not text:
        return jsonify({"error": "Le paramètre 'text' est manquant."}), 400

    if image_url:
        image_path = download_image(image_url)
        session['image_path'] = image_path  # Stocker le chemin de l'image dans la session
        session['image_url'] = image_url

    elif 'image_path' in session:
        image_path = session['image_path']  # Récupérer le chemin de l'image depuis la session

    else:
        return jsonify({"error": "Le paramètre 'image_url' est manquant et aucune image n'a été précédemment fournie."}), 400

    if 'history' not in session:
        session['history'] = []

    session['history'].append({"role": "user", "parts": [text]})

    # Logique pour appeler Google Gemini (ici, vous devriez appeler votre modèle Gemini)
    response_text = "Réponse simulée basée sur l'image et le texte."

    session['history'].append({"role": "model", "parts": [response_text]})

    return jsonify({"response": response_text})

# Lancement de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
