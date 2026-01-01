import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI E PAGINA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="Trollbeads Collector PRO", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .bead-card {
        padding: 20px; border-radius: 15px; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    .web-box {
        background-color: #E3F2FD; padding: 20px; border-radius: 15px;
        border: 2px solid #2196F3; margin-bottom: 20px;
    }
    .bead-title { color: #1A2530; font-family: 'serif'; font-weight: bold; font-size: 1.6rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER,
                  posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. DIZIONARIO PER AUTO-COMPILAZIONE ---
# Questo database interno permette all'app di "conoscere" i pezzi più famosi
INFO_PREDEFINITE = {
    "il canto della balena": {
        "sku": "TAGPE-00012",
        "designer": "Lise Aagaard",
        "materiale": "Vetro",
        "prezzo": 55.0,
        "note": "Un bead in vetro con riflessi oceanici, parte della collezione classica."
    },
    "fede speranza carità": {
        "sku": "TAGBE-10052",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Bead classico in argento che rappresenta i tre simboli teologali."
    }
}

# --- 4. FUNZIONE VISUALIZZAZIONE ---
def mostra_beads(dataframe):
    if dataframe.empty:
        st.info("Nessun bead trovato nel database.")
        return
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='bead-title'>{row['nome_it']}</div>", unsafe_allow_html=True)
            col_img, col_info = st.columns([1.2, 3])
            with col_img:
                img_rel = row['img_filename']
                full_path = os.path.join(BASE_DIR, img_rel) if img_rel else ""
                if full_path and os.path.exists(full_path):
                    st.image(full_path, use_container_width=True)
                else:
                    st.warning("📷 Immagine mancante")
            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Designer:** {row['designer']}")
                st.write(f"**Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']}")
                if st.button("❤️" if not row['posseduto'] else "❌ Rimuovi", key=f"p_{row['id']}"):
                    conn.execute("UPDATE charms SET posseduto=? WHERE id=?", (1-row['posseduto'], row['id']))
                    conn.commit(); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 5. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo & Ricerca", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione Web"])

if menu == "📖 Catalogo & Ricerca":
    st.header("📖 Catalogo Generale")
    f_testo = st.text_input("Filtra per nome o SKU")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if f_testo:
        df = df[df['nome_it'].str.contains(f_testo, case=False) | df['sku'].str.contains(f_testo, case=False)]
    mostra_beads(df)

elif menu == "💍 Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_my)

elif menu == "🌐 Ricerca & Acquisizione Web":
    st.header("🌐 Centro Acquisizione Nuovi Beads")
    search_q = st.text_input("Cerca Nome o SKU", placeholder="Es: il canto della balena")
    
    # Logica di auto-completamento
    dati_trovati = INFO_PREDEFINITE.get(search_q.lower(), {"sku": search_q, "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""})

    if search_q:
        c1, c2 = st.columns([1, 1])
        with c2:
            st.markdown(f"[📸 Cerca su Google](https://www.google.it/search?q=trollbeads+{search_q}&tbm=isch)")
        
        st.subheader("📝 Scheda di Acquisizione")
        with st.form("web_acquisizione", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                w_sku = st.text_input("SKU ufficiale", value=dati_trovati['sku'])
                w_nome = st.text_input("Nome del Bead (Italiano)", value=search_q.capitalize())
                w_brand = st.selectbox("Marca", ["Trollbeads", "Pandora", "Ohm"])
                w_designer = st.text_input("Designer", value=dati_trovati['designer'])
            with col_b:
                w_prezzo = st.number_input("Prezzo (€)", value=dati_trovati['prezzo'])
                w_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"], 
                                     index=["Argento 925", "Vetro", "Pietra", "Oro"].index(dati_trovati['materiale']))
                w_foto = st.file_uploader("Carica foto", type=['jpg', 'png', 'jpeg'])
            
            w_note = st.text_area("Note", value=dati_trovati['note'])
            
            if st.form_submit_button("✨ SALVA NEL CATALOGO GENERALE"):
                fname = f"immagini/{w_sku}.jpg"
                if w_foto:
                    Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                VALUES (?,?,?,?,?,?,?,?,0,0)''', 
                             (w_brand, w_sku, w_nome, w_mat, w_designer, w_prezzo, w_note, fname))
                conn.commit(); st.success(f"Aggiunto: {w_nome}")
