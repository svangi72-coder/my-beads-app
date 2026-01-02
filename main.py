import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# --- 1. SETUP AMBIENTE IPAD ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_finale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads iPad Pro", page_icon="💎", layout="wide")

# --- 2. LOGICA IA DIRETTA ---
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def chiama_ia_google(testo):
    if not API_KEY:
        return None
    
    # Usiamo l'endpoint più compatibile in assoluto
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    prompt = f"""
    Estrai dati dal testo e rispondi SOLO con un JSON. 
    Chiavi: sku, nome, designer, materiale, prezzo, peso, descrizione.
    Testo: {testo}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            testo_ia = res_json['candidates'][0]['content']['parts'][0]['text']
            # Pulizia per iPad (rimuove eventuali ```json)
            testo_ia = testo_ia.replace('```json', '').replace('```', '').strip()
            return json.loads(testo_ia)
    except:
        return None
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

# --- 4. INTERFACCIA TOUCH-FRIENDLY ---
st.sidebar.title("💎 MyBeads iPad")
menu = st.sidebar.radio("Vai a:", ["➕ Aggiungi con IA", "💍 La Mia Collezione", "💾 Backup"])

if menu == "➕ Aggiungi con IA":
    st.title("✨ Acquisizione Automatica")
    st.write("Copia la descrizione da Safari e incollala qui sotto.")
    
    testo_in = st.text_area("Testo del Bead", height=150)
    
    # Session state per non perdere i dati durante il refresh su iPad
    if 'temp_bead' not in st.session_state:
        st.session_state.temp_bead = {"sku":"", "nome":"", "designer":"", "materiale":"Argento 925", "prezzo":0.0, "peso":0.0, "descrizione":""}

    if st.button("🤖 ANALIZZA TESTO"):
        if testo_in:
            with st.spinner("L'IA sta lavorando..."):
                risultato = chiama_ia_google(testo_in)
                if risultato:
                    st.session_state.temp_bead = risultato
                    st.success("Dati estratti! Controlla e salva.")
                else:
                    st.error("L'IA non risponde. Controlla la chiave API nei Secrets o compila a mano.")
        else:
            st.warning("Incolla un testo prima!")

    st.divider()

    # Form di inserimento (Dati estratti o manuali)
    with st.form("form_bead"):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU", value=st.session_state.temp_bead.get("sku", ""))
            nome = st.text_input("Nome", value=st.session_state.temp_bead.get("nome", ""))
            des = st.text_input("Designer", value=st.session_state.temp_bead.get("designer", ""))
        with col2:
            pre = st.number_input("Prezzo (€)", value=float(st.session_state.temp_bead.get("prezzo", 0) or 0))
            pes = st.number_input("Peso (g)", value=float(st.session_state.temp_bead.get("peso", 0) or 0))
            mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Oro", "Pietra", "Ambra"], 
                               index=1 if "Vetro" in str(st.session_state.temp_bead.get("materiale", "")) else 0)
        
        desc = st.text_area("Descrizione", value=st.session_state.temp_bead.get("descrizione", ""), height=100)
        foto = st.file_uploader("📸 Foto (Libreria o Scatto)", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("💾 SALVA NEL TELEFONO"):
            if sku and nome:
                p_foto = ""
                if foto:
                    fname = f"mie_immagini/{sku.replace('/', '_')}.jpg"
                    Image.open(foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    p_foto = fname
                
                conn.execute("INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) VALUES (?,?,?,?,?,?,?,?)",
                             (sku, nome, des, mat, pre, pes, desc, p_foto))
                conn.commit()
                st.success(f"Bead {nome} salvato!")
                st.balloons()
            else:
                st.error("SKU e Nome sono obbligatori!")

elif menu == "💍 La Mia Collezione":
    st.title("💍 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if row['foto_path']:
                    st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
            with c2:
                st.write(f"**Materiale:** {row['materiale']} | **Peso:** {row['peso']}g")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Backup", f, "backup_beads.db")
