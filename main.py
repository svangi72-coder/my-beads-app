import streamlit as st
import sqlite3
import pandas as pd
import os
import json
import requests
from PIL import Image

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads_v5.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Pro", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE IA (CHIAMATA DIRETTA CORRETTA) ---
API_KEY = st.secrets.get("GOOGLE_API_KEY")

def estrai_dati_ia_diretto(testo):
    if not API_KEY:
        st.error("API Key non trovata nei Secrets.")
        return None
    
    # URL ufficiale v1
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    prompt = f"""
    Analizza il testo del gioiello ed estrai i dati in formato JSON. 
    Usa solo queste chiavi: "sku", "nome", "designer", "materiale", "prezzo", "peso", "descrizione".
    REGOLE: 
    - Prezzo e Peso devono essere numeri puri.
    - Se non sai il materiale, usa "Argento 925".
    - Descrizione deve essere il significato del bead.
    Testo: {testo}
    """
    
    # Struttura Payload corretta per Gemini v1
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "response_mime_type": "application/json",
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        
        if response.status_code != 200:
            st.error(f"Errore Google (Stato {response.status_code}): {response.text}")
            return None
            
        risultato = response.json()
        
        # Navigazione sicura nel JSON di risposta
        if 'candidates' in risultato and len(risultato['candidates']) > 0:
            content_text = risultato['candidates'][0]['content']['parts'][0]['text']
            return json.loads(content_text)
        else:
            st.error("L'IA ha risposto ma non ha trovato contenuti.")
            return None
            
    except Exception as e:
        st.error(f"Errore di connessione: {e}")
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
st.sidebar.title("💎 MyBeads AI")
menu = st.sidebar.radio("Menu", ["✨ Estrazione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Estrazione AI":
    st.title("✨ Analisi Automatica con Google AI")
    st.write("Incolla qui sotto la descrizione copiata da Trollbeads o altri cataloghi.")
    
    testo_web = st.text_area("Testo da analizzare", height=200, placeholder="Copia qui testo e dettagli tecnici...")
    
    if 'dati_ai' not in st.session_state:
        st.session_state.dati_ai = {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "peso": 0.0, "descrizione": ""}

    if st.button("🤖 Avvia Analisi Intelligente"):
        if testo_web:
            with st.spinner("L'IA sta leggendo i dati..."):
                risultato = estrai_dati_ia_diretto(testo_web)
                if risultato:
                    st.session_state.dati_ai = risultato
                    st.success("Dati estratti con successo! Verifica la scheda qui sotto.")
        else:
            st.warning("Inserisci del testo da analizzare.")

    st.divider()

    # SCHEDA DI VERIFICA E SALVATAGGIO
    with st.form("scheda_salvataggio"):
        st.subheader("📝 Verifica Dati ed Inserimento Foto")
        c1, c2 = st.columns(2)
        with c1:
            in_sku = st.text_input("Codice SKU", value=st.session_state.dati_ai.get("sku", ""))
            in_nome = st.text_input("Nome Bead", value=st.session_state.dati_ai.get("nome", ""))
            in_des = st.text_input("Designer", value=st.session_state.dati_ai.get("designer", ""))
        with c2:
            in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_ai.get("prezzo", 0) or 0))
            in_pes = st.number_input("Peso (g)", value=float(st.session_state.dati_ai.get("peso", 0) or 0))
            mat_ia = st.session_state.dati_ai.get("materiale", "Argento 925")
            idx = LISTA_MATERIALI.index(mat_ia) if mat_ia in LISTA_MATERIALI else 1
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx)
        
        in_desc = st.text_area("Descrizione (Significato)", value=st.session_state.dati_ai.get("descrizione", ""), height=150)
        in_foto = st.file_uploader("📸 Carica la foto salvata", type=['jpg', 'jpeg', 'png'])
        
        if st.form_submit_button("💾 SALVA DEFINITIVAMENTE NEL DATABASE"):
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
                st.success(f"Bead '{in_nome}' salvato correttamente!")
                st.balloons()
            else:
                st.error("SKU e Nome sono obbligatori per il salvataggio.")

elif menu == "💍 Mia Collezione":
    st.title("💍 La Mia Collezione")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if df.empty:
        st.info("La collezione è vuota.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if row['foto_path']:
                        st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
                with c2:
                    st.write(f"**Materiale:** {row['materiale']} | **Peso:** {row['peso']}g")
                    st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                    st.info(f"**Descrizione:** {row['descrizione']}")
                    if st.button("Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Manuale")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Esporta Database (.db)", f, "my_beads_archive.db")
