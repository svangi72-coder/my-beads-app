import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI E PAGINA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

# Crea la cartella fisica se non esiste
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
    .web-section { background-color: #F1F3F6; padding: 20px; border-radius: 15px; margin-top: 20px; }
    .link-button {
        text-decoration: none; padding: 8px 15px; border-radius: 8px;
        background-color: #FFFFFF; color: #1A2530; font-weight: bold;
        display: inline-block; margin: 5px; border: 1px solid #D1D3D8; font-size: 0.9rem;
    }
    .link-button:hover { background-color: #71797E; color: white; }
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
    
    c.execute("SELECT count(*) FROM charms")
    if c.fetchone()[0] == 0:
        # Percorsi aggiornati con prefisso immagini/
        beads_master = [
            ('Trollbeads', 'TAGBE-10052', 'immagini/fede.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', 'Cuore, ancora e croce', 45.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TAGPE-00012', 'immagini/balena.jpg', 'Canto della Balena', 'Whale Song', 'Vetro blu intenso', 55.0, 'Lise Aagaard', 'Vetro', 0, 0)
        ]
        c.executemany('''INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 3. FUNZIONE VISUALIZZAZIONE ---
def mostra_beads(dataframe, is_collezione_personale=False):
    if dataframe.empty:
        st.warning("Nessun bead trovato.")
        return
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'><div class='bead-title'>{row['nome_it']}</div></div>", unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 3])
            with col_img:
                img_relative_path = row['img_filename']
                # Costruisce il percorso assoluto per caricare il file correttamente
                full_img_path = os.path.join(BASE_DIR, img_relative_path) if img_relative_path else ""
                
                if full_img_path and os.path.exists(full_img_path):
                    st.image(full_img_path, use_container_width=True)
                else:
                    st.markdown("<h2 style='text-align: center;'>🖼️</h2>", unsafe_allow_html=True)
                    st.caption(f"Percorso: {img_relative_path}")
            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Eng:** {row['nome_en']} | **Brand:** {row['brand']}")
                with st.expander("Dettagli e Azioni"):
                    st.write(f"**Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']}")
                    st.write(f"**Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 Attivo'}")
                    st.write(f"**Note:** {row['desc_it']}")
                    
                    b_a, b_b = st.columns(2)
                    with b_a:
                        label = "❌ Rimuovi" if row['posseduto'] else "❤️ Possiedo"
                        if st.button(label, key=f"act_{row['id']}"):
                            val = 1 - row['posseduto']
                            conn.execute("UPDATE charms SET posseduto = ? WHERE id = ?", (val, row['id']))
                            conn.commit()
                            st.rerun()
                    with b_b:
                        if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                            conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                            conn.commit()
                            st.rerun()
        st.write("")

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Naviga:", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Ricerca Avanzata", "Statistiche"])

if menu == "Catalogo Generale":
    st.header("📖 Catalogo Completo")
    search = st.text_input("🔍 Ricerca rapida")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search:
        mask = df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)
        df = df[mask]
    mostra_beads(df)

elif menu == "Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_p, is_collezione_personale=True)

elif menu == "Aggiungi Nuovo":
    st.header("➕ Nuovo Inserimento")
    metodo = st.radio("Foto:", ["Fotocamera iPad 📸", "Galleria 🖼️"])
    foto = st.camera_input("Scatta") if metodo == "Fotocamera iPad 📸" else st.file_uploader("Carica", type=['jpg','png','jpeg'])
    
    with st.form("form_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_sku = st.text_input("SKU")
            f_nome_it = st.text_input("Nome (IT)")
            f_nome_en = st.text_input("Nome (EN)")
        with c2:
            f_brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Ohm Beads", "Altro"])
            f_prezzo = st.number_input("Prezzo (€)", min_value=0.0)
            f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro", "Rame"])
            f_ret = st.checkbox("Retired")
        f_desc = st.text_area("Descrizione")
        
        if st.form_submit_button("✨ Salva nel Catalogo"):
            relative_name = f"immagini/{f_sku}.jpg" if f_sku else "immagini/temp.jpg"
            if foto:
                full_save_path = os.path.join(BASE_DIR, relative_name)
                Image.open(foto).convert('RGB').save(full_save_path)
            
            conn.execute('''INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, prezzo, materiale, fuori_produzione, posseduto) 
                            VALUES (?,?,?,?,?,?,?,?,?,0)''', 
                         (f_brand, f_sku, relative_name, f_nome_it, f_nome_en, f_desc, f_prezzo, f_mat, 1 if f_ret else 0))
            conn.commit()
            st.success(f"Salvato correttamente come {relative_name}")

elif menu == "Ricerca Avanzata":
    st.header("🔍 Ricerca Integrata (DB + Web)")
    with st.expander("🛠️ Filtri Database", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            s_brand = st.multiselect("Brand", ["Trollbeads", "Pandora", "Ohm Beads"])
            s_mat = st.multiselect("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        with c2:
            s_sku = st.text_input("Cerca SKU")
            s_parola = st.text_input("Cerca Nome/Parola")
        with c3:
            s_stato = st.radio("Produzione", ["Tutti", "Attivi", "Retired"])
            s_web = st.checkbox("Mostra link Google/eBay", value=True)

    query = "SELECT * FROM charms WHERE 1=1"
    params = []
    if s_brand: query += f" AND brand IN ({','.join(['?']*len(s_brand))})"; params.extend(s_brand)
    if s_mat: query += f" AND materiale IN ({','.join(['?']*len(s_mat))})"; params.extend(s_mat)
    if s_sku: query += " AND sku LIKE ?"; params.append(f"%{s_sku}%")
    if s_parola: query += " AND (nome_it LIKE ? OR nome_en LIKE ? OR desc_it LIKE ?)"; params.extend([f"%{s_parola}%"]*3)
    if s_stato == "Attivi": query += " AND fuori_produzione = 0"
    elif s_stato == "Retired": query += " AND fuori_produzione = 1"
    
    df_f = pd.read_sql(query, conn, params=params)
    
    if s_web and (s_sku or s_parola):
        st.markdown("<div class='web-section'>", unsafe_allow_html=True)
        q_web = f"trollbeads {s_sku} {s_parola}".strip()
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1: st.markdown(f"<a href='https://www.google.it/search?q={q_web}&tbm=isch' target='_blank' class='link-button'>📸 Google Immagini</a>", unsafe_allow_html=True)
        with col_w2: st.markdown(f"<a href='https://www.ebay.it/sch/i.html?_nkw={q_web}' target='_blank' class='link-button'>💰 Valore eBay</a>", unsafe_allow_html=True)
        with col_w3: st.markdown(f"<a href='https://www.trollbeads.com/da-dk/search?q={s_sku}' target='_blank' class='link-button'>🌍 Trollbeads Global</a>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    mostra_beads(df_f)

elif menu == "Statistiche":
    st.header("📊 Statistiche")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if not df_p.empty:
        c1, c2 = st.columns(2)
        c1.metric("Pezzi Totali", len(df_p))
        c2.metric("Valore Stimato", f"€{df_p['prezzo'].sum():.2f}")
        st.bar_chart(df_p['materiale'].value_counts())
    else:
        st.info("Aggiungi beads alla tua collezione per vedere i dati.")
