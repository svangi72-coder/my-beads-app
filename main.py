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
    .bead-title { color: #1A2530; font-family: 'serif'; font-weight: bold; font-size: 1.6rem; }
    .filter-box { background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #DDE1E6; margin-bottom: 20px; }
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

# --- 3. FUNZIONE VISUALIZZAZIONE ---
def mostra_beads(dataframe):
    if dataframe.empty:
        st.info("Nessun bead trovato.")
        return
    
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='bead-title'>{row['nome_it']}</div>", unsafe_allow_html=True)
            
            col_img, col_info = st.columns([1.2, 3])
            
            with col_img:
                img_rel = row['img_filename']
                full_path = os.path.join(BASE_DIR, img_rel) if img_rel else ""
                
                if full_path and os.path.exists(full_path) and not os.path.isdir(full_path):
                    st.image(full_path, use_container_width=True)
                else:
                    st.warning("⚠️ Foto mancante")
                    # CORRETTO: Ricerca Web intelligente
                    q_img = f"trollbeads {row['sku']} {row['nome_it']}".replace(" ", "+")
                    url_google = f"https://www.google.it/search?q={q_img}&tbm=isch"
                    st.markdown(f"[🔍 Trova foto su Google]({url_google})")
                    
                    up_file = st.file_uploader("Carica foto", type=['jpg','jpeg','png'], key=f"up_{row['id']}")
                    if up_file:
                        clean_sku = str(row['sku']).replace("/", "_") if row['sku'] else f"bead_{row['id']}"
                        new_rel_path = f"immagini/{clean_sku}.jpg"
                        new_full_path = os.path.join(BASE_DIR, new_rel_path)
                        
                        img = Image.open(up_file)
                        img.convert('RGB').save(new_full_path, "JPEG")
                        
                        conn.execute("UPDATE charms SET img_filename=? WHERE id=?", (new_rel_path, row['id']))
                        conn.commit()
                        st.success("Foto salvata!")
                        st.rerun()

            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Marca:** {row['brand']} | **Materiale:** {row['materiale']}")
                
                t_info, t_edit = st.tabs(["📋 Dettagli", "📝 Modifica"])
                
                with t_info:
                    st.write(f"**Prezzo:** €{row['prezzo']} | **Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 In Prod.'}")
                    st.write(f"**Note:** {row['desc_it']}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        lbl = "❌ Rimuovi dai miei" if row['posseduto'] else "❤️ Aggiungi ai miei"
                        if st.button(lbl, key=f"p_{row['id']}"):
                            conn.execute("UPDATE charms SET posseduto=? WHERE id=?", (1-row['posseduto'], row['id']))
                            conn.commit(); st.rerun()
                    with c2:
                        if st.button("🗑️ Elimina", key=f"d_{row['id']}"):
                            conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                            conn.commit(); st.rerun()
                
                with t_edit:
                    with st.form(f"edit_{row['id']}"):
                        n_nome = st.text_input("Nome", value=row['nome_it'])
                        n_prezzo = st.number_input("Prezzo", value=float(row['prezzo']))
                        n_desc = st.text_area("Note", value=row['desc_it'])
                        if st.form_submit_button("Salva"):
                            conn.execute("UPDATE charms SET nome_it=?, prezzo=?, desc_it=? WHERE id=?", (n_nome, n_prezzo, n_desc, row['id']))
                            conn.commit(); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli Sezione:", ["📖 Catalogo & Ricerca", "💍 Mia Collezione", "➕ Nuovo Inserimento"])

if menu == "📖 Catalogo & Ricerca":
    st.header("🔍 Ricerca Avanzata")
    
    with st.container():
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            f_testo = st.text_input("Nome o Parola")
            f_sku = st.text_input("Cerca SKU")
        with col2:
            f_brand = st.multiselect("Brand", ["Trollbeads", "Pandora", "Ohm"])
            f_mat = st.multiselect("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        with col3:
            f_stato = st.radio("Stato", ["Tutti", "In Produzione", "Retired"])
        st.markdown("</div>", unsafe_allow_html=True)

    query = "SELECT * FROM charms WHERE 1=1"
    params = []
    if f_testo: query += " AND (nome_it LIKE ? OR desc_it LIKE ?)"; params.extend([f"%{f_testo}%"]*2)
    if f_sku: query += " AND sku LIKE ?"; params.append(f"%{f_sku}%")
    if f_brand: query += f" AND brand IN ({','.join(['?']*len(f_brand))})"; params.extend(f_brand)
    if f_mat: query += f" AND materiale IN ({','.join(['?']*len(f_mat))})"; params.extend(f_mat)
    if f_stato == "In Produzione": query += " AND fuori_produzione = 0"
    elif f_stato == "Retired": query += " AND fuori_produzione = 1"
    
    df = pd.read_sql(query, conn, params=params)
    mostra_beads(df)

elif menu == "💍 Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_my)

elif menu == "➕ Nuovo Inserimento":
    st.header("➕ Aggiungi Nuovo")
    with st.form("new_bead"):
        c1, c2 = st.columns(2)
        with c1:
            n_sku = st.text_input("SKU")
            n_nome = st.text_input("Nome")
        with c2:
            n_brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Ohm"])
            n_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        
        foto = st.camera_input("Foto")
        
        if st.form_submit_button("Inserisci"):
            # Percorso salvato come immagini/nome.jpg
            path_foto = f"immagini/{n_sku}.jpg" if n_sku else ""
            if foto and n_sku:
                full_save_path = os.path.join(BASE_DIR, path_foto)
                Image.open(foto).convert('RGB').save(full_save_path, "JPEG")
            
            conn.execute("INSERT INTO charms (brand, sku, nome_it, materiale, img_filename, posseduto, fuori_produzione, prezzo, desc_it) VALUES (?,?,?,?,?,0,0,0.0,'')", 
                         (n_brand, n_sku, n_nome, n_mat, path_foto))
            conn.commit(); st.success("Aggiunto!")
