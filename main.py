from flask import Flask, request, jsonify
import os
import google.generativeai as genai
import requests

app = Flask(__name__)

# Configuration de l'API Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Dictionnaire pour stocker les sessions de conversation par user_id
chat_sessions = {}

# Compteur global pour user_id
current_user_id = 1

def download_image(url):
    """Télécharge une image depuis une URL et l'enregistre localement."""
    response = requests.get(url)
    if response.status_code == 200:
        with open("temp_image.jpg", "wb") as f:
            f.write(response.content)
        return "temp_image.jpg"
    else:
        raise Exception("Image download failed")

def start_or_continue_chat(user_id, text, image_url=None):
    """Démarre ou continue une session de chat pour l'utilisateur donné."""
    if user_id not in chat_sessions:
        # Si l'utilisateur n'a pas encore de session, on la crée
        chat_sessions[user_id] = {
            "model": genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                }
            ),
            "history": []
        }

    # Récupère la session actuelle de l'utilisateur
    user_session = chat_sessions[user_id]
    model = user_session["model"]
    history = user_session["history"]

    # Si une image est fournie, téléchargez-la et téléchargez-la à Google Gemini
    if image_url:
        local_image_path = download_image(image_url)
        image_file = genai.upload_file(local_image_path, mime_type="image/jpeg")
        history.append({"role": "user", "parts": [image_file, text]})
    else:
        # Si seulement du texte est fourni, l'ajouter à l'historique
        history.append({"role": "user", "parts": [text]})

    # Continue la conversation avec l'historique complet
    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(text)

    # Mise à jour de l'historique avec la réponse du modèle
    history.append({"role": "model", "parts": [response.text]})

    return response.text

@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    global current_user_id

    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    # Génère un user_id automatiquement
    user_id = current_user_id

    try:
        # Continue la conversation ou démarre une nouvelle session
        response_text = start_or_continue_chat(user_id, text, image_url)
        # Incrémente l'ID pour le prochain utilisateur
        current_user_id += 1
        return jsonify({"user_id": user_id, "response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pro_text_only', methods=['GET'])
def process_text_only():
    global current_user_id

    text = request.args.get('text')

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    # Génère un user_id automatiquement
    user_id = current_user_id

    try:
        # Continue la conversation avec uniquement du texte
        response_text = start_or_continue_chat(user_id, text)
        # Incrémente l'ID pour le prochain utilisateur
        current_user_id += 1
        return jsonify({"user_id": user_id, "response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lancement de l'application sur le host 0.0.0.0
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
