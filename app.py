from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import io
import pdfplumber
import pandas as pd
import re
import datetime as dt

app = Flask(__name__)

# Chemin du fichier JSON des identifiants du compte de service
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account.json'  # Assurez-vous d'ajouter le fichier comme secret sur Render
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    return service

# Endpoint pour lister les fichiers dans un dossier Google Drive
@app.route('/list_files', methods=['GET'])
def list_files_in_folder():
    folder_id = request.args.get('folder_id')
    if not folder_id:
        return jsonify({'error': 'folder_id is required'}), 400

    service = authenticate_google_drive()
    all_files = []
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None

    try:
        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
                pageToken=page_token
            ).execute()
            all_files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break
        return jsonify(all_files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint pour télécharger et analyser un fichier PDF
@app.route('/download_and_extract', methods=['POST'])
def download_and_extract():
    file_id = request.json.get('file_id')
    if not file_id:
        return jsonify({'error': 'file_id is required'}), 400

    service = authenticate_google_drive()
    request_drive = service.files().get_media(fileId=file_id)
    file_path = os.path.join('/tmp', f"{file_id}.pdf")

    try:
        # Télécharger le fichier PDF
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request_drive)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% complete.")
        
        # Extraire les informations du PDF
        doc_num, immat_info = extract_info_from_pdf(file_path)
        os.remove(file_path)  # Supprimer le fichier après extraction
        return jsonify({'doc_num': doc_num, 'immat_info': immat_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_info_from_pdf(file_path):
    doc_num, immat_info = None, None
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                # Extraction du numéro de document
                if not doc_num:
                    doc_num_match = re.search(r'N° du document :\s*([\w-]+)', text)
                    doc_num = doc_num_match.group(1) if doc_num_match else None

                # Extraction de l'immatriculation
                immat_match = re.search(r'NICE AEROPORT\s(.*?)(?=\n)', text)
                if immat_match and not immat_info:
                    immat_info = immat_match.group(1).strip()
                    immat_info = re.sub(r'NICE AEROPORT|CAGNES SUR MER|NICE', '', immat_info, flags=re.IGNORECASE).strip()
                    immat_info = immat_info.replace(' ', '-')
        
        return doc_num, immat_info
    except Exception as e:
        print(f"Erreur lors de l'extraction des informations du fichier {file_path}: {e}")
        return None, None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
