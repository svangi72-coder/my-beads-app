import streamlit as st
import sqlite3
import pandas as pd
import os
import json
from PIL import Image
import google.generativeai as genai

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_v3.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Collector", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE IA (VERSIONE STABILE) ---
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # Usiamo il modello stabile senza suffissi beta
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("ERRORE: API Key non trovata nei Secrets di Streamlit.")
    model = None

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

# --- 4. FUNZIONE IA (ROBUSTA) ---
def estrai_dati_ia(testo):
    if not model: return None
    
    prompt = f"""
    Analizza il testo e restituisci SOLO un oggetto JSON con queste chiavi:
    "sku", "nome", "designer", "materiale", "prezzo", "peso", "descrizione".
    Usa 0 per i numeri mancanti.
    Testo: {testo}
    """
    try:
        # Chiamata standard senza parametri di versione espliciti
        response = model.generate_content(prompt)
        testo_risposta = response.text.strip()
        
        # Pulizia per estrarre il JSON puro
        if "```json" in testo_risposta:
            testo_risposta = testo_risposta.split("```json")[1].split("```")[0]
        elif "```" in testo_risposta:
            testo_risposta = testo_risposta.split("```")[1].split("```")[0]
            
        return json.loads(testo_risposta)
    except Exception as e:
        st.error(f"Nota: Se vedi ancora 404, prova a cambiare il nome modello in 'gemini-1.5-flash-latest' nel codice.")
        st.error(f"Dettaglio Errore: {e}")
        return None

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("Navigazione", ["✨ Acquisizione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Acquisizione AI":
    st.title("✨ Analisi Intelligente Google")
    
    testo_web = st.text_area("Incolla qui la descrizione del sito:", height=150)
    
    if 'dati_ai' not in st.session_state:
        st.session_state.dati_ai = {"sku": "", "nome": "", "designer": "", "materiale": "Vetro", "prezzo": 0.0, "peso": 0.0, "descrizione": ""}

    if st.button("🤖 Estrai Dati"):
        if testo_web:
            risultato = estrai_dati_ia(testo_web)
            if risultato:
                st.session_state.dati_ai = risultato
                st.success("Dati estratti!")
        else:
            st.warning("Incolla un testo prima.")

    st.divider()

    with st.form("salvataggio"):
        c1, c2 = st.columns(2)
        with c1:
            sku = st.text_input("SKU", value=st.session_state.dati_ai.get("sku", ""))
            nome = st.text_input("Nome", value=st.session_state.dati_ai.get("nome", ""))
            des = st.text_input("Designer", value=st.session_state.dati_ai.get("designer", ""))
        with c2:
            pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_ai.get("prezzo", 0)))
            pes = st.number_input("Peso (g)", value=float(st.session_state.dati_ai.get("peso", 0)))
            mat_ia = st.session_state.dati_ai.get("materiale", "Vetro")
            idx = LISTA_MATERIALI.index(mat_ia) if mat_ia in LISTA_MATERIALI else 0
            mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx)
        
        desc = st.text_area("Descrizione", value=st.session_state.dati_ai.get("descrizione", ""))
        foto = st.file_uploader("Carica Foto", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("💾 SALVA NEL DB"):
            if sku and nome:
                path_f = ""
                if foto:
                    fname = f"mie_immagini/{sku.replace('/', '_')}.jpg"
                    Image.open(foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    path_f = fname
                
                conn.execute("INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) VALUES (?,?,?,?,?,?,?,?)",
                             (sku, nome, des, mat, pre, pes, desc, path_f))
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
                st.write(f"**Materiale:** {row['materiale']} | **Peso:** {row['peso']}g")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.title("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database", f, "backup_beads.db")
