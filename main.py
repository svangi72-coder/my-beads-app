import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURAZIONE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Auto-Capture", page_icon="🌐", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. FUNZIONE DI RICERCA WEB AUTOMATIZZATA ---
def genera_link_ricerca(query):
    # Link mirati per estrarre dati tecnici
    google_img = f"https://www.google.it/search?q=trollbeads+{query.replace(' ', '+')}&tbm=isch"
    troll_site = f"https://www.google.it/search?q=site:trollbeads.com+{query.replace(' ', '+')}"
    return google_img, troll_site

# --- 4. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["🔍 Ricerca & Cattura Web", "📖 Mia Collezione", "💾 Backup"])

if menu == "🔍 Ricerca & Cattura Web":
    st.title("🌐 Centro di Cattura Dati Web")
    
    # STEP 1: RICERCA
    query = st.text_input("💎 Inserisci Nome o SKU per avviare la ricerca automatica", placeholder="Es: Il canto della balena o TAGPE-00012")
    
    if query:
        link_img, link_info = genera_link_ricerca(query)
        
        st.markdown(f"### 🤖 Azioni per {query.capitalize()}:")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.link_button("📸 Trova Foto Ufficiale", link_img)
        with col_l2:
            st.link_button("📝 Trova Dati Tecnici (SKU/Designer)", link_info)
            
        st.divider()
        
        # STEP 2: ACQUISIZIONE AUTOMATIZZATA TRAMITE URL
        st.subheader("🔗 Acquisizione tramite URL Foto")
        st.write("Copia l'indirizzo dell'immagine (tasto destro -> copia indirizzo immagine) e incollalo qui:")
        
        url_foto = st.text_input("URL Immagine Web", placeholder="https://www.trollbeads.com/images/...")
        
        foto_catturata = None
        if url_foto:
            try:
                res = requests.get(url_foto, timeout=10)
                foto_catturata = Image.open(BytesIO(res.content))
                st.image(foto_catturata, caption="Anteprima Catturata dal Web", width=250)
                st.success("✅ Foto agganciata! Compila i dati tecnici qui sotto per salvare tutto.")
            except:
                st.error("⚠️ Non riesco a leggere questa immagine. Prova un altro link o usa la fotocamera.")

        # STEP 3: SCHEDA TECNICA
        with st.form("form_acquisizione"):
            c1, c2 = st.columns(2)
            with c1:
                in_sku = st.text_input("SKU", value=query if "-" in query else "")
                in_nome = st.text_input("Nome", value=query if "-" not in query else "")
                in_des = st.text_input("Designer")
            with c2:
                in_pre = st.number_input("Prezzo (€)", step=1.0)
                in_mat = st.selectbox("Materiale", ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra"])
            
            in_desc = st.text_area("Descrizione (Significato)")
            
            if st.form_submit_button("💾 SALVA DEFINITIVAMENTE NEL DB LOCALE"):
                if in_sku and in_nome:
                    # Salvataggio Fisico Foto
                    nome_file = f"{in_sku.replace('/', '_')}.jpg"
                    percorso_rel = os.path.join('mie_immagini', nome_file)
                    percorso_abs = os.path.join(BASE_DIR, percorso_rel)
                    
                    if foto_catturata:
                        foto_catturata.convert('RGB').save(percorso_abs, "JPEG")
                    
                    conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                                    VALUES (?,?,?,?,?,?,?)''', 
                                 (in_sku, in_nome, in_des, in_mat, in_pre, in_desc, percorso_rel))
                    conn.commit()
                    st.success(f"✅ {in_nome} memorizzato con successo nella cartella locale!")
                else:
                    st.error("Inserisci SKU e Nome per completare il salvataggio.")

elif menu == "📖 Mia Collezione":
    st.title("💎 Archivio Locale")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                p = os.path.join(BASE_DIR, row['foto_path'])
                if os.path.exists(p): st.image(p)
            with c2:
                st.write(f"**Materiale:** {row['materiale']} | **Designer:** {row['designer']}")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("🗑️ Elimina", key=row['id']):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.title("💾 Esporta Database")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Backup (.db)", f, "my_beads.db")
