import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. SETUP AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')
if not os.path.exists(IMG_FOLDER): 
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💍", layout="wide")

# --- 2. DIZIONARIO INTELLIGENTE ---
DIZIONARIO = {
    "balena": {
        "sku": "TAGPE-00012", 
        "nome": "Il Canto della Balena", 
        "designer": "Morten Pol Engell Nørregård", 
        "mat": "Vetro", 
        "prezzo": 85.0, 
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni."
    },
    "fede": {
        "sku": "TAGBE-10052", 
        "nome": "Fede, Speranza e Carità", 
        "designer": "Søren Nielsen", 
        "mat": "Argento 925", 
        "prezzo": 45.0, 
        "note": "Classico simbolo con croce, ancora e cuore."
    }
}
LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

# --- 3. INIZIALIZZAZIONE SESSION STATE (La "Memoria" dell'app) ---
if 'dati_ricerca' not in st.session_state:
    st.session_state.dati_ricerca = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 4. FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, 
                  nome_it TEXT, designer TEXT, materiale TEXT, prezzo REAL, 
                  desc_it TEXT, img_filename TEXT, fuori_produzione INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 5. NAVIGAZIONE ---
menu = st.sidebar.radio("Navigazione", ["📖 Collezione", "🌐 Acquisizione", "💾 Backup"])

if menu == "🌐 Acquisizione":
    st.header("🌐 Ricerca e Inserimento Garantito")
    
    # BARRA DI RICERCA
    cerca = st.text_input("🔍 Cerca Nome (es: balena) e premi INVIO sulla tastiera iPad")
    
    if cerca:
        chiave = cerca.lower().strip()
        trovato = False
        for k, v in DIZIONARIO.items():
            if k in chiave:
                st.session_state.dati_ricerca = v
                trovato = True
                break
        if not trovato:
            st.session_state.dati_ricerca = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

    st.divider()
    
    # CAMPI DI INSERIMENTO (Prendono i dati dalla memoria Session State)
    col1, col2 = st.columns(2)
    with col1:
        in_sku = st.text_input("SKU Tecnico", value=st.session_state.dati_ricerca['sku'])
        in_nome = st.text_input("Nome Ufficiale", value=st.session_state.dati_ricerca['nome'])
        in_des = st.text_input("Designer", value=st.session_state.dati_ricerca['designer'])
    with col2:
        in_pre = st.number_input("Prezzo (€)", value=float(st.session_state.dati_ricerca['prezzo']), step=1.0)
        idx_m = LISTA_MATERIALI.index(st.session_state.dati_ricerca['mat']) if st.session_state.dati_ricerca['mat'] in LISTA_MATERIALI else 0
        in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
        in_ret = st.checkbox("Retired (Fuori Produzione)")

    in_foto = st.camera_input("Scatta la foto")
    in_note = st.text_area("Note e Storia", value=st.session_state.dati_ricerca['note'])
    
    if st.button("📥 SALVA NEL DATABASE PERSONALE"):
        if in_sku and in_nome:
            fname = f"immagini/{in_sku.replace('/', '_')}.jpg"
            if in_foto:
                Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome_it, designer, materiale, prezzo, desc_it, img_filename, fuori_produzione) 
                            VALUES (?,?,?,?,?,?,?,?)''', 
                         (in_sku, in_nome, in_des, in_mat, in_pre, in_note, fname, 1 if in_ret else 0))
            conn.commit()
            st.success(f"Bead '{in_nome}' salvato!")
            # Reset memoria dopo il salvataggio
            st.session_state.dati_ricerca = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}
            st.rerun()

elif menu == "📖 Collezione":
    st.header("💍 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome_it']} ({row['sku']})"):
            st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
            img_p = os.path.join(BASE_DIR, row['img_filename'])
            if row['img_filename'] and os.path.exists(img_p):
                st.image(img_p, width=300)
            if st.button("Elimina", key=f"del_{row['id']}"):
                conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                conn.commit()
                st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database", f, "my_beads.db")
