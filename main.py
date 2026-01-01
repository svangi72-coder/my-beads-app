import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. SETUP AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Pro", page_icon="💍", layout="wide")

# --- 2. DIZIONARIO TECNICO ---
DIZIONARIO = {
    "balena": {"sku": "TAGPE-00012", "nome": "Il Canto della Balena", "designer": "Morten Pol Engell Nørregård", "mat": "Vetro", "prezzo": 85.0, "note": "Megattera con balenottero."},
    "fede": {"sku": "TAGBE-10052", "nome": "Fede, Speranza e Carità", "designer": "Søren Nielsen", "mat": "Argento 925", "prezzo": 45.0, "note": "Croce, Ancora, Cuore."}
}
LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra"]

# --- 3. FUNZIONI DB ---
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, 
                  nome_it TEXT, designer TEXT, materiale TEXT, prezzo REAL, 
                  desc_it TEXT, img_filename TEXT, fuori_produzione INTEGER)''')
    conn.commit()

init_db()

# --- 4. INTERFACCIA ---
menu = st.sidebar.radio("Navigazione", ["📖 Collezione", "🌐 Acquisizione", "💾 Backup"])

if menu == "🌐 Acquisizione":
    st.header("🌐 Ricerca e Inserimento")
    
    # Ricerca per nome (Fuori dal form per essere reattiva)
    cerca = st.text_input("🔍 Cerca Nome (es: balena) e premi INVIO").lower().strip()
    
    # Recupero dati dal dizionario
    info = DIZIONARIO.get(cerca, {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""})
    if cerca and info["sku"] == "": # Ricerca parziale
        for k, v in DIZIONARIO.items():
            if k in cerca: info = v; break

    # Modulo di inserimento
    with st.form("form_nuovo_bead", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("SKU Tecnico", value=info['sku'])
            in_nome = st.text_input("Nome Ufficiale", value=info['nome'])
            in_des = st.text_input("Designer", value=info['designer'])
        with col2:
            in_pre = st.number_input("Prezzo (€)", value=float(info['prezzo']))
            idx_m = LISTA_MATERIALI.index(info['mat']) if info['mat'] in LISTA_MATERIALI else 0
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
            in_foto = st.camera_input("Foto iPad") # Priorità a fotocamera iPad
            
        in_note = st.text_area("Note", value=info['note'])
        in_ret = st.checkbox("Retired")
        
        submit = st.form_submit_button("📥 SALVA NEL DATABASE")
        
        if submit:
            if in_sku and in_nome:
                conn = get_connection()
                fname = f"immagini/{in_sku}.jpg"
                if in_foto:
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, designer, materiale, prezzo, desc_it, img_filename, fuori_produzione) 
                                VALUES ('Trollbeads',?,?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_note, fname, 1 if in_ret else 0))
                conn.commit()
                st.success(f"Salvato: {in_nome}")
            else:
                st.error("Inserisci Nome e SKU!")

elif menu == "📖 Collezione":
    st.header("💍 Archivio Personale")
    # Filtri
    f_txt = st.text_input("Filtra per Nome o SKU")
    
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if f_txt:
        df = df[df['nome_it'].str.contains(f_txt, case=False) | df['sku'].str.contains(f_txt, case=False)]
    
    for _, row in df.iterrows():
        with st.expander(f"{row['nome_it']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if row['img_filename'] and os.path.exists(os.path.join(BASE_DIR, row['img_filename'])):
                    st.image(os.path.join(BASE_DIR, row['img_filename']))
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                st.write(f"**Note:** {row['desc_it']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Manuale")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "mio_backup.db")
