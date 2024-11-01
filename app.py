from flask import Flask, request, jsonify
import os

app = Flask(__name__)

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdfFile' not in request.files:
        return jsonify({'message': 'Aucun fichier PDF trouvé'}), 400

    pdf_file = request.files['pdfFile']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)

    # Code Python à exécuter sur le PDF, comme l'analyse ou la génération de rapport
    message = "Fichier PDF traité avec succès."

    return jsonify({'message': message})

if __name__ == "__main__":
    app.run(debug=True)