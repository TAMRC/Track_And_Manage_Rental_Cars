from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Active CORS pour toutes les routes

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdfFile' not in request.files:
        return jsonify({'message': 'Aucun fichier PDF trouvé'}), 400

    pdf_file = request.files['pdfFile']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)

    message = "Fichier PDF traité avec succès."
    return jsonify({'message': message})

# Ajout de la route de santé
@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)
