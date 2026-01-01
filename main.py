import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. SETUP AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'foto_beads')

# Creazione cartella immagini se non esiste
if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal", page_icon="💍", layout="wide")

# --- 2. DIZIONARIO TECNICO (Per auto-compilazione veloce) ---
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

# --- 3. GESTIONE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. INTERFACCIA ---
st.sidebar.title("Menu iPad")
menu = st.sidebar.radio("Vai a:", ["➕ Aggiungi Nuovo", "💍 La Mia Collezione", "💾 Backup"])

if menu == "➕ Aggiungi Nuovo":
    st.header("➕ Nuova Acquisizione")
    
    # RICERCA ISTANTANEA
    cerca = st.text_input("🔍 Cerca nel DB interno (es: balena) o scrivi il nome").lower().strip()
    
    # Recupero dati
    info = DIZIONARIO.get(cerca, {"sku": "", "nome": cerca.capitalize(), "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "descrizione": ""})

    st.divider()
    
    # SCHEDA DI ACQUISIZIONE
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("Codice SKU", value=info["sku"])
            in_nome = st.text_input("Nome Ufficiale", value=info["nome"])
            in_designer = st.text_input("Designer", value=info["designer"])
        with col2:
            in_prezzo = st.number_input("Prezzo (€)", value=float(info["prezzo"]), step=1.0)
            try:
                idx_m = LISTA_MATERIALI.index(info["materiale"])
            except:
                idx_m = 0
            in_materiale = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
            
        in_descrizione = st.text_area("Descrizione (Significato)", value=info["descrizione"], height=150)
        
        st.write("**📷 Carica Foto (Salvala prima da Safari sul tuo iPad)**")
        in_foto = st.file_uploader("Scegli dal rullino o scatta", type=['jpg', 'jpeg', 'png'])

    if st.button("💾 SALVA DEFINITIVAMENTE NEL DB"):
        if in_sku and in_nome:
            # Gestione nome file foto
            nome_foto = f"{in_sku.replace('/', '_')}.jpg"
            percorso_salvataggio = os.path.join(IMG_FOLDER, nome_foto)
            
            if in_foto:
                # Salvataggio fisico
                img = Image.open(in_foto).convert('RGB')
                img.save(os.path.join(BASE_DIR, percorso_salvataggio), "JPEG")
                st.success("✅ Foto salvata correttamente!")
            
            # Salvataggio dati nel DB
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (in_sku, in_nome, in_designer, in_materiale, in_prezzo, in_descrizione, percorso_salvataggio))
            conn.commit()
            st.success(f"Bead '{in_nome}' aggiunto alla collezione!")
            st.balloons()
        else:
            st.error("Inserisci almeno SKU e Nome!")

elif menu == "💍 La Mia Collezione":
    st.header("💍 Archivio Personale")
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if df.empty:
        st.info("Nessun bead ancora salvato.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    # Caricamento immagine corretto per iPad
                    if row['foto_path']:
                        full_path = os.path.join(BASE_DIR, row['foto_path'])
                        if os.path.exists(full_path):
                            st.image(full_path, use_container_width=True)
                        else:
                            st.warning("Foto non trovata.")
                with c2:
                    st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']}")
                    st.write(f"**Prezzo:** €{row['prezzo']}")
                    st.info(f"**Significato:** {row['descrizione']}")
                    if st.button("Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Dati")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_beads.db")
