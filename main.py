import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="Trollbeads Collector PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO INTELLIGENTE POTENZIATO ---
# Ho aggiunto più varianti per assicurarmi che il sistema trovi i dati
INFO_PREDEFINITE = {
    "il canto della balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Lise Aagaard",
        "materiale": "Vetro",
        "prezzo": 55.0,
        "note": "Bead in vetro sfaccettato con sfumature blu e verdi."
    },
    "fede speranza carità": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Classico simbolo con croce, ancora e cuore."
    },
    "fede speranza e carità": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Classico simbolo con croce, ancora e cuore."
    }
}

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER, posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione"])

if menu == "🌐 Ricerca & Acquisizione":
    st.header("🌐 Centro Acquisizione Intelligente")
    
    # Pulizia input: togliamo spazi extra e rendiamo tutto minuscolo
    raw_input = st.text_input("Inserisci Nome o SKU per auto-completare", placeholder="Es: il canto della balena")
    search_q = raw_input.strip().lower()
    
    # Cerchiamo nel dizionario
    dati = INFO_PREDEFINITE.get(search_q, {
        "sku": raw_input, 
        "nome": raw_input.capitalize(), 
        "designer": "", 
        "materiale": "Argento 925", 
        "prezzo": 0.0, 
        "note": ""
    })

    if raw_input:
        st.markdown(f"[📸 Apri Ricerca Immagini Google](https://www.google.it/search?q=trollbeads+{search_q.replace(' ', '+')}&tbm=isch)")
        
        with st.form("form_acquisizione"):
            st.subheader("📝 Verifica i dati prima di salvare")
            col1, col2 = st.columns(2)
            with col1:
                w_sku = st.text_input("SKU ufficiale", value=dati['sku'])
                w_nome = st.text_input("Nome del Bead", value=dati['nome'])
                w_designer = st.text_input("Designer", value=dati['designer'])
            with col2:
                w_prezzo = st.number_input("Prezzo (€)", value=dati['prezzo'])
                w_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"], 
                                     index=["Argento 925", "Vetro", "Pietra", "Oro"].index(dati['materiale']))
                w_foto = st.file_uploader("Carica foto", type=['jpg', 'jpeg', 'png'])
            
            w_note = st.text_area("Note", value=dati['note'])
            
            if st.form_submit_button("✨ SALVA NEL CATALOGO"):
                fname = f"immagini/{w_sku}.jpg"
                if w_foto:
                    Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                VALUES ('Trollbeads',?,?,?,?,?,?,?,0,0)''', 
                             (w_sku, w_nome, w_mat, w_designer, w_prezzo, w_note, fname))
                conn.commit()
                st.success(f"Bead '{w_nome}' salvato con successo!")

# (Le altre sezioni Catalogo e Collezione rimangono invariate)
