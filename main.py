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

# --- 2. DIZIONARIO DI SUPPORTO AGGIORNATO ---
DIZIONARIO_AIUTO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro", # <--- Corretto: Vetro
        "prezzo": 85.0,
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925", # <--- Corretto: Argento
        "prezzo": 45.0,
        "note": "Croce, Ancora e Cuore."
    }
}

LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra", "Rame"]

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

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("VAI A:", ["💎 La Mia Collezione", "➕ Aggiungi Nuovo", "💾 Backup Cloud"])

if menu == "➕ Aggiungi Nuovo":
    st.title("➕ Inserimento Bead")
    
    # RICERCA
    cerca = st.text_input("🔍 Digita il nome (es. balena) e premi INVIO").lower().strip()
    
    # Inizializzazione dati predefiniti
    info = {"sku": "", "nome": cerca.capitalize(), "designer": "", "mat": "Argento 925", "prezzo": 0.0, "note": ""}
    
    # Se troviamo la parola nel dizionario, carichiamo i dati
    if cerca:
        for k, v in DIZIONARIO_AIUTO.items():
            if k in cerca:
                info = {
                    "sku": v["sku"], "nome": v["nome"], "designer": v["designer"],
                    "mat": v["materiale"], "prezzo": v["prezzo"], "note": v["note"]
                }
                break

    st.divider()
    
    # CAMPI DI INSERIMENTO
    col1, col2 = st.columns(2)
    with col1:
        new_sku = st.text_input("SKU Tecnico", value=info["sku"])
        new_nome = st.text_input("Nome Ufficiale", value=info["nome"])
        new_des = st.text_input("Designer", value=info["designer"])
    with col2:
        new_pre = st.number_input("Prezzo (€)", value=float(info["prezzo"]), step=1.0)
        # Selezione dinamica del materiale
        try:
            default_index = LISTA_MATERIALI.index(info["mat"])
        except ValueError:
            default_index = 0
        new_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=default_index)

    new_note = st.text_area("Note e Storia", value=info["note"])

    # --- FOTO ---
    st.write("### 📸 Immagine")
    attiva_cam = st.checkbox("Usa Fotocamera iPad")
    
    foto_file = None
    if attiva_cam:
        foto_file = st.camera_input("Scatta")
    else:
        foto_file = st.file_uploader("Carica dalla galleria", type=['jpg', 'png', 'jpeg'])

    if st.button("💾 SALVA NEL MIO DATABASE"):
        if new_sku and new_nome:
            # Creiamo un nome file pulito usando lo SKU
            nome_file = f"{new_sku.replace('/', '_')}.jpg"
            percorso_relativo = os.path.join('mie_immagini', nome_file)
            percorso_assoluto = os.path.join(BASE_DIR, percorso_relativo)
            
            if foto_file:
                # Salvataggio fisico della foto
                img = Image.open(foto_file)
                img.convert('RGB').save(percorso_assoluto, "JPEG")
                st.info(f"Foto salvata in: {percorso_relativo}")
            else:
                percorso_relativo = ""

            # Inserimento nel DB
            conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, note, foto_path) 
                            VALUES (?,?,?,?,?,?,?)''', 
                         (new_sku, new_nome, new_des, new_mat, new_pre, new_note, percorso_relativo))
            conn.commit()
            st.success(f"✅ Bead '{new_nome}' salvato con successo!")
            st.balloons()
        else:
            st.error("❌ Errore: SKU e Nome sono necessari!")

elif menu == "💎 La Mia Collezione":
    st.title("💎 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if df.empty:
        st.info("La collezione è vuota.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if row['foto_path']:
                        full_img_path = os.path.join(BASE_DIR, row['foto_path'])
                        if os.path.exists(full_path := full_img_path):
                            st.image(full_path, use_container_width=True)
                        else:
                            st.warning("Foto non trovata nel percorso.")
                    else:
                        st.write("Nessuna foto caricata.")
                with c2:
                    st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']}")
                    st.write(f"**Materiale:** {row['materiale']}")
                    st.write(f"**Note:** {row['note']}")
                    if st.button("Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

elif menu == "💾 Backup Cloud":
    st.header("💾 Backup")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_beads.db")
