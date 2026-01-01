import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE AMBIENTE STANDALONE ---
# Definiamo i percorsi locali. Su iPad/iPhone l'app userà la sua cartella privata.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal App", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO DI SUPPORTO (MEMORIA LOCALE) ---
# Dati pre-caricati per aiutarti nell'inserimento veloce
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

# --- 3. GESTIONE DATABASE PERSONALE ---
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

# --- 4. LOGICA DI RICERCA (FUNZIONAMENTO ISTANTANEO) ---
# Usiamo lo stato della sessione per "bloccare" i dati trovati
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

def cerca_e_compila():
    parola = st.session_state.search_input.lower().strip()
    found = False
    for k, v in DIZIONARIO_AIUTO.items():
        if k in parola:
            st.session_state.temp_data = {
                "sku": v["sku"], "nome": v["nome"], "designer": v["designer"],
                "mat": v["materiale"], "prezzo": v["prezzo"], "note": v["note"]
            }
            found = True
            break
    if not found and parola != "":
        st.session_state.temp_data = {"sku": "", "nome": parola.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 5. INTERFACCIA UTENTE (NAVIGAZIONE) ---
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Aggiungi Nuovo", "💾 Backup Cloud"])

# --- SEZIONE A: COLLEZIONE ---
if menu == "💎 La Mia Collezione":
    st.title("💎 Il Mio Archivio Personale")
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if df.empty:
        st.info("La tua collezione è ancora vuota. Inizia ad aggiungere i tuoi beads!")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if row['foto_path'] and os.path.exists(os.path.join(BASE_DIR, row['foto_path'])):
                        st.image(os.path.join(BASE_DIR, row['foto_path']), use_container_width=True)
                with c2:
                    st.write(f"**Designer:** {row['designer']}")
                    st.write(f"**Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']}")
                    st.write(f"**Note:** {row['note']}")
                    if st.button("Elimina Pezzo", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

# --- SEZIONE B: AGGIUNGI (IL CUORE DELL'APP) ---
elif menu == "➕ Aggiungi Nuovo":
    st.title("➕ Inserimento Bead")
    
    # Campo di ricerca fuori dai form per massima reattività
    st.text_input("🔍 Cerca nel dizionario (es. balena) o scrivi il nome", 
                 key="search_input", on_change=cerca_e_compila)
    
    st.divider()
    
    # Campi compilati automaticamente o manualmente
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

    st.write("**📷 Foto (Usa fotocamera iPad o carica file)**")
    new_foto = st.camera_input("Scatta")
    new_note = st.text_area("Note e Storia", value=st.session_state.temp_data["note"])

    if st.button("💾 SALVA NEL MIO TELEFONO"):
        if new_sku and new_nome:
            percorso_foto = f"mie_immagini/{new_sku}.jpg"
            if new_foto:
                Image.open(new_foto).convert('RGB').save(os.path.join(BASE_DIR, percorso_foto), "JPEG")
            
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, note, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (new_sku, new_nome, new_des, new_mat, new_pre, new_note, percorso_foto))
            conn.commit()
            st.success(f"Bead '{new_nome}' salvato localmente!")
            st.session_state.temp_data = {"sku": "", "nome": "", "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}
        else:
            st.error("Inserisci almeno SKU e Nome.")

# --- SEZIONE C: BACKUP (TUA RICHIESTA SPECIFICA) ---
elif menu == "💾 Backup Cloud":
    st.title("💾 Gestione Backup Personale")
    st.write("Scarica il tuo database per salvarlo su iCloud, Google Drive o inviarlo via email.")
    
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            st.download_button(
                label="📤 Esporta Database (.db)",
                data=f,
                file_name="backup_beads_personale.db",
                mime="application/x-sqlite3"
            )
    
    st.divider()
    st.subheader("📥 Ripristina Dati")
    st.write("Hai cambiato telefono? Carica qui il tuo file di backup.")
    file_caricato = st.file_uploader("Scegli il file .db", type="db")
    if file_caricato:
        with open(DB_PATH, "wb") as f:
            f.write(file_caricato.getbuffer())
        st.success("Dati ripristinati! Ricarica la pagina.")
