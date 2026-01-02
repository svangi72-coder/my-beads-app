import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# --- 1. SETUP AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_v12.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads iPad PRO", page_icon="💎", layout="wide")

# --- 2. LOGICA IA CON AUTO-CORREZIONE URL (FIX 404) ---
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def chiama_ia_google(testo):
    if not API_KEY:
        st.error("🔑 API KEY non configurata nei Secrets.")
        return None
    
    # Proviamo entrambi i percorsi che Google potrebbe richiedere
    endpoints = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    ]
    
    prompt = f"""
    Estrai i dati in JSON. Chiavi: sku, nome, designer, materiale, prezzo, peso, descrizione.
    Usa numeri per prezzo/peso. Testo: {testo}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for url in endpoints:
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                # Pulizia per iPad
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_json)
        except:
            continue
            
    st.error("❌ Nessun endpoint Google ha risposto (Errore 404 o 400). Verifica che la chiave sia attiva.")
    return None

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, peso REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. INTERFACCIA ---
st.sidebar.title("💎 MyBeads iPad")
menu = st.sidebar.radio("Vai a:", ["➕ Aggiungi con IA", "📖 La Mia Collezione", "💾 Backup Cloud"])

if menu == "➕ Aggiungi con IA":
    st.title("✨ Inserimento con IA")
    testo_web = st.text_area("Incolla qui la descrizione del sito:", height=200)
    
    if 'temp' not in st.session_state:
        st.session_state.temp = {"sku":"", "nome":"", "designer":"", "materiale":"Argento 925", "prezzo":0.0, "peso":0.0, "descrizione":""}

    if st.button("🤖 ANALIZZA TESTO"):
        if testo_web:
            with st.spinner("L'IA sta testando i percorsi di connessione..."):
                dati = chiama_ia_google(testo_web)
                if dati:
                    st.session_state.temp = dati
                    st.success("Dati estratti!")
        else:
            st.warning("Incolla un testo.")

    st.divider()

    with st.form("form_final"):
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("Codice SKU", value=st.session_state.temp.get("sku", ""))
            in_nome = st.text_input("Nome Ufficiale", value=st.session_state.temp.get("nome", ""))
            in_des = st.text_input("Designer", value=st.session_state.temp.get("designer", ""))
        with col2:
            in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.temp.get("prezzo", 0) or 0))
            in_pes = st.number_input("Peso (g)", value=float(st.session_state.temp.get("peso", 0) or 0))
            mat_ia = st.session_state.temp.get("materiale", "Argento 925")
            in_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Oro", "Pietra", "Ambra"], 
                                  index=0 if "Argento" in str(mat_ia) else 1)
        
        in_desc = st.text_area("Descrizione (Significato)", value=st.session_state.temp.get("descrizione", ""), height=150)
        in_foto = st.file_uploader("📸 Carica Foto", type=['jpg', 'png', 'jpeg'])
        
        if st.form_submit_button("💾 SALVA DEFINITIVAMENTE"):
            if in_sku and in_nome:
                fname = ""
                if in_foto:
                    fname = f"mie_immagini/{in_sku.replace('/', '_')}.jpg"
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                conn.execute("INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) VALUES (?,?,?,?,?,?,?,?)",
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_pes, in_desc, fname))
                conn.commit()
                st.success("Salvato correttamente!")
                st.balloons()

elif menu == "📖 La Mia Collezione":
    st.title("📖 Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if row['foto_path']:
                    st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
            with c2:
                st.write(f"**Peso:** {row['peso']}g | **Materiale:** {row['materiale']}")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup Cloud":
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Backup", f, "backup_beads.db")
