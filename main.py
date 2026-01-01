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

st.set_page_config(page_title="Trollbeads Collector Pro", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FDFDFD; }
    .bead-card {
        padding: 20px; border-radius: 15px; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; box-shadow: 2px 2px 12px rgba(0,0,0,0.03);
        margin-bottom: 25px;
    }
    .bead-title { color: #1A2530; font-family: 'serif'; font-weight: bold; font-size: 1.5rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE CON REINSERIMENTO DATI BASE ---
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
    
    # Se il database è vuoto, aggiungi i dati di esempio per non vederlo vuoto
    c.execute("SELECT count(*) FROM charms")
    if c.fetchone()[0] == 0:
        beads_master = [
            ('Trollbeads', 'TAGBE-10052', 'immagini/fede.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', 'Cuore, ancora e croce', 45.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TAGPE-00012', 'immagini/balena.jpg', 'Canto della Balena', 'Whale Song', 'Vetro blu intenso', 55.0, 'Lise Aagaard', 'Vetro', 0, 0)
        ]
        c.executemany('''INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 3. FUNZIONE VISUALIZZAZIONE CON MODIFICA ---
def mostra_beads(dataframe):
    if dataframe.empty:
        st.info("Nessun bead trovato in questa sezione.")
        return
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'><div class='bead-title'>{row['nome_it']}</div></div>", unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                img_relative_path = row['img_filename']
                full_img_path = os.path.join(BASE_DIR, img_relative_path) if img_relative_path else ""
                if full_img_path and os.path.exists(full_img_path):
                    st.image(full_img_path, use_container_width=True)
                else:
                    st.markdown("<h2 style='text-align: center;'>🖼️</h2>", unsafe_allow_html=True)
                    st.caption(f"Percorso: {img_relative_path}")

            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Brand:** {row['brand']} | **Materiale:** {row['materiale']}")
                
                tab1, tab2 = st.tabs(["Dettagli e Azioni", "📝 Modifica"])
                
                with tab1:
                    st.write(f"**Prezzo:** €{row['prezzo']} | **Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 Attivo'}")
                    st.write(f"**Note:** {row['desc_it']}")
                    btn_a, btn_b = st.columns(2)
                    with btn_a:
                        label = "❌ Rimuovi da Collezione" if row['posseduto'] else "❤️ Aggiungi a Collezione"
                        if st.button(label, key=f"poss_{row['id']}"):
                            val = 1 - row['posseduto']
                            conn.execute("UPDATE charms SET posseduto = ? WHERE id = ?", (val, row['id']))
                            conn.commit()
                            st.rerun()
                    with btn_b:
                        if st.button("🗑️ Elimina Definitivamente", key=f"del_{row['id']}"):
                            conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                            conn.commit()
                            st.rerun()

                with tab2:
                    with st.form(f"edit_form_{row['id']}"):
                        e_nome = st.text_input("Nome (IT)", value=row['nome_it'])
                        e_prezzo = st.number_input("Prezzo (€)", value=row['prezzo'])
                        e_desc = st.text_area("Note", value=row['desc_it'])
                        e_foto = st.file_uploader("Cambia Foto", type=['jpg', 'jpeg', 'png'], key=f"foto_{row['id']}")
                        
                        if st.form_submit_button("Salva Modifiche"):
                            img_path = row['img_filename']
                            if e_foto:
                                img_path = f"immagini/{row['sku']}.jpg"
                                Image.open(e_foto).convert('RGB').save(os.path.join(BASE_DIR, img_path))
                            
                            conn.execute('''UPDATE charms SET nome_it=?, prezzo=?, desc_it=?, img_filename=? WHERE id=?''',
                                         (e_nome, e_prezzo, e_desc, img_path, row['id']))
                            conn.commit()
                            st.success("Aggiornato!")
                            st.rerun()

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Naviga:", ["Catalogo Generale", "Mia Collezione", "Nuovo Inserimento", "Ricerca Avanzata"])

if menu == "Catalogo Generale":
    st.header("📖 Catalogo Completo")
    search = st.text_input("🔍 Cerca rapida (Nome o SKU)")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search:
        mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]
    mostra_beads(df)

elif menu == "Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_p)

elif menu == "Nuovo Inserimento":
    st.header("➕ Aggiungi un nuovo Bead")
    foto = st.camera_input("Scatta Foto")
    with st.form("add_new"):
        c1, c2 = st.columns(2)
        with c1:
            f_sku = st.text_input("SKU")
            f_nome = st.text_input("Nome")
        with c2:
            f_brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Altro"])
            f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        if st.form_submit_button("Salva"):
            fname = f"immagini/{f_sku}.jpg"
            if foto: 
                Image.open(foto).convert('RGB').save(os.path.join(BASE_DIR, fname))
            conn.execute("INSERT INTO charms (brand, sku, img_filename, nome_it, prezzo, materiale, fuori_produzione, posseduto, desc_it) VALUES (?,?,?,?,?,?,0,0,'')", 
                         (f_brand, f_sku, fname, f_nome, 0.0, f_mat))
            conn.commit()
            st.success(f"Aggiunto: {fname}")
            st.rerun()

elif menu == "Ricerca Avanzata":
    st.header("🔍 Ricerca e Link Esterni")
    s_sku = st.text_input("Inserisci SKU per cercare su Google/eBay")
    if s_sku:
        st.markdown(f"[📸 Cerca {s_sku} su Google Immagini](https://www.google.it/search?q=trollbeads+sku+{s_sku}&tbm=isch)")
        st.markdown(f"[💰 Cerca {s_sku} su eBay](https://www.ebay.it/sch/i.html?_nkw=trollbeads+{s_sku})")
