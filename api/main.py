from flask import Flask, request, jsonify, session
import os
import google.generativeai as genai
import requests
from secrets import token_hex

app = Flask(__name__)
app.secret_key = token_hex(16)  # Clé secrète pour gérer les sessions

# Configuration de l'API Google Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
    """Télécharge le fichier sur Gemini et retourne le fichier."""
    file = genai.upload_file(path, mime_type=mime_type)
    return file

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
    """Traite le texte et l'image pour la première requête ou continue une conversation."""
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if not text:
        return jsonify({"error": "Le paramètre 'text' est requis."}), 400

    # Initialisation de l'historique si ce n'est pas déjà fait
    if 'history' not in session:
        session['history'] = []

    # Gérer les cas où l'image est fournie ou non
    if image_url:
        # Télécharger l'image et l'ajouter à Gemini
        image_path = download_image(image_url)
        image_file = upload_to_gemini(image_path)

        # Ajouter le message de l'utilisateur avec l'image
        session['history'].append({"role": "user", "parts": [image_file, text]})
    else:
        # Ajouter le message de l'utilisateur sans image
        session['history'].append({"role": "user", "parts": [text]})

    # Créer la session de chat
    chat_session = genai.ChatSession()
    chat_session.add_history(session['history'])

    # Envoyer le message et obtenir la réponse
    response = chat_session.send_message(text)
    
    # Ajouter la réponse du modèle à l'historique
    session['history'].append({"role": "model", "parts": [response.text]})

    return jsonify({"response": response.text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
