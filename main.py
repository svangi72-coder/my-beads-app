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

# --- 2. DIZIONARIO TECNICO (Dati Corretti) ---
DIZIONARIO = {
    "balena": {
        "sku": "TAGPE-00012", 
        "nome": "Il Canto della Balena", 
        "designer": "Morten Pol Engell Nørregård", 
        "mat": "Vetro", 
        "prezzo": 85.0, 
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero."
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

# --- 3. FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, 
                  nome_it TEXT, designer TEXT, materiale TEXT, prezzo REAL, 
                  desc_it TEXT, img_filename TEXT, fuori_produzione INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Navigazione", ["📖 Collezione", "🌐 Acquisizione", "💾 Backup"])

if menu == "🌐 Acquisizione":
    st.header("🌐 Ricerca e Inserimento Immediato")
    
    # RICERCA: Senza form per aggiornamento istantaneo
    cerca = st.text_input("🔍 Cerca Nome (es: balena) e premi INVIO").lower().strip()
    
    info = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}
    if cerca:
        for k, v in DIZIONARIO.items():
            if k in cerca:
                info = v
                break

    st.divider()
    
    # CAMPI DI INSERIMENTO (Senza st.form per evitare blocchi)
    col1, col2 = st.columns(2)
    with col1:
        in_sku = st.text_input("SKU Tecnico", value=info['sku'])
        in_nome = st.text_input("Nome Ufficiale", value=info['nome'])
        in_des = st.text_input("Designer", value=info['designer'])
    with col2:
        in_pre = st.number_input("Prezzo (€)", value=float(info['prezzo']), step=1.0)
        idx_m = LISTA_MATERIALI.index(info['mat']) if info['mat'] in LISTA_MATERIALI else 0
        in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
        in_ret = st.checkbox("Retired (Fuori Produzione)")

    st.write("**📷 Foto iPad**")
    in_foto = st.camera_input("Scatta la foto del bead")
    in_note = st.text_area("Note e Storia", value=info['note'])
    
    if st.button("📥 SALVA DEFINITIVAMENTE NEL DATABASE"):
        if in_sku and in_nome:
            fname = f"immagini/{in_sku.replace('/', '_')}.jpg"
            if in_foto:
                Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome_it, designer, materiale, prezzo, desc_it, img_filename, fuori_produzione) 
                            VALUES (?,?,?,?,?,?,?,?)''', 
                         (in_sku, in_nome, in_des, in_mat, in_pre, in_note, fname, 1 if in_ret else 0))
            conn.commit()
            st.success(f"Bead '{in_nome}' salvato con successo!")
            st.balloons()
        else:
            st.error("Errore: SKU e Nome sono necessari!")

elif menu == "📖 Collezione":
    st.header("💍 Il Mio Archivio")
    # Filtri veloci
    f_txt = st.text_input("🔍 Filtra per Nome o SKU")
    
    df = pd.read_sql("SELECT * FROM charms", conn)
    if f_txt:
        df = df[df['nome_it'].str.contains(f_txt, case=False) | df['sku'].str.contains(f_txt, case=False)]
    
    for _, row in df.iterrows():
        with st.expander(f"{row['nome_it']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                img_p = os.path.join(BASE_DIR, row['img_filename'])
                if row['img_filename'] and os.path.exists(img_p):
                    st.image(img_p)
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                st.write(f"**Materiale:** {row['materiale']} | **Stato:** {'Retired' if row['fuori_produzione'] else 'Attivo'}")
                st.write(f"**Note:** {row['desc_it']}")
                if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Manuale")
    st.write("Scarica il database e salvalo nei tuoi file su iCloud.")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "my_beads.db")
