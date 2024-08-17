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
        with open("temp_image.jpg", "wb") as f:
            f.write(response.content)
        return "temp_image.jpg"
    else:
        raise Exception("Échec du téléchargement de l'image.")

@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if not text:
        return jsonify({"error": "Le paramètre 'text' est manquant."}), 400

    if not image_url and 'image_url' not in session:
        return jsonify({"error": "Le paramètre 'image_url' est manquant."}), 400

    if 'image_url' in session and not image_url:
        image_url = session['image_url']

    if image_url and 'image_url' not in session:
        session['image_url'] = image_url
        download_image(image_url)

    if 'history' not in session:
        session['history'] = []

    session['history'].append({"role": "user", "parts": [text]})

    # Logique pour appeler Google Gemini
    response_text = "Réponse simulée basée sur l'image et le texte."

    session['history'].append({"role": "model", "parts": [response_text]})

    return jsonify({"response": response_text})

# Lancement de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
