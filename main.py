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

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO TECNICO CON SIGNIFICATI REALI E MATERIALI CORRETTI ---
DIZIONARIO_AIUTO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro", 
        "prezzo": 85.0,
        "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw106f239f/images/TAGPE-00012.jpg",
        "descrizione": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero. Per te che hai un messaggio da cantare e lo trasmetti con grande intensità."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw789e456/images/TAGBE-10052.jpg",
        "descrizione": "I tre simboli classici: la Croce per la Fede, l'Ancora per la Speranza e il Cuore per la Carità. Un bead che racchiude i valori fondamentali che ci guidano nel cammino della vita."
    }
}

LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Aggiungi Nuovo", "💾 Backup Cloud"])

if menu == "➕ Aggiungi Nuovo":
    st.title("➕ Acquisizione con Significato e Anteprima")
    
    cerca = st.text_input("🔍 Digita il nome (es. balena) e premi INVIO").lower().strip()
    
    # Dati iniziali
    info = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "desc": "", "img_url": ""}
    
    # Ricerca precisa nel dizionario
    if cerca:
        for k, v in DIZIONARIO_AIUTO.items():
            if k in cerca:
                info = {
                    "sku": v["sku"], "nome": v["nome"], "designer": v["designer"],
                    "mat": v["materiale"], "prezzo": v["prezzo"], "desc": v["descrizione"],
                    "img_url": v["img_url"]
                }
                break

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        new_sku = st.text_input("SKU Tecnico", value=info["sku"])
        new_nome = st.text_input("Nome Bead", value=info["nome"])
        new_des = st.text_input("Designer", value=info["designer"])
    with col2:
        new_pre = st.number_input("Prezzo (€)", value=float(info["prezzo"]), step=1.0)
        # FORZATURA MATERIALE: Calcolo indice dinamico dalla lista ufficiale
        try:
            m_index = LISTA_MATERIALI.index(info["mat"])
        except ValueError:
            m_index = 0
        new_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=m_index)

    # --- CATTURA E ANTEPRIMA IMMAGINE ---
    st.write("### 📸 Anteprima Immagine")
    foto_da_salvare = None
    
    if info["img_url"]:
        try:
            response = requests.get(info["img_url"], timeout=10)
            foto_da_salvare = Image.open(BytesIO(response.content))
            st.image(foto_da_salvare, caption=f"Anteprima ufficiale per {info['nome']}", width=250)
            st.success("✅ Immagine acquisita correttamente. Premendo Salva verrà memorizzata nel DB.")
        except:
            st.error("⚠️ Impossibile caricare l'anteprima dal web. Controlla la connessione.")

    attiva_cam = st.checkbox("Preferisco scattare una foto con iPad o caricare file locale")
    if attiva_cam:
        uploaded = st.file_uploader("Carica o Scatta", type=['jpg', 'jpeg', 'png'])
        if uploaded: 
            foto_da_salvare = Image.open(uploaded)
            st.image(foto_da_salvare, caption="Foto personalizzata caricata", width=250)

    new_descrizione = st.text_area("Descrizione (Significato del Bead)", value=info["desc"], height=150)

    if st.button("💾 SALVA NEL MIO DATABASE PERSONALE"):
        if new_sku and new_nome:
            nome_file = f"{new_sku.replace('/', '_')}.jpg"
            percorso_assoluto = os.path.join(BASE_DIR, IMG_FOLDER, nome_file)
            percorso_db = os.path.join('mie_immagini', nome_file)
            
            if foto_da_salvare:
                foto_da_salvare.convert('RGB').save(percorso_assoluto, "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (new_sku, new_nome, new_des, new_mat, new_pre, new_descrizione, percorso_db))
            conn.commit()
            st.success(f"✅ {new_nome} salvato con successo!")
            st.balloons()
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
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup Cloud":
    st.header("💾 Backup Manuale")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Esporta Archivio (.db)", f, "my_beads_backup.db")
