from flask import Flask, request, jsonify, session
import os
import google.generativeai as genai
import requests
from flask_session import Session

app = Flask(__name__)

# Configuration de l'API Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configurer la clé secrète pour Flask sessions
app.secret_key = os.urandom(24)

# Configurer Flask pour stocker les sessions côté serveur
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def download_image(url):
    """Télécharge une image depuis une URL et l'enregistre localement."""
    response = requests.get(url)
    if response.status_code == 200:
        with open("temp_image.jpg", "wb") as f:
            f.write(response.content)
        return "temp_image.jpg"
    else:
        raise Exception("Image download failed")

def start_or_continue_chat(text):
    """Continue la session de chat pour l'utilisateur avec l'image et le texte fournis."""
    # Vérifiez si une image existe déjà dans la session
    if 'image_file' not in session:
        raise Exception("No image found in session. Please upload an image first.")

    # Récupérer le modèle et l'historique pour cette session spécifique
    user_session = session.get('chat_session', {
        "chat_history": [],
        "model": genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
        )
    })

    history = user_session["chat_history"]
    model = user_session["model"]
    image_file = session['image_file']  # Récupère l'image de la session

    # Ajoute l'image et le texte dans l'historique (uniquement lors de la première requête)
    if len(history) == 0:
        history.append({"role": "user", "parts": [image_file, text]})
    else:
        history.append({"role": "user", "parts": [text]})

    # Continue la conversation avec l'historique complet
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(text)

    # Mise à jour de l'historique avec la réponse du modèle
    history.append({"role": "model", "parts": [response.text]})

    # Enregistrer l'historique dans la session
    session['chat_session'] = {
        "chat_history": history,
        "model": model
    }

    return response.text

@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if not text or not image_url:
        return jsonify({"error": "Missing 'text' or 'image_url' parameter"}), 400

    try:
        # Télécharger et enregistrer l'image localement
        local_image_path = download_image(image_url)
        image_file = genai.upload_file(local_image_path, mime_type="image/jpeg")

        # Enregistrez l'image dans la session pour les requêtes futures
        session['image_file'] = image_file

        # Démarre la conversation avec l'image et le texte
        response_text = start_or_continue_chat(text)
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pro_text_only', methods=['GET'])
def process_text_only():
    text = request.args.get('text')

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    try:
        # Continue la conversation avec seulement du texte, en utilisant l'image existante
        response_text = start_or_continue_chat(text)
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lancement de l'application sur le host 0.0.0.0
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
