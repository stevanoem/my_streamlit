import os
from datetime import datetime

import streamlit as st
import logging
#from logging.handlers import RotatingFileHandler

#from google.oauth2.credentials import Credentials
#from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
#from google.auth.transport.requests import Request
from google.oauth2 import service_account

# --- GOOGLE DRIVE SETUP ---

SCOPES = ['https://www.googleapis.com/auth/drive.file']
#CREDENTIALS_FILE = 'credentials.json'  # stavi u isti folder gde je app ili apsolutnu putanju
#TOKEN_FILE = 'token.json'


LOG_DIR = "logovi"
FILE_DIR = "fajlovi"

def google_drive_auth():
    """
    Autentifikacija pomoću Google Service Account kredencijala iz Streamlit Secrets.
    Ovo je ispravan i preporučen način za server-side aplikacije.
    """
    logger = logging.getLogger(__name__) # Dobijamo logger za svaki slučaj

    try:
        # Učitava SVE kredencijale iz secrets sekcije koju smo nazvali [google_service_account]
        # st.secrets vraća rečnik (dictionary) koji savršeno odgovara onome što funkcija očekuje
        creds_json = st.secrets["google_service_account"]
        
        # Kreiramo objekat sa kredencijalima iz učitanog rečnika
        creds = service_account.Credentials.from_service_account_info(
            creds_json, 
            scopes=SCOPES
        )
        
        logger.info("Uspešno kreirani kredencijali pomoću Service Account-a.")
        return creds

    except KeyError:
        # ako sekcija [google_service_account] uopšte ne postoji u secrets
        error_msg = "Greška: Sekcija [google_service_account] nije pronađena u Streamlit Secrets."
        logger.error(error_msg)
        st.error(error_msg)
        st.error("Molimo vas, proverite da li ste ispravno uneli tajne na Streamlit Cloud-u i u lokalnom 'secrets.toml' fajlu.")
        return None

    except Exception as e:
    
        error_msg = f"Greška prilikom učitavanja ili parsiranja Service Account kredencijala: {e}"
        logger.error(error_msg)
        st.error("Došlo je do neočekivane greške pri povezivanju sa Google nalogom.")
        st.error(error_msg)
        return None

def upload_drive(file_path, creds, folder_id):
    """Postavlja fajl sa date putanje na Google Drive."""
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(file_path) ,
            'parents': [folder_id] }
        media = MediaFileUpload(file_path)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return file.get('id')
    except Exception as e:
        
        logging.getLogger(__name__).error(f"Greška prilikom upload-a na Google Drive: {e}")
        st.error(f"Greška prilikom upload-a na Google Drive: {e}")
        return None

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
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        original_naziv, ekstenzija = os.path.splitext(fajl.name)
        
        novi_naziv_fajla = f"{original_naziv}_{timestamp}{ekstenzija}"
        
        fajl_putanja = os.path.join(FILE_DIR, novi_naziv_fajla)

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
    with st.spinner("Vrši se analiza i upload..."):
        # ... (analiza) ...
        st.session_state['rezultat'] = analiza(st.session_state['txt fajl'])

        creds = google_drive_auth()

        # 1. Eksplicitna provera da li je autentifikacija uspela
        if creds:

            try:
                DRIVE_FOLDER_ID = st.secrets["google_drive_folder"]["folder_id"]
            except KeyError:
                st.error("Nije pronađen ID Google Drive foldera u secrets.toml!")
                DRIVE_FOLDER_ID = None
            #korisnicki_fajl_putanja = st.session_state['fajl putanja']
            #drive_id = upload_drive(korisnicki_fajl_putanja, creds)

            if DRIVE_FOLDER_ID:
                korisnicki_fajl_putanja = st.session_state['fajl putanja']
                drive_id = upload_drive(korisnicki_fajl_putanja, creds, DRIVE_FOLDER_ID)
            
            # 2. Eksplicitna provera da li je upload uspeo
            if drive_id:
                logger.info(f"Fajl uspešno uploadovan. Drive ID: {drive_id}")
                st.session_state['stage'] = 'zavrseno' # SAMO AKO JE SVE PROŠLO OK
            else:
                # Upload nije uspeo, greška je već ispisana
                st.session_state['stage'] = 'fajl sacuvan' # Vraćamo korisnika nazad
        else:
            # Autentifikacija nije uspela, greška je već ispisana
            st.session_state['stage'] = 'fajl sacuvan' # Vraćamo korisnika nazad

        st.rerun()

# analiza zavrsena
elif st.session_state['stage'] == 'zavrseno':
    st.success('Analiza zavrsena')
    st.text(st.session_state['rezultat'])

    if st.button("Pokreni novu analizu"):
        st.session_state['stage'] = 'pocetak'
        logger.info('Pokretanje nove analize')
        st.rerun()




