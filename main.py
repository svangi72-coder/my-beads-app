import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI E PAGINA ---
# Otteniamo il percorso della cartella dove si trova questo file main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')

st.set_page_config(page_title="Trollbeads Collector Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FDFDFD; }
    .bead-card {
        padding: 15px; border-radius: 12px; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; margin-bottom: 20px;
    }
    .bead-title { color: #1A2530; font-family: 'serif'; font-weight: bold; font-size: 1.3rem; }
    .google-btn {
        background-color: #4285F4; color: white; padding: 10px 20px;
        border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE ---
def init_db():
    # Connessione al database usando il percorso dinamico
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, prezzo REAL, materiale TEXT, 
                  fuori_produzione INTEGER, posseduto INTEGER)''')
    
    c.execute("SELECT count(*) FROM charms")
    if c.fetchone()[0] == 0:
        beads_master = [
            ('Trollbeads', 'TAGBE-10052', 'fede.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', 'Cuore e ancora', 45.0, 'Argento 925', 0, 0),
            ('Trollbeads', 'TAGPE-00012', 'balena.jpg', 'Canto della Balena', 'Whale Song', 'Vetro blu', 55.0, 'Vetro', 0, 0)
        ]
        c.executemany("INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, prezzo, materiale, fuori_produzione, posseduto) VALUES (?,?,?,?,?,?,?,?,?,?)", beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 3. FUNZIONE VISUALIZZAZIONE ---
def mostra_beads(df, titolo_sezione):
    st.subheader(f"{titolo_sezione} ({len(df)})")
    if df.empty:
        st.info("Nessun bead trovato.")
        return
    
    for _, row in df.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 4])
            with col1:
                # Percorso immagine dinamico
                img_path = os.path.join(BASE_DIR, row['img_filename']) if row['img_filename'] else ""
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.markdown("<h1 style='text-align: center;'>💎</h1>", unsafe_allow_html=True)
                    st.caption("Immagine non trovata")
            with col2:
                st.markdown(f"<div class='bead-title'>{row['nome_it']}</div>", unsafe_allow_html=True)
                st.write(f"**SKU:** {row['sku']} | **Brand:** {row['brand']} | **Materiale:** {row['materiale']}")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    label = "❤️ Possiedo" if not row['posseduto'] else "❌ Rimuovi"
                    if st.button(label, key=f"pos_{row['id']}"):
                        nuovo = 0 if row['posseduto'] else 1
                        conn.execute("UPDATE charms SET posseduto = ? WHERE id = ?", (nuovo, row['id']))
                        conn.commit()
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Menu", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Ricerca Avanzata"])

if menu == "Catalogo Generale":
    st.header("📖 Tutti i Beads")
    df_all = pd.read_sql("SELECT * FROM charms", conn)
    mostra_beads(df_all, "Database Completo")

elif menu == "Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_my, "I miei pezzi")

elif menu == "Aggiungi Nuovo":
    st.header("➕ Inserisci nel Database")
    foto = st.camera_input("Scatta Foto")
    with st.form("add"):
        f_sku = st.text_input("SKU")
        f_nome = st.text_input("Nome (IT)")
        f_nome_en = st.text_input("Nome (EN)")
        f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        f_prezzo = st.number_input("Prezzo", min_value=0.0)
        if st.form_submit_button("Salva"):
            fname = f"{f_sku}.jpg" if f_sku else "temp.jpg"
            if foto:
                full_img_path = os.path.join(BASE_DIR, fname)
                Image.open(foto).convert("RGB").save(full_img_path)
            conn.execute("INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, prezzo, materiale, posseduto) VALUES ('Trollbeads',?,?,?,?,?,?,0)", 
                         (f_sku, fname, f_nome, f_nome_en, f_prezzo, f_mat))
            conn.commit()
            st.success(f"Salvato correttamente come {fname}")

elif menu == "Ricerca Avanzata":
    st.header("🔍 Ricerca nel DB e su Google")
    cerca_testo = st.text_input("Cerca per Nome o SKU")
    
    if cerca_testo:
        url_google = f"https://www.google.it/search?q=trollbeads+{cerca_testo.replace(' ', '+')}&tbm=isch"
        st.markdown(f'<a href="{url_google}" target="_blank" class="google-btn">🔍 Cerca "{cerca_testo}" su Google Immagini</a>', unsafe_allow_html=True)
        
        # Ricerca nel DB
        query = "SELECT * FROM charms WHERE nome_it LIKE ? OR nome_en LIKE ? OR sku LIKE ?"
        p = f"%{cerca_testo}%"
        df_res = pd.read_sql(query, conn, params=(p, p, p))
        mostra_beads(df_res, "Risultati Database")
