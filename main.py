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

def generate_response_with_gemini(text, image_path=None):
    """Appelle l'API Google Gemini pour générer une réponse basée sur le texte et l'image."""
    if image_path:
        # Télécharger l'image sur Gemini et obtenir un URI
        image_file = genai.upload_file(image_path, mime_type="image/jpeg")

        # Créer une session de chat avec l'historique et l'image
        chat_session = genai.ChatSession(
            model="gemini-1.5-pro",
            temperature=1,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192
        )

        chat_session.add_user_message(text)
        chat_session.add_image(image_file)

    else:
        # Créer une session de chat sans image
        chat_session = genai.ChatSession(
            model="gemini-1.5-pro",
            temperature=1,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192
        )
        chat_session.add_user_message(text)

    # Envoyer le message et obtenir la réponse
    response = chat_session.generate()

    return response.text

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

    # Appel à Google Gemini pour générer la réponse
    response_text = generate_response_with_gemini(text, image_path)

    session['history'].append({"role": "model", "parts": [response_text]})

    return jsonify({"response": response_text})

# Lancement de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
