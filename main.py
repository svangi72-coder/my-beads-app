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

# --- 3. FUNZIONE VISUALIZZAZIONE SCHEDE ---
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
                if full_path and os.path.exists(full_path) and not os.path.isdir(full_path):
                    st.image(full_path, use_container_width=True)
                else:
                    st.warning("📷 Immagine mancante")

            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Marca:** {row['brand']} | **Designer:** {row['designer']}")
                st.write(f"**Materiale:** {row['materiale']} | **Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 In Prod.'}")
                
                t1, t2 = st.tabs(["📋 Info", "📝 Modifica"])
                with t1:
                    st.write(f"**Prezzo:** €{row['prezzo']} | **Note:** {row['desc_it']}")
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
                with t2:
                    with st.form(f"edit_{row['id']}"):
                        en_it = st.text_input("Nome", value=row['nome_it'])
                        en_sku = st.text_input("SKU", value=row['sku'])
                        en_des = st.text_input("Designer", value=row['designer'])
                        en_pre = st.number_input("Prezzo", value=float(row['prezzo']))
                        if st.form_submit_button("Aggiorna"):
                            conn.execute("UPDATE charms SET nome_it=?, sku=?, designer=?, prezzo=? WHERE id=?", (en_it, en_sku, en_des, en_pre, row['id']))
                            conn.commit(); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo & Ricerca", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione Web"])

if menu == "📖 Catalogo & Ricerca":
    st.header("📖 Catalogo Generale")
    f_testo = st.text_input("Filtra per nome o SKU")
    query = "SELECT * FROM charms"
    if f_testo:
        query += f" WHERE nome_it LIKE '%{f_testo}%' OR sku LIKE '%{f_testo}%'"
    df = pd.read_sql(query, conn)
    mostra_beads(df)

elif menu == "💍 Mia Collezione":
    st.header("💍 La Mia Collezione")
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_my)

elif menu == "🌐 Ricerca & Acquisizione Web":
    st.header("🌐 Centro Acquisizione Nuovi Beads")
    st.markdown("""
        <div class='web-box'>
        1. Inserisci lo SKU o il Nome che vuoi cercare.<br>
        2. Usa i link per trovare i dati ufficiali.<br>
        3. Compila la scheda qui sotto e salva nel Catalogo Generale.
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        search_q = st.text_input("Codice SKU o Nome da cercare", placeholder="Esempio: TAGBE-10052")
    
    if search_q:
        with c2:
            st.write("**Strumenti di ricerca:**")
            st.markdown(f"[📸 Google Immagini](https://www.google.it/search?q=trollbeads+{search_q}&tbm=isch)")
            st.markdown(f"[💰 Valutazione eBay](https://www.ebay.it/sch/i.html?_nkw=trollbeads+{search_q})")
        
        st.divider()
        st.subheader("📝 Scheda di Acquisizione")
        with st.form("web_acquisizione", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                w_sku = st.text_input("SKU ufficiale", value=search_q)
                w_nome = st.text_input("Nome del Bead (Italiano)")
                w_brand = st.selectbox("Marca", ["Trollbeads", "Pandora", "Ohm"])
                w_designer = st.text_input("Designer (es: Lise Aagaard)")
            with col_b:
                w_prezzo = st.number_input("Prezzo di listino (€)", min_value=0.0, step=0.5)
                w_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro", "Rame", "Ambra"])
                w_stato = st.checkbox("È un pezzo Retired (Fuori produzione)?")
                w_foto = st.file_uploader("Carica la foto trovata", type=['jpg', 'png', 'jpeg'])
            
            w_note = st.text_area("Note aggiuntive / Storia")
            
            if st.form_submit_button("✨ SALVA NEL CATALOGO GENERALE"):
                if w_sku and w_nome:
                    # Gestione Foto
                    fname = f"immagini/{w_sku}.jpg"
                    if w_foto:
                        Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    
                    conn.execute('''INSERT INTO charms 
                                    (brand, sku, nome_it, materiale, designer, prezzo, fuori_produzione, desc_it, img_filename, posseduto) 
                                    VALUES (?,?,?,?,?,?,?,?,?,0)''', 
                                 (w_brand, w_sku, w_nome, w_mat, w_designer, w_prezzo, 1 if w_stato else 0, w_note, fname))
                    conn.commit()
                    st.success(f"✅ {w_nome} ({w_sku}) è stato aggiunto al Catalogo Generale!")
                else:
                    st.error("Inserisci almeno SKU e Nome per salvare.")
