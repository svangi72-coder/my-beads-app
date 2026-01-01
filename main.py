import streamlit as st
import sqlite3
import pandas as pd
import os
import json
from PIL import Image
import requests
from io import BytesIO
import google.generativeai as genai

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Collector", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE IA (MODIFICATA PER RISOLVERE ERRORE 404) ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # Cambiato da 'gemini-pro' a 'gemini-1.5-flash'
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("ERRORE: API Key di Google AI non trovata nei Secrets.")
    model = None

# --- 3. DATABASE (Include campo PESO) ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, peso REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()
LISTA_MATERIALI = ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame", "Perla"]

# --- 4. FUNZIONE IA AGGIORNATA ---
def estrai_dati_con_ia(testo_da_analizzare):
    if not model: return None
    
    prompt = f"""
    Analizza il testo seguente su un gioiello Trollbeads ed estrai i dati in formato JSON puro.
    Usa queste chiavi: "sku", "nome", "designer", "materiale", "prezzo", "peso", "descrizione".
    REGOLE: 
    1. Prezzo e Peso devono essere numeri (usa 0 se non trovati). 
    2. Se il materiale contiene 'Vetro', usa 'Vetro'. Se contiene 'Argento', usa 'Argento 925'.
    3. Descrizione deve essere il significato completo.
    
    Testo: {testo_da_analizzare}
    """
    try:
        response = model.generate_content(prompt)
        # Pulizia per sicurezza nel caso l'IA risponda con markdown ```json
        json_clean = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_clean)
    except Exception as e:
        st.error(f"Errore tecnico IA: {e}")
        return None

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("Navigazione", ["✨ Acquisizione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Acquisizione AI":
    st.title("✨ Analisi Intelligente Google AI")
    
    testo_input = st.text_area("Incolla qui la descrizione copiata dal web:", height=150, placeholder="Es: Il Canto della Balena... TAGPE-00012... Designer Morten Pol Engell Nørregård...")
    
    # Inizializza session state per i dati
    if 'dati_bead' not in st.session_state:
        st.session_state.dati_bead = {"sku": "", "nome": "", "designer": "", "materiale": "Vetro", "prezzo": 0.0, "peso": 0.0, "descrizione": ""}

    if st.button("🤖 Estrai Dati e Compila Form"):
        if testo_input:
            risultato = estrai_dati_con_ia(testo_input)
            if risultato:
                st.session_state.dati_bead = risultato
                st.success("Dati estratti con successo!")
        else:
            st.warning("Incolla un testo prima di procedere.")

    st.divider()

    # Form con i dati pronti
    with st.form("form_finale"):
        c1, c2 = st.columns(2)
        with c1:
            in_sku = st.text_input("SKU Tecnico", value=st.session_state.dati_bead.get("sku", ""))
            in_nome = st.text_input("Nome Ufficiale", value=st.session_state.dati_bead.get("nome", ""))
            in_des = st.text_input("Designer", value=st.session_state.dati_bead.get("designer", ""))
        with c2:
            in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_bead.get("prezzo", 0)))
            in_peso = st.number_input("Peso (g)", value=float(st.session_state.dati_bead.get("peso", 0)))
            try:
                idx_m = LISTA_MATERIALI.index(st.session_state.dati_bead.get("materiale", "Vetro"))
            except:
                idx_m = 0
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
        
        in_desc = st.text_area("Descrizione (Significato)", value=st.session_state.dati_bead.get("descrizione", ""), height=100)
        in_foto = st.file_uploader("📸 Carica la foto (salvata da Safari)", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("💾 SALVA NELL'ARCHIVIO PERSONALE"):
            if in_sku and in_nome:
                path_f = ""
                if in_foto:
                    fname = f"mie_immagini/{in_sku.replace('/', '_')}.jpg"
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    path_f = fname
                
                conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) 
                                VALUES (?,?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_peso, in_desc, path_f))
                conn.commit()
                st.success(f"Bead '{in_nome}' salvato correttamente!")
                st.balloons()
            else:
                st.error("Mancano SKU o Nome!")

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
                st.write(f"**Materiale:** {row['materiale']} | **Peso:** {row['peso']}g")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.title("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database", f, "backup_beads.db")
