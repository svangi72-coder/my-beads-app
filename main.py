import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal App", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO DI SUPPORTO ---
DIZIONARIO_AIUTO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro",
        "prezzo": 85.0,
        "note": "Megattera con balenottero. Mare tropicale."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Croce, Ancora e Cuore."
    }
}

# --- 3. DATABASE PERSONALE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  sku TEXT, nome TEXT, designer TEXT, 
                  materiale TEXT, prezzo REAL, note TEXT, 
                  foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. GESTIONE MEMORIA (SESSION STATE) ---
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

def cerca_e_compila():
    parola = st.session_state.search_input.lower().strip()
    if parola in DIZIONARIO_AIUTO:
        v = DIZIONARIO_AIUTO[parola]
        st.session_state.temp_data = {
            "sku": v["sku"], "nome": v["nome"], "designer": v["designer"],
            "mat": v["materiale"], "prezzo": v["prezzo"], "note": v["note"]
        }
    elif parola != "":
        st.session_state.temp_data = {"sku": "", "nome": parola.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Aggiungi Nuovo", "💾 Backup Cloud"])

if menu == "➕ Aggiungi Nuovo":
    st.title("➕ Inserimento Bead")
    
    # RICERCA PULITA (Senza telecamera che disturba)
    st.text_input("🔍 Digita il nome (es. balena) e premi INVIO", 
                 key="search_input", on_change=cerca_e_compila)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        new_sku = st.text_input("SKU Tecnico", value=st.session_state.temp_data["sku"])
        new_nome = st.text_input("Nome Bead", value=st.session_state.temp_data["nome"])
        new_des = st.text_input("Designer", value=st.session_state.temp_data["designer"])
    with col2:
        new_pre = st.number_input("Prezzo (€)", value=float(st.session_state.temp_data["prezzo"]), step=1.0)
        lista_mat = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra"]
        idx = lista_mat.index(st.session_state.temp_data["mat"]) if st.session_state.temp_data["mat"] in lista_mat else 0
        new_mat = st.selectbox("Materiale", lista_mat, index=idx)

    new_note = st.text_area("Note e Storia", value=st.session_state.temp_data["note"])

    # --- GESTIONE FOTO A RICHIESTA ---
    st.write("### 📸 Immagine")
    opzione_foto = st.radio("Scegli come inserire la foto:", ["Nessuna / Carica file", "Usa Fotocamera iPad"], horizontal=True)
    
    foto_finale = None
    if opzione_foto == "Usa Fotocamera iPad":
        foto_finale = st.camera_input("Inquadra il bead")
    else:
        foto_finale = st.file_uploader("Carica una foto dalla galleria", type=['jpg', 'png', 'jpeg'])

    if st.button("💾 SALVA NEL MIO TELEFONO"):
        if new_sku and new_nome:
            percorso_foto = f"mie_immagini/{new_sku}.jpg"
            if foto_finale:
                Image.open(foto_finale).convert('RGB').save(os.path.join(BASE_DIR, percorso_foto), "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, note, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (new_sku, new_nome, new_des, new_mat, new_pre, new_note, percorso_foto))
            conn.commit()
            st.success(f"Bead '{new_nome}' salvato!")
            st.session_state.temp_data = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}
            st.rerun()

elif menu == "💎 La Mia Collezione":
    st.title("💎 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                full_img_path = os.path.join(BASE_DIR, row['foto_path'])
                if row['foto_path'] and os.path.exists(full_img_path):
                    st.image(full_img_path, use_container_width=True)
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                st.write(f"**Note:** {row['note']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()

elif menu == "💾 Backup Cloud":
    st.title("💾 Esporta Database")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Backup (.db)", f, "backup_beads.db")
