import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE E DATABASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER, posseduto INTEGER)''')
    return conn

conn = init_db()

# Dizionario per auto-completamento rapido
DIZIONARIO_TECNICO = {
    "balena": {"sku": "TAGPE-00012", "nome": "Il Canto della Balena", "designer": "Morten Pol Engell Nørregård", "materiale": "Vetro", "prezzo": 85.0, "note": "Megattera con balenottero."},
    "fede": {"sku": "TAGBE-10052", "nome": "Fede, Speranza e Carità", "designer": "Søren Nielsen", "materiale": "Argento 925", "prezzo": 45.0, "note": "Croce, Ancora, Cuore."}
}

LISTA_MATERIALI = ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame"]

# --- 2. LOGICA VISUALIZZAZIONE ---
def mostra_scheda_bead(row):
    with st.container():
        st.markdown(f"### {row['nome_it']}")
        col1, col2 = st.columns([1, 2])
        with col1:
            if row['img_filename'] and os.path.exists(os.path.join(BASE_DIR, row['img_filename'])):
                st.image(os.path.join(BASE_DIR, row['img_filename']), use_container_width=True)
        with col2:
            st.write(f"**SKU:** {row['sku']} | **Designer:** {row['designer']}")
            st.write(f"**Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']}")
            st.write(f"**Note:** {row['desc_it']}")
            if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); st.rerun()
        st.divider()

# --- 3. NAVIGAZIONE ---
menu = st.sidebar.radio("Navigazione", ["📖 Catalogo Generale", "🌐 Ricerca & Acquisizione"])

if menu == "🌐 Ricerca & Acquisizione":
    st.header("🌐 Acquisizione con Scansione e Filtri")
    
    # --- PARTE 1: RICERCA E FILTRI ---
    with st.container():
        st.subheader("🔍 Parametri di Ricerca Web")
        c1, c2 = st.columns(2)
        with c1:
            q_nome = st.text_input("Inserisci NOME (es: balena)", key="acq_name").strip().lower()
        with c2:
            q_sku = st.text_input("Inserisci SKU (es: TAGPE-00012)", key="acq_sku").strip().upper()

    # Recupero dati da dizionario se disponibile
    info = DIZIONARIO_TECNICO.get(q_nome, {"sku": q_sku, "nome": q_nome.capitalize(), "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""})
    
    # Link Google basati sulla scissione SKU/Nome
    if q_nome or q_sku:
        query_web = f"trollbeads {q_sku} {q_nome}".replace(" ", "+")
        st.markdown(f"🔗 [Risultati Web per {q_nome} {q_sku}](https://www.google.it/search?q={query_web})")

    # --- PARTE 2: ACQUISIZIONE DATI ---
    st.subheader("📝 Scheda Tecnica per Database Generale")
    with st.form("form_database_generale"):
        col_a, col_b = st.columns(2)
        with col_a:
            in_sku = st.text_input("SKU Tecnico", value=info['sku'])
            in_nome = st.text_input("Nome Ufficiale IT", value=info['nome'])
            in_designer = st.text_input("Nome Designer", value=info['designer'])
            in_prezzo = st.number_input("Prezzo Listino (€)", value=info['prezzo'])
        
        with col_b:
            idx_m = LISTA_MATERIALI.index(info['materiale']) if info['materiale'] in LISTA_MATERIALI else 0
            in_materiale = st.selectbox("Materiale Prevalente", LISTA_MATERIALI, index=idx_m)
            in_stato = st.selectbox("Stato Produzione", ["In Produzione", "Retired"])
            
            st.write("**📷 Immagine Bead**")
            input_metodo = st.radio("Sorgente foto:", ["Carica file", "Scatta foto ora"])
            if input_metodo == "Carica file":
                in_foto = st.file_uploader("Scegli file", type=['jpg', 'png'])
            else:
                in_foto = st.camera_input("Inquadra il bead")

        in_note = st.text_area("Descrizione Estesa e Storia", value=info['note'])
        
        if st.form_submit_button("📥 SALVA NEL DATABASE GENERALE"):
            if in_sku and in_nome:
                fname = f"immagini/{in_sku}.jpg"
                if in_foto:
                    Image.open(in_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                VALUES ('Trollbeads',?,?,?,?,?,?,?,0,?)''', 
                             (in_sku, in_nome, in_materiale, in_designer, in_prezzo, in_note, fname, 1 if in_stato=="Retired" else 0))
                conn.commit()
                st.success(f"Dati salvati correttamente: {in_nome} [{in_sku}]")
            else:
                st.error("Errore: SKU e Nome sono campi obbligatori per il database.")

elif menu == "📖 Catalogo Generale":
    st.header("📖 Archivio Generale Beads")
    # Filtri di visualizzazione
    with st.sidebar.expander("🔍 Filtri Archivio", expanded=True):
        f_m = st.multiselect("Filtra per Materiale", LISTA_MATERIALI)
        f_s = st.text_input("Cerca per SKU")
    
    query = "SELECT * FROM charms"
    df = pd.read_sql(query, conn)
    if f_m: df = df[df['materiale'].isin(f_m)]
    if f_s: df = df[df['sku'].str.contains(f_s, case=False)]
    
    for _, row in df.iterrows():
        mostra_scheda_bead(row)
