import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_v4.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Pro", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE IA (CHIAMATA DIRETTA) ---
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def estrai_dati_ia_diretto(testo):
    if not API_KEY:
        st.error("API Key non trovata nei Secrets.")
        return None
    
    # URL della API Stabile (v1) invece della Beta
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Analizza il testo ed estrai i dati in formato JSON puro.
    Usa queste chiavi: "sku", "nome", "designer", "materiale", "prezzo", "peso", "descrizione".
    REGOLE: Prezzo/Peso sono numeri (0 se ignoti). Materiale deve essere uno tra: Vetro, Argento 925, Oro, Pietra, Ambra.
    Testo: {testo}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        risultato = response.json()
        
        # Estrazione del testo JSON dalla risposta di Google
        json_text = risultato['candidates'][0]['content']['parts'][0]['text']
        return json.loads(json_text)
    except Exception as e:
        st.error(f"Errore nella comunicazione con Google AI: {e}")
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
LISTA_MATERIALI = ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame", "Perla"]

# --- 4. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["✨ Acquisizione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Acquisizione AI":
    st.title("✨ Acquisizione Intelligente (v1 Stable)")
    
    testo_web = st.text_area("Incolla qui la descrizione del bead:", height=150)
    
    if 'dati_ai' not in st.session_state:
        st.session_state.dati_ai = {"sku": "", "nome": "", "designer": "", "materiale": "Vetro", "prezzo": 0.0, "peso": 0.0, "descrizione": ""}

    if st.button("🤖 Analizza con IA"):
        if testo_web:
            risultato = estrai_dati_ia_diretto(testo_web)
            if risultato:
                st.session_state.dati_ai = risultato
                st.success("Dati estratti con successo!")
        else:
            st.warning("Incolla un testo.")

    st.divider()

    with st.form("salvataggio"):
        c1, c2 = st.columns(2)
        with c1:
            in_sku = st.text_input("SKU", value=st.session_state.dati_ai.get("sku", ""))
            in_nome = st.text_input("Nome", value=st.session_state.dati_ai.get("nome", ""))
            in_des = st.text_input("Designer", value=st.session_state.dati_ai.get("designer", ""))
        with c2:
            in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_ai.get("prezzo", 0)))
            in_pes = st.number_input("Peso (g)", value=float(st.session_state.dati_ai.get("peso", 0)))
            mat_ia = st.session_state.dati_ai.get("materiale", "Vetro")
            idx = LISTA_MATERIALI.index(mat_ia) if mat_ia in LISTA_MATERIALI else 0
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx)
        
        in_desc = st.text_area("Descrizione", value=st.session_state.dati_ai.get("descrizione", ""), height=100)
        in_foto = st.file_uploader("📸 Foto", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("💾 SALVA"):
            if in_sku and in_nome:
                fname = f"mie_immagini/{in_sku.replace('/', '_')}.jpg"
                path_f = ""
                if in_foto:
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    path_f = fname
                
                conn.execute("INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) VALUES (?,?,?,?,?,?,?,?)",
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_pes, in_desc, path_f))
                conn.commit()
                st.success("Salvato!")
            else:
                st.error("SKU e Nome obbligatori.")

elif menu == "💍 Mia Collezione":
    st.title("💍 Il Mio Archivio")
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

elif menu == "💾 Backup":
    st.title("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database", f, "backup.db")
