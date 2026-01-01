import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_v7.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Pro", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE IA (VERSIONE V1 STABILE) ---
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def estrai_dati_ia_diretto(testo):
    if not API_KEY:
        st.error("API Key non trovata nei Secrets.")
        return None
    
    # URL CAMBIATO DA v1beta A v1 (STABILE)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    prompt = f"""
    Analizza il testo del gioiello ed estrai i dati nel seguente formato JSON:
    {{
      "sku": "codice",
      "nome": "nome",
      "designer": "nome designer",
      "materiale": "Vetro o Argento 925 o Pietra",
      "prezzo": 0.0,
      "peso": 0.0,
      "descrizione": "significato completo"
    }}
    Restituisci SOLO il JSON puro, senza commenti o markdown.
    Testo: {testo}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        
        if response.status_code != 200:
            st.error(f"Errore Google ({response.status_code}): {response.text}")
            return None
            
        risultato = response.json()
        raw_text = risultato['candidates'][0]['content']['parts'][0]['text']
        
        # Pulizia manuale del testo
        clean_json = raw_text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
            
    except Exception as e:
        st.error(f"Errore analisi: {e}")
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
LISTA_MATERIALI = ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame", "Perla", "Altro"]

# --- 4. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["✨ Estrazione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Estrazione AI":
    st.title("✨ Acquisizione Intelligente (v1 Stable)")
    
    testo_web = st.text_area("Incolla qui la descrizione del bead:", height=200)
    
    if 'dati_ai' not in st.session_state:
        st.session_state.dati_ai = {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "peso": 0.0, "descrizione": ""}

    if st.button("🤖 Avvia Analisi"):
        if testo_web:
            with st.spinner("L'IA sta elaborando sulla versione stabile..."):
                risultato = estrai_dati_ia_diretto(testo_web)
                if risultato:
                    st.session_state.dati_ai = risultato
                    st.success("Dati pronti!")
        else:
            st.warning("Incolla del testo.")

    st.divider()

    with st.form("scheda"):
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("SKU", value=st.session_state.dati_ai.get("sku", ""))
            in_nome = st.text_input("Nome", value=st.session_state.dati_ai.get("nome", ""))
            in_des = st.text_input("Designer", value=st.session_state.dati_ai.get("designer", ""))
        with col2:
            in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_ai.get("prezzo", 0) or 0))
            in_pes = st.number_input("Peso (g)", value=float(st.session_state.dati_ai.get("peso", 0) or 0))
            mat_ia = st.session_state.dati_ai.get("materiale", "Argento 925")
            idx = LISTA_MATERIALI.index(mat_ia) if mat_ia in LISTA_MATERIALI else 1
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx)
        
        in_desc = st.text_area("Descrizione", value=st.session_state.dati_ai.get("descrizione", ""), height=150)
        in_foto = st.file_uploader("📸 Carica Foto", type=['jpg', 'png', 'jpeg'])
        
        if st.form_submit_button("💾 SALVA NEL DATABASE"):
            if in_sku and in_nome:
                nome_f = f"{in_sku.replace('/', '_')}.jpg"
                path_f = os.path.join(IMG_FOLDER, nome_f)
                if in_foto:
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, path_f), "JPEG")
                else:
                    path_f = ""
                
                conn.execute("INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) VALUES (?,?,?,?,?,?,?,?)",
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_pes, in_desc, path_f))
                conn.commit()
                st.success("Salvato correttamente!")
                st.balloons()

elif menu == "💍 Mia Collezione":
    st.title("💍 Archivio Personale")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if row['foto_path']:
                    st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
            with c2:
                st.write(f"**Peso:** {row['peso']}g | **Prezzo:** €{row['prezzo']}")
                st.write(f"**Materiale:** {row['materiale']} | **Designer:** {row['designer']}")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Esporta DB", f, "archivio_beads.db")
