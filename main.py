import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# Configurazione cartelle (iPad compatibile)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_finale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'foto')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI", layout="wide")

# RECUPERO CHIAVE
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def estrai_con_ia(testo_utente):
    # L'unico endpoint che attualmente garantisce il funzionamento con chiavi gratuite v1
    # Usiamo il modello 8b (più compatibile) e forziamo la v1 (non beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-8b:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    # Prompt semplificato per ridurre errori di parsing
    prompt = f"Analizza e rispondi solo in JSON: {{'sku':'', 'nome':'', 'materiale':'', 'peso':0.0, 'descrizione':''}}. Testo: {testo_utente}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # Se il modello 8b fallisce (404), proviamo l'ultimo tentativo col modello base
        if response.status_code == 404:
            url_alt = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            response = requests.post(url_alt, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            res_data = response.json()
            testo_ia = res_data['candidates'][0]['content']['parts'][0]['text']
            # Pulizia stringa JSON per iPad
            clean_json = testo_ia.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        else:
            return f"Errore specifico Google: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Errore connessione: {str(e)}"

# --- INTERFACCIA ---
st.title("💍 MyBeads iPad Manager")

if 'dati' not in st.session_state:
    st.session_state.dati = {"sku":"", "nome":"", "materiale":"", "peso":0.0, "descrizione":""}

testo_area = st.text_area("Incolla qui il testo da Safari:", height=150)

if st.button("🤖 ANALIZZA TESTO"):
    if testo_area:
        with st.spinner("Estrazione in corso..."):
            risultato = estrai_con_ia(testo_area)
            if isinstance(risultato, dict):
                st.session_state.dati = risultato
                st.success("Dati caricati!")
            else:
                st.error(risultato)

st.divider()

# FORM DI SALVATAGGIO (Sempre attivo, anche se l'IA fallisce)
with st.form("scheda_bead"):
    c1, c2 = st.columns(2)
    with c1:
        in_sku = st.text_input("SKU", value=st.session_state.dati.get('sku', ''))
        in_nome = st.text_input("Nome", value=st.session_state.dati.get('nome', ''))
    with c2:
        in_peso = st.number_input("Peso (g)", value=float(st.session_state.dati.get('peso', 0) or 0))
        in_mat = st.text_input("Materiale", value=st.session_state.dati.get('materiale', ''))
    
    in_desc = st.text_area("Descrizione (Significato)", value=st.session_state.dati.get('descrizione', ''))
    in_foto = st.file_uploader("📸 Foto (Rullino iPad)", type=['jpg', 'png', 'jpeg'])

    if st.form_submit_button("💾 SALVA NEL DATABASE"):
        if in_sku and in_nome:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("CREATE TABLE IF NOT EXISTS beads (sku TEXT, nome TEXT, peso REAL, materiale TEXT, descrizione TEXT, foto TEXT)")
            
            path_salvataggio = ""
            if in_foto:
                path_salvataggio = f"foto/{in_sku}.jpg"
                Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, path_salvataggio), "JPEG")
            
            conn.execute("INSERT INTO beads VALUES (?,?,?,?,?,?)", (in_sku, in_nome, in_peso, in_mat, in_desc, path_salvataggio))
            conn.commit()
            conn.close()
            st.success("Bead salvato correttamente!")
        else:
            st.error("Inserisci SKU e Nome per salvare.")

# VISUALIZZAZIONE ARCHIVIO
if st.checkbox("Mostra la mia collezione"):
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM beads", conn)
        conn.close()
        for _, r in df.iterrows():
            with st.expander(f"{r['nome']} ({r['sku']})"):
                col_img, col_txt = st.columns([1,2])
                with col_img:
                    if r['foto']: st.image(os.path.join(BASE_DIR, r['foto']), use_container_width=True)
                with col_txt:
                    st.write(f"**Peso:** {r['peso']}g | **Mat:** {r['materiale']}")
                    st.write(f"*Descrizione:* {r['descrizione']}")
