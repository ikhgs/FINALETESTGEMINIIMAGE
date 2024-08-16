from flask import Flask, request, jsonify
import os
import google.generativeai as genai

# Configuration de l'API Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialisation de l'application Flask
app = Flask(__name__)

# Route pour gérer les requêtes avec 'text' et 'image_url'
@app.route('/api/pro_with_image', methods=['GET'])
def process_text_and_image():
    text = request.args.get('text')
    image_url = request.args.get('image_url')

    if text and image_url:
        # Télécharger l'image via l'URL et la transmettre à Gemini
        file = genai.upload_file(image_url, mime_type="image/jpeg")

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

    return jsonify({"error": "Invalid parameters"}), 400

# Route pour gérer les requêtes avec seulement 'text'
@app.route('/api/pro_text_only', methods=['GET'])
def process_text():
    text = request.args.get('text')

    if text:
        # Créer une session de chat sans image
        chat_session = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }
        ).start_chat(history=[{"role": "user", "parts": [text]}])

        # Envoyer le message et recevoir la réponse
        response = chat_session.send_message(text)
        return jsonify({"response": response.text})

    return jsonify({"error": "No text provided"}), 400

# Lancement de l'application sur le host 0.0.0.0
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
