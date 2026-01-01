import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal App", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO TECNICO POTENZIATO (Con URL Immagini) ---
# Qui inseriamo l'URL diretto dell'immagine ufficiale per "catturarla"
DIZIONARIO_AIUTO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro", 
        "prezzo": 85.0,
        "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw106f239f/images/TAGPE-00012.jpg",
        "note": "Megattera con balenottero."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw789e456/images/TAGBE-10052.jpg",
        "note": "Croce, Ancora e Cuore."
    }
}

LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, note TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Aggiungi Nuovo", "💾 Backup Cloud"])

if menu == "➕ Aggiungi Nuovo":
    st.title("➕ Inserimento Intelligente")
    
    cerca = st.text_input("🔍 Digita il nome e premi INVIO (es. balena)").lower().strip()
    
    # Reset dati
    info = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": "", "img_url": ""}
    
    # Logica di "Cattura" Dati e Materiale
    if cerca:
        for k, v in DIZIONARIO_AIUTO.items():
            if k in cerca:
                info = {
                    "sku": v["sku"], "nome": v["nome"], "designer": v["designer"],
                    "mat": v["materiale"], "prezzo": v["prezzo"], "note": v["note"],
                    "img_url": v["img_url"]
                }
                break

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        new_sku = st.text_input("SKU", value=info["sku"])
        new_nome = st.text_input("Nome", value=info["nome"])
        new_des = st.text_input("Designer", value=info["designer"])
    with col2:
        new_pre = st.number_input("Prezzo (€)", value=float(info["prezzo"]))
        # FORZATURA MATERIALE: Cerchiamo l'indice esatto per non sbagliare
        try:
            m_index = LISTA_MATERIALI.index(info["mat"])
        except:
            m_index = 0
        new_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=m_index)

    # --- CATTURA IMMAGINE ---
    st.write("### 📸 Gestione Immagine")
    foto_da_salvare = None
    
    if info["img_url"]:
        st.info("✨ Immagine ufficiale trovata!")
        try:
            response = requests.get(info["img_url"])
            foto_da_salvare = Image.open(BytesIO(response.content))
            st.image(foto_da_salvare, caption="Anteprima catturata dal web", width=200)
        except:
            st.warning("Impossibile caricare l'anteprima web automaticamente.")

    attiva_cam = st.checkbox("Preferisco usare la fotocamera iPad o caricare file")
    if attiva_cam:
        uploaded = st.file_uploader("Carica o Scatta", type=['jpg', 'jpeg', 'png'])
        if uploaded: foto_da_salvare = Image.open(uploaded)

    new_note = st.text_area("Note", value=info["note"])

    if st.button("💾 SALVA NEL MIO DATABASE"):
        if new_sku and new_nome:
            nome_file = f"{new_sku.replace('/', '_')}.jpg"
            percorso_assoluto = os.path.join(BASE_DIR, IMG_FOLDER, nome_file)
            percorso_db = os.path.join('mie_immagini', nome_file)
            
            if foto_da_salvare:
                foto_da_salvare.convert('RGB').save(percorso_assoluto, "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, note, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (new_sku, new_nome, new_des, new_mat, new_pre, new_note, percorso_db))
            conn.commit()
            st.success(f"✅ {new_nome} salvato con materiale {new_mat} e foto acquisita!")
        else:
            st.error("Inserisci SKU e Nome.")

elif menu == "💎 La Mia Collezione":
    st.title("💎 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                p = os.path.join(BASE_DIR, row['foto_path'])
                if os.path.exists(p): st.image(p, use_container_width=True)
            with c2:
                st.write(f"**Materiale:** {row['materiale']} | **Designer:** {row['designer']}")
                st.write(f"**Prezzo:** €{row['prezzo']} | **Note:** {row['note']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup Cloud":
    st.header("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_beads.db")
