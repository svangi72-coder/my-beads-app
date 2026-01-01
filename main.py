import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI (Locale su iPad/PC) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💍", layout="wide")

# --- 2. DIZIONARIO TECNICO (Dati Corretti dai tuoi screenshot) ---
DIZIONARIO = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro",
        "prezzo": 85.0,
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero."
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

# --- 3. DATABASE LOCALE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER, posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Menu", ["📖 Mia Collezione", "🌐 Ricerca e Acquisizione", "💾 Backup"])

if menu == "🌐 Ricerca e Acquisizione":
    st.header("🌐 Acquisizione Intelligente (Dati Scissi)")
    
    # CAMPO RICERCA: Fuori dal form per reattività immediata
    cerca_nome = st.text_input("🔍 Digita il nome (es: balena) e premi INVIO", key="search_input")
    
    # Logica di ricerca flessibile
    info = {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""}
    if cerca_nome:
        chiave = cerca_nome.lower().strip()
        # Cerca corrispondenza parziale nel dizionario
        for k, v in DIZIONARIO.items():
            if k in chiave:
                info = v
                break
    
    if cerca_nome:
        st.info(f"Dati trovati per: {info['nome'] if info['nome'] else cerca_nome}")
        st.markdown(f"[📸 Apri Ricerca Google Immagini](https://www.google.it/search?q=trollbeads+{cerca_nome.replace(' ', '+')}&tbm=isch)")

    # FORM DI SALVATAGGIO: Con tutti i campi richiesti
    with st.form("form_acquisizione"):
        st.subheader("📝 Verifica i dati tecnici")
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("SKU Ufficiale (scisso dal nome)", value=info['sku'])
            in_nome = st.text_input("Nome Bead (Italiano)", value=info['nome'] if info['nome'] else cerca_nome.capitalize())
            in_des = st.text_input("Designer", value=info['designer'])
            in_brand = st.selectbox("Marca", ["Trollbeads", "Pandora", "Ohm"])
        with col2:
            in_pre = st.number_input("Prezzo Listino (€)", value=info['prezzo'], step=1.0)
            # Fix materiale automatico
            idx_m = LISTA_MATERIALI.index(info['materiale']) if info['materiale'] in LISTA_MATERIALI else 0
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
            in_stato = st.checkbox("Retired (Fuori Produzione)")
            
            # OPZIONE FOTO: Scatto iPad o Caricamento
            metodo_foto = st.radio("Sorgente foto:", ["Fotocamera iPad 📸", "Galleria 🖼️"])
            if metodo_foto == "Fotocamera iPad 📸":
                foto_input = st.camera_input("Inquadra il bead")
            else:
                foto_input = st.file_uploader("Scegli file", type=['jpg', 'png', 'jpeg'])

        in_note = st.text_area("Note e Storia", value=info['note'])
        
        if st.form_submit_button("💾 SALVA NEL MIO DB PERSONALE"):
            if in_sku and in_nome:
                # Salvataggio fisico immagine
                fname = f"immagini/{in_sku.replace('/', '_')}.jpg"
                if foto_input:
                    Image.open(foto_input).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, designer, materiale, prezzo, desc_it, img_filename, fuori_produzione, posseduto) 
                                VALUES (?,?,?,?,?,?,?,?,?,1)''', 
                             (in_brand, in_sku, in_nome, in_des, in_mat, in_pre, in_note, fname, 1 if in_stato else 0))
                conn.commit()
                st.success(f"Bead '{in_nome}' salvato nel tuo archivio!")
            else:
                st.error("Inserisci almeno SKU e Nome.")

elif menu == "📖 Mia Collezione":
    st.header("💍 Il Mio Archivio Personale")
    
    # FILTRI AVANZATI RICHIESTI
    with st.expander("🔍 Filtra la tua collezione", expanded=True):
        f_c1, f_c2, f_c3 = st.columns(3)
        with f_c1: f_nome = st.text_input("Cerca Nome/SKU")
        with f_c2: f_mat = st.multiselect("Materiale", LISTA_MATERIALI)
        with f_c3: f_stato = st.radio("Stato", ["Tutti", "Attivi", "Retired"])

    df = pd.read_sql("SELECT * FROM charms", conn)
    
    # Logica Filtri
    if f_nome:
        df = df[df['nome_it'].str.contains(f_nome, case=False) | df['sku'].str.contains(f_nome, case=False)]
    if f_mat:
        df = df[df['materiale'].isin(f_mat)]
    if f_stato == "Retired":
        df = df[df['fuori_produzione'] == 1]
    elif f_stato == "Attivi":
        df = df[df['fuori_produzione'] == 0]

    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"### {row['nome_it']} ({row['sku']})")
            c1, c2 = st.columns([1, 2])
            with c1:
                path = os.path.join(BASE_DIR, row['img_filename'])
                if os.path.exists(path): st.image(path, use_container_width=True)
            with c2:
                st.write(f"**Designer:** {row['designer']} | **Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Materiale:** {row['materiale']} | **Stato:** {'Retired' if row['fuori_produzione'] else 'Attivo'}")
                st.write(f"**Storia:** {row['desc_it']}")
                if st.button("🗑️ Rimuovi", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                    conn.commit(); st.rerun()
            st.divider()

elif menu == "💾 Backup":
    st.header("💾 Backup su iCloud/Google Drive")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica il tuo Database (.db)", f, "my_beads_archive.db")
