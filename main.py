import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image
import io

# --- 1. CONFIGURAZIONE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal", page_icon="💍", layout="wide")

# --- 2. GESTIONE DATABASE LOCALE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome_it TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, desc_it TEXT, 
                  img_filename TEXT, fuori_produzione INTEGER)''')
    return conn

conn = init_db()

# --- 3. DIZIONARIO TECNICO (Per aiutarti nell'inserimento) ---
DIZIONARIO = {
    "balena": {"sku": "TAGPE-00012", "nome": "Il Canto della Balena", "designer": "Morten Pol Engell Nørregård", "mat": "Vetro", "prezzo": 85.0, "note": "Megattera con balenottero."},
    "fede": {"sku": "TAGBE-10052", "nome": "Fede, Speranza e Carità", "designer": "Søren Nielsen", "mat": "Argento 925", "prezzo": 45.0, "note": "Croce, Ancora, Cuore."}
}

# --- 4. MENU LATERALE ---
menu = st.sidebar.radio("Menu", ["💎 La Mia Collezione", "🌐 Aggiungi Bead", "💾 Backup e Sicurezza"])

# --- SEZIONE BACKUP (La tua richiesta) ---
if menu == "💾 Backup e Sicurezza":
    st.header("💾 Gestione Dati Personali")
    st.info("Da qui puoi scaricare il tuo database per salvarlo su iCloud o Google Drive.")
    
    # ESPORTAZIONE (Backup)
    with open(DB_PATH, "rb") as f:
        st.download_button(
            label="📤 Scarica Backup Database (.db)",
            data=f,
            file_name="mio_archivio_beads.db",
            mime="application/x-sqlite3"
        )
    
    st.divider()
    
    # IMPORTAZIONE (Ripristino)
    st.subheader("📥 Ripristina Backup")
    uploaded_db = st.file_uploader("Carica il tuo file .db salvato in precedenza", type="db")
    if uploaded_db is not None:
        with open(DB_PATH, "wb") as f:
            f.write(uploaded_db.getbuffer())
        st.success("Database ripristinato con successo! Riavvia l'app.")

# --- SEZIONE AGGIUNGI (Con Foto iPad) ---
elif menu == "🌐 Aggiungi Bead":
    st.header("🌐 Nuova Acquisizione")
    search = st.text_input("Cerca nome per auto-completare", key="search").lower()
    info = DIZIONARIO.get(search, {"sku":"", "nome":search.capitalize(), "designer":"", "mat":"Argento 925", "prezzo":0.0, "note":""})
    
    with st.form("acq_form"):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU", value=info['sku'])
            nome = st.text_input("Nome", value=info['nome'])
            designer = st.text_input("Designer", value=info['designer'])
        with col2:
            prezzo = st.number_input("Prezzo (€)", value=info['prezzo'])
            materiale = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"], index=0 if info['mat']=="Argento 925" else 1)
            foto = st.camera_input("Scatta foto col tuo iPad") # Fotocamera iPad
            
        note = st.text_area("Note", value=info['note'])
        
        if st.form_submit_button("💾 SALVA NEL MIO DB"):
            fname = f"immagini/{sku}.jpg" if sku else "temp.jpg"
            if foto:
                Image.open(foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
            
            conn.execute("INSERT INTO charms (sku, nome_it, designer, materiale, prezzo, desc_it, img_filename) VALUES (?,?,?,?,?,?,?)",
                         (sku, nome, designer, materiale, prezzo, note, fname))
            conn.commit()
            st.success("Salvato localmente!")

# --- SEZIONE CATALOGO ---
elif menu == "💎 La Mia Collezione":
    st.header("💎 I Miei Beads")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome_it']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                path = os.path.join(BASE_DIR, row['img_filename'])
                if os.path.exists(path): st.image(path)
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                st.write(f"**Note:** {row['desc_it']}")
                if st.button("Elimina", key=row['id']):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
