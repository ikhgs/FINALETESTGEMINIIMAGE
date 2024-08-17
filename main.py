from flask import Flask, request, jsonify
import os
import google.generativeai as genai

app = Flask(__name__)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configurez votre modèle
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Dictionnaire pour stocker l'historique des conversations
conversation_history = {}

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

@app.route('/api/bas', methods=['POST'])
def api_bas():
    if 'image' not in request.files or 'prompt' not in request.form:
        return jsonify({"error": "Image and prompt are required"}), 400

    image = request.files['image']
    prompt = request.form['prompt']
    user_id = 1  # Id utilisateur fixe pour cet exemple

    # Sauvegarder l'image temporairement
    image_path = 'temp_image.jpeg'
    image.save(image_path)

    file = upload_to_gemini(image_path, mime_type="image/jpeg")

    # Démarrer ou poursuivre la session de chat
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    chat_session = model.start_chat(
        history=conversation_history[user_id] + [
            {
                "role": "user",
                "parts": [file, prompt],
            }
        ]
    )
    
    # Enregistrer la session dans l'historique
    conversation_history[user_id] = chat_session.history

    response = chat_session.send_message(prompt)
    return jsonify({"response": response.text})

@app.route('/api/haut', methods=['GET'])
def api_haut():
    prompt = request.args.get('prompt')
    user_id = 1  # Id utilisateur fixe pour cet exemple

    if user_id not in conversation_history:
        return jsonify({"error": "No conversation history found for this user"}), 404

    chat_session = model.start_chat(
        history=conversation_history[user_id]
    )
    
    response = chat_session.send_message(prompt)
    
    # Enregistrer la mise à jour de la session dans l'historique
    conversation_history[user_id] = chat_session.history

    return jsonify({"response": response.text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
