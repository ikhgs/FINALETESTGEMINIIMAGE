import requests
from flask import Flask, request, jsonify
import os
import google.generativeai as genai

# Configuration de l'API Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialisation de l'application Flask
app = Flask(__name__)

# Fonction pour télécharger l'image depuis une URL
def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Enregistrer l'image temporairement
        with open("temp_image.jpg", "wb") as f:
            f.write(response.content)
        return "temp_image.jpg"
    else:
        raise Exception("Image download failed")

# Route pour gérer les requêtes avec 'text' et 'image_url'
@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if text and image_url:
        try:
            # Télécharger l'image depuis l'URL
            local_image_path = download_image(image_url)

            # Télécharger l'image à Gemini
            file = genai.upload_file(local_image_path, mime_type="image/jpeg")

            # Créer une session de chat avec le modèle Gemini
            chat_session = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "text/plain",
                }
            ).start_chat(history=[{"role": "user", "parts": [file, text]}])

            # Envoyer le message et recevoir la réponse
            response = chat_session.send_message("Que voyez-vous sur cette image?")
            return jsonify({"response": response.text})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid parameters"}), 400

# Lancement de l'application sur le host 0.0.0.0
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
