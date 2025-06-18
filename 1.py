import os
from datetime import datetime

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- GOOGLE DRIVE SETUP ---

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'  # stavi u isti folder gde je app ili apsolutnu putanju
TOKEN_FILE = 'token.json'


LOG_DIR = "logovi"
FILE_DIR = "fajlovi"

def google_drive_auth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def upload_drive(file_path, creds):

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(file_path)
    }

    media = MediaFileUpload(file_path)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return file.get('id')

def inicijalizuj_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("ProbaApp")

    # zastita od duplog logovanja, proveravam da li logger nema hendler
    if len(logger.handlers) == 0:
        logger.setLevel(logging.INFO)

        # ne prosledjuje poruku parent loggeru, sprecavam dupliranje logova
        logger.propagate = False

        log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


        #Fajl hendler
        #log_path = os.path.join(LOG_DIR, 'proba.log')
        #file_handler = logging.FileHandler(log_path)
        #file_handler.setFormatter(log_formatter)
        #logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)

    return logger

def analiza(sadrzaj):
    return sadrzaj.upper()

if 'logger' not in st.session_state:
    st.session_state['logger'] = inicijalizuj_logger()

logger = st.session_state['logger']

st.title("Proba")

if "stage" not in st.session_state:
    st.session_state['stage'] = 'pocetak'
    st.session_state['txt fajl'] = ''
    st.session_state['fajl putanja'] = ''
    st.session_state['rezultat'] = ''
    logger.info("Session state inicijalizovan. Aplikacija ceka fajl.")


# cekanje fajla
if st.session_state['stage'] == 'pocetak':
    fajl = st.file_uploader(
        "Izaberi txt fajl",
        type=['txt']
    )

    if fajl is not None:
        os.makedirs(FILE_DIR, exist_ok=True)
        fajl_putanja = os.path.join(FILE_DIR, fajl.name)

        with open(fajl_putanja, 'wb') as f:
            f.write(fajl.getbuffer())

        sadrzaj = fajl.read().decode('utf-8')

        st.session_state['txt fajl'] = sadrzaj
        st.session_state['fajl putanja'] = fajl_putanja

        st.session_state['stage'] = 'fajl sacuvan'
        logger.info(f'Fajl {fajl.name} uspesno sacuvan')
        st.rerun()

# fajl ubacen ceka se analiza
elif st.session_state['stage'] == 'fajl sacuvan':
    st.success(f'Fajl spreman za analizu')

    if st.button('Pokreni analizu'):
        st.session_state['stage'] = 'analiza u toku'
        st.rerun()

# analiza
elif st.session_state['stage'] == 'analiza u toku':
    try:
        logger.info('Pokrenuta analiza')
        st.session_state['rezultat'] = analiza(st.session_state['txt fajl'])
                # --- Google Drive upload ---
        try:
            creds = google_drive_auth()

            # Fajl korisnika
            korisnicki_fajl = st.session_state['fajl putanja']
            korisnicki_fajl_drive_id = upload_drive(korisnicki_fajl, creds)
            logger.info(f'Korisnicki fajl uploadovan na Google Drive sa ID: {korisnicki_fajl_drive_id}')

            # Log fajl
            log_fajl_putanja = os.path.join(LOG_DIR, 'proba.log')
            log_fajl_drive_id = upload_drive(log_fajl_putanja, creds)
            logger.info(f'Log fajl uploadovan na Google Drive sa ID: {log_fajl_drive_id}')

        except Exception as e:
            logger.error(f'Greska prilikom upload-a na Google Drive: {e}')
        st.session_state['stage'] = 'zavrseno'

        st.rerun()
    except Exception as e:
        logger.error(f'Greska {e}')

        st.session_state['stage'] = 'fajl sacuvan'
        st.rerun()

# analiza zavrsena
elif st.session_state['stage'] == 'zavrseno':
    st.success('Analiza zavrsena')
    st.text(st.session_state['rezultat'])

    if st.button("Pokreni novu analizu"):
        st.session_state['stage'] = 'pocetak'
        logger.info('Pokretanje nove analize')
        st.rerun()




