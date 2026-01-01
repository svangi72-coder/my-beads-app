import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image
import io

# --- 1. CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO TECNICO (Dati Corretti) ---
DIZIONARIO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro",
        "prezzo": 85.0,
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Classico simbolo con croce, ancora e cuore."
    }
}

LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

# --- 3. INIZIALIZZAZIONE DATABASE PERSONALE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome_it TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, desc_it TEXT, 
                  img_filename TEXT, fuori_produzione INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. FUNZIONE RICERCA NEL DIZIONARIO ---
def trova_info(testo):
    testo = testo.lower().strip()
    for chiave, dati in DIZIONARIO.items():
        if chiave in testo:
            return dati
    return {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["📖 Mia Collezione", "🌐 Ricerca e Acquisizione", "💾 Backup"])

if menu == "🌐 Ricerca e Acquisizione":
    st.header("🌐 Acquisizione Nuovi Dati")
    
    # Ricerca Scissa
    query = st.text_input("🔍 Cerca per Nome (es: balena)", help="Scrivi qui il nome per auto-compilare i dati ufficiali")
    info = trova_info(query)
    
    if query:
        st.markdown(f"### [🔗 Cerca foto di '{query}' su Google Immagini](https://www.google.it/search?q=trollbeads+{query.replace(' ', '+')}&tbm=isch)")

    with st.form("form_acquisizione"):
        st.subheader("📝 Dettagli Tecnici")
        c1, c2 = st.columns(2)
        with c1:
            in_sku = st.text_input("SKU Ufficiale", value=info['sku'])
            in_nome = st.text_input("Nome Bead", value=info['nome'] if info['nome'] else query.capitalize())
            in_des = st.text_input("Designer", value=info['designer'])
        with c2:
            in_pre = st.number_input("Prezzo (€)", value=info['prezzo'])
            idx_mat = LISTA_MATERIALI.index(info['materiale']) if info['materiale'] in LISTA_MATERIALI else 0
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_mat)
            in_stato = st.checkbox("Retired (Fuori Produzione)")
        
        st.write("**📷 Immagine**")
        foto_ipad = st.camera_input("Scatta foto col tuo iPad")
        in_note = st.text_area("Note e Storia", value=info['note'])
        
        if st.form_submit_button("📥 SALVA NEL MIO DATABASE"):
            if in_sku and in_nome:
                fname = f"immagini/{in_sku}.jpg"
                if foto_ipad:
                    Image.open(foto_ipad).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                
                conn.execute('''INSERT INTO charms (sku, nome_it, designer, materiale, prezzo, desc_it, img_filename, fuori_produzione) 
                                VALUES (?,?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_note, fname, 1 if in_stato else 0))
                conn.commit()
                st.success(f"Bead {in_nome} salvato!")
            else:
                st.error("Inserisci SKU e Nome per procedere.")

elif menu == "📖 Mia Collezione":
    st.header("📖 La Mia Collezione Personale")
    
    # Filtri di ricerca nel database
    with st.expander("🔍 Filtra i miei beads"):
        f_txt = st.text_input("Cerca per nome o SKU")
        f_mat = st.multiselect("Materiale", LISTA_MATERIALI)
    
    df = pd.read_sql("SELECT * FROM charms", conn)
    if f_txt:
        df = df[df['nome_it'].str.contains(f_txt, case=False) | df['sku'].str.contains(f_txt, case=False)]
    if f_mat:
        df = df[df['materiale'].isin(f_mat)]
        
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"### {row['nome_it']} ({row['sku']})")
            c1, c2 = st.columns([1, 2])
            with c1:
                path = os.path.join(BASE_DIR, row['img_filename'])
                if os.path.exists(path): st.image(path, use_container_width=True)
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']}")
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Note:** {row['desc_it']}")
                if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                    conn.commit(); st.rerun()
            st.divider()

elif menu == "💾 Backup":
    st.header("💾 Backup Manuale (iPad)")
    st.write("Scarica il file del database per salvarlo su iCloud Drive.")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "mio_database_beads.db")
