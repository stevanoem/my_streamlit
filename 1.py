import os
from datetime import datetime
import string

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler


LOG_DIR = "logovi"
FILE_DIR = "fajlovi"

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
        log_path = os.path.join(LOG_DIR, 'proba.log')
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

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




