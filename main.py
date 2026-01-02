import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# Configurazione Base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_final_v14.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads iPad", layout="wide")

# Funzione IA Ultra-Semplificata
def estrai_dati(testo):
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        return "Errore: Chiave non trovata nei Secrets"
    
    # Proviamo l'endpoint più universale in assoluto
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"Estrai in JSON: sku, nome, materiale, peso, descrizione. Testo: {testo}"}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res = response.json()
            return json.loads(res['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', ''))
        else:
            return f"Errore Google {response.status_code}: {response.text}"
    except Exception as e:
        return f"Errore connessione: {str(e)}"

# --- INTERFACCIA ---
st.title("💎 MyBeads iPad Pro")

testo_web = st.text_area("Incolla testo da Safari:", height=150)

if 'dati' not in st.session_state:
    st.session_state.dati = {"sku":"", "nome":"", "materiale":"", "peso":0.0, "descrizione":""}

if st.button("🤖 ANALIZZA"):
    risultato = estrai_dati(testo_web)
    if isinstance(risultato, dict):
        st.session_state.dati = risultato
        st.success("Dati estratti!")
    else:
        st.error(risultato)

# Form di salvataggio
with st.form("salva_bead"):
    c1, c2 = st.columns(2)
    with c1:
        sku = st.text_input("SKU", value=st.session_state.dati.get("sku", ""))
        nome = st.text_input("Nome", value=st.session_state.dati.get("nome", ""))
    with c2:
        peso = st.number_input("Peso (g)", value=float(st.session_state.dati.get("peso", 0) or 0))
        mat = st.text_input("Materiale", value=st.session_state.dati.get("materiale", ""))
    
    desc = st.text_area("Descrizione", value=st.session_state.dati.get("descrizione", ""))
    foto = st.file_uploader("📸 Carica Foto", type=['jpg', 'png'])

    if st.form_submit_button("💾 SALVA"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("CREATE TABLE IF NOT EXISTS charms (sku TEXT, nome TEXT, peso REAL, materiale TEXT, descrizione TEXT, foto TEXT)")
        
        path_foto = ""
        if foto:
            path_foto = f"immagini/{sku}.jpg"
            Image.open(foto).convert('RGB').save(os.path.join(BASE_DIR, path_foto), "JPEG")
        
        conn.execute("INSERT INTO charms VALUES (?,?,?,?,?,?)", (sku, nome, peso, mat, desc, path_foto))
        conn.commit()
        st.success("Salvato!")

# Visualizzazione
st.divider()
if st.checkbox("Mostra Collezione"):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM charms", conn)
        st.table(df)
        for _, r in df.iterrows():
            if r['foto']: st.image(os.path.join(BASE_DIR, r['foto']), width=200)
    except:
        st.write("Ancora nessun dato.")
