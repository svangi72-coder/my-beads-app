import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. SETUP CARTELLINE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'archivio_beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini_beads')
if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal", page_icon="💍", layout="wide")

# --- 2. IL TUO DATABASE TECNICO (Aggiungi qui altri modelli) ---
DIZIONARIO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro",
        "prezzo": 85.0,
        "descrizione": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "descrizione": "I tre simboli classici: la Croce per la Fede, l'Ancora per la Speranza e il Cuore per la Carità."
    }
}
LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

# --- 3. GESTIONE DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS beads 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. INTERFACCIA ---
st.sidebar.title("Menu")
scelta = st.sidebar.radio("Vai a:", ["Aggiungi Nuovo", "La Mia Collezione", "Backup"])

if scelta == "Aggiungi Nuovo":
    st.header("➕ Inserimento Bead")
    
    # RICERCA: Appena scrivi e premi INVIO, i campi sotto si riempiono
    nome_ricerca = st.text_input("🔍 Cerca nome nel database (es: balena)").lower().strip()
    
    # Recupero dati dal dizionario
    info = DIZIONARIO.get(nome_ricerca, {"sku": "", "nome": nome_ricerca.capitalize(), "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "descrizione": ""})

    st.divider()
    
    # Campi compilati automaticamente
    col1, col2 = st.columns(2)
    with col1:
        in_sku = st.text_input("Codice SKU", value=info["sku"])
        in_nome = st.text_input("Nome Ufficiale", value=info["nome"])
        in_designer = st.text_input("Designer", value=info["designer"])
    with col2:
        in_prezzo = st.number_input("Prezzo (€)", value=float(info["prezzo"]), step=1.0)
        # Selezione materiale precisa
        try:
            idx_m = LISTA_MATERIALI.index(info["materiale"])
        except:
            idx_m = 0
        in_materiale = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)

    in_descrizione = st.text_area("Descrizione", value=info["descrizione"], height=100)
    
    st.write("**📸 Carica Foto**")
    st.info("Consiglio: Salva la foto da Google sul tuo iPad e caricala qui sotto.")
    in_foto = st.file_uploader("Seleziona foto o scatta", type=['jpg', 'jpeg', 'png'])

    if st.button("📥 SALVA NELL'ARCHIVIO PERSONALE"):
        if in_sku and in_nome:
            path_foto = ""
            if in_foto:
                nome_file = f"{in_sku.replace('/', '_')}.jpg"
                path_foto = os.path.join('immagini_beads', nome_file)
                Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, path_foto), "JPEG")
            
            conn.execute('''INSERT INTO beads (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (in_sku, in_nome, in_designer, in_materiale, in_prezzo, in_descrizione, path_foto))
            conn.commit()
            st.success(f"Bead '{in_nome}' salvato correttamente!")
            st.balloons()
        else:
            st.error("Inserisci almeno SKU e Nome!")

elif scelta == "La Mia Collezione":
    st.header("💍 I Miei Pezzi")
    df = pd.read_sql("SELECT * FROM beads", conn)
    if df.empty:
        st.write("Nessun bead salvato.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if row['foto_path'] and os.path.exists(os.path.join(BASE_DIR, row['foto_path'])):
                        st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
                with c2:
                    st.write(f"**Materiale:** {row['materiale']} | **Designer:** {row['designer']}")
                    st.write(f"**Descrizione:** {row['descrizione']}")
                    if st.button("Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM beads WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

elif scelta == "Backup":
    st.header("💾 Scarica Dati")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Esporta Database (.db)", f, "backup_beads.db")
