import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
from PIL import Image
from io import BytesIO
import webbrowser

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO INTERNO (Per i pezzi già noti) ---
DIZIONARIO_AIUTO = {
    "balena": {
        "sku": "TAGPE-00012", "nome": "Il Canto della Balena", "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro", "prezzo": 85.0, "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw106f239f/images/TAGPE-00012.jpg",
        "descrizione": "La megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero. Per chi ha un messaggio intenso da cantare."
    },
    "fede": {
        "sku": "TAGBE-10052", "nome": "Fede, Speranza e Carità", "designer": "Søren Nielsen",
        "materiale": "Argento 925", "prezzo": 45.0, "img_url": "https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw789e456/images/TAGBE-10052.jpg",
        "descrizione": "Croce, Ancora e Cuore: i valori fondamentali che guidano il cammino della vita."
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
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Ricerca & Acquisizione Web", "💾 Backup Cloud"])

if menu == "➕ Ricerca & Acquisizione Web":
    st.title("🌐 Ricerca Intelligente sul Web")
    
    # INPUT DI RICERCA
    cerca = st.text_input("🔍 Inserisci Nome o SKU del Bead (es. 'ritmo del tamburo' o 'TAGBE-00001')").lower().strip()
    
    # Logica di ricerca: prima interna, poi esterna
    info = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "desc": "", "img_url": ""}
    trovato_interno = False

    if cerca:
        # 1. Verifica interna
        for k, v in DIZIONARIO_AIUTO.items():
            if k in cerca:
                info = {"sku": v["sku"], "nome": v["nome"], "designer": v["designer"], "mat": v["materiale"], "prezzo": v["prezzo"], "desc": v["descrizione"], "img_url": v["img_url"]}
                trovato_interno = True
                break
        
        # 2. Strumenti di Ricerca Web (Se non trovato o per approfondire)
        st.subheader("🛠️ Strumenti di Recupero Dati")
        col_w1, col_w2, col_w3 = st.columns(3)
        query_web = f"trollbeads {cerca}".replace(" ", "+")
        
        with col_w1:
            st.markdown(f"[📸 Foto Ufficiali (Google)]({'https://www.google.it/search?q=' + query_web + '&tbm=isch'})")
        with col_w2:
            st.markdown(f"[📖 Significato e Storia]({'https://www.google.it/search?q=' + query_web + '+significato+storia'})")
        with col_w3:
            st.markdown(f"[💰 Valore di Mercato (eBay)]({'https://www.ebay.it/sch/i.html?_nkw=' + query_web})")

    st.divider()
    
    # SCHEDA DI ACQUISIZIONE
    with st.form("form_web_acq"):
        st.subheader("📝 Compila la Scheda con i dati trovati")
        c1, c2 = st.columns(2)
        with c1:
            new_sku = st.text_input("SKU Tecnico (trovato sul web)", value=info["sku"])
            new_nome = st.text_input("Nome Ufficiale", value=info["nome"])
            new_des = st.text_input("Designer", value=info["designer"])
        with c2:
            new_pre = st.number_input("Prezzo (€)", value=float(info["prezzo"]))
            try: m_idx = LISTA_MATERIALI.index(info["mat"])
            except: m_idx = 0
            new_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=m_idx)
        
        new_desc = st.text_area("Descrizione e Significato (Copia/Incolla dal web)", value=info["desc"], height=150)
        
        st.write("### 📸 Immagine")
        # Se abbiamo un URL (da dizionario), proviamo a pre-caricare
        if info["img_url"]:
            try:
                res = requests.get(info["img_url"], timeout=5)
                st.image(Image.open(BytesIO(res.content)), width=200, caption="Anteprima automatica")
            except: pass
            
        new_foto = st.file_uploader("Carica o Scatta la foto trovata sul web", type=['jpg','jpeg','png'])
        
        if st.form_submit_button("💾 SALVA DEFINITIVAMENTE NEL MIO DB"):
            if new_sku and new_nome:
                nome_f = f"{new_sku.replace('/', '_')}.jpg"
                path_a = os.path.join(BASE_DIR, IMG_FOLDER, nome_f)
                path_db = os.path.join('mie_immagini', nome_f)
                
                if new_foto:
                    Image.open(new_foto).convert('RGB').save(path_a, "JPEG")
                
                conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                                VALUES (?,?,?,?,?,?,?)''', 
                             (new_sku, new_nome, new_des, new_mat, new_pre, new_desc, path_db))
                conn.commit()
                st.success(f"Bead '{new_nome}' salvato con successo nel tuo archivio!")
            else:
                st.error("Inserisci SKU e Nome per procedere.")

elif menu == "💎 La Mia Collezione":
    st.title("💎 La Mia Collezione")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']:.2f}")
            st.info(f"**Significato:** {row['descrizione']}")
            p = os.path.join(BASE_DIR, row['foto_path'])
            if os.path.exists(p): st.image(p, width=300)
            if st.button("Elimina", key=f"d_{row['id']}"):
                conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup Cloud":
    st.header("💾 Backup Manuale")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Esporta Database (.db)", f, "my_beads_archive.db")
