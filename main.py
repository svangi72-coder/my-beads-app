import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image
import requests
from io import BytesIO

# --- 1. CONFIGURAZIONE LOCALE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Web Collector", page_icon="🌐", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. NAVIGAZIONE ---
menu = st.sidebar.radio("Menu", ["🌐 Ricerca & Estrazione Web", "💍 Mia Collezione", "💾 Backup"])

if menu == "🌐 Ricerca & Estrazione Web":
    st.title("🌐 Centro di Estrazione Dati Web")
    
    # CAMPO DI RICERCA WEB
    query = st.text_input("🔍 Cosa vuoi cercare sul Web?", placeholder="Es: Il canto della balena o TAGPE-00012")
    
    if query:
        st.subheader("🤖 Link per Estrazione Rapida")
        st.write("Usa questi link per trovare i dati. Su iPad, tieni premuto sull'immagine e seleziona 'Copia Indirizzo Immagine'.")
        
        c1, c2, c3 = st.columns(3)
        q_url = query.replace(" ", "+")
        with c1:
            st.link_button("📸 Trova Foto (Google)", f"https://www.google.it/search?q=trollbeads+{q_url}&tbm=isch")
        with c2:
            st.link_button("📝 Trova Dati e Storia", f"https://www.google.it/search?q=site:trollbeads.com+{q_url}")
        with c3:
            st.link_button("💰 Valore Mercato", f"https://www.ebay.it/sch/i.html?_nkw=trollbeads+{q_url}")

    st.divider()

    # SCHEDA DI ACQUISIZIONE
    with st.form("form_estrazione"):
        st.subheader("📝 Scheda Tecnica da Salvare")
        col_a, col_b = st.columns(2)
        with col_a:
            in_sku = st.text_input("SKU ufficiale trovato")
            in_nome = st.text_input("Nome ufficiale trovato", value=query.capitalize())
            in_des = st.text_input("Designer")
        with col_b:
            in_pre = st.number_input("Prezzo stimato (€)", step=1.0)
            in_mat = st.selectbox("Materiale", ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame"])
        
        # CAMPO DESCRIZIONE (Richiesto come Descrizione)
        in_desc = st.text_area("Descrizione (Incolla qui il significato trovato online)", height=150)
        
        # SISTEMA DI CATTURA IMMAGINE VIA URL
        st.write("**🖼️ Cattura Foto**")
        url_img = st.text_input("Incolla qui l'URL dell'immagine copiata da Safari")
        
        in_foto_file = st.file_uploader("Oppure carica la foto se l'hai salvata", type=['jpg', 'png', 'jpeg'])
        
        submit = st.form_submit_button("💾 SALVA NEL MIO DATABASE")
        
        if submit:
            if in_sku and in_nome:
                nome_f = f"{in_sku.replace('/', '_')}.jpg"
                path_rel = os.path.join('mie_immagini', nome_f)
                path_abs = os.path.join(BASE_DIR, path_rel)
                
                # Prova a scaricare dall'URL se fornito
                if url_img:
                    try:
                        resp = requests.get(url_img, timeout=10)
                        Image.open(BytesIO(resp.content)).convert('RGB').save(path_abs, "JPEG")
                        st.success("✅ Foto catturata dall'URL!")
                    except:
                        st.error("❌ Impossibile catturare l'immagine dall'URL (Sito protetto). Caricala manualmente.")
                
                # Se c'è un file caricato manualmente, vince sull'URL
                if in_foto_file:
                    Image.open(in_foto_file).convert('RGB').save(path_abs, "JPEG")
                
                conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                                VALUES (?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_desc, path_rel))
                conn.commit()
                st.success(f"Bead '{in_nome}' salvato correttamente!")
            else:
                st.error("Inserisci SKU e Nome per salvare.")

elif menu == "💍 Mia Collezione":
    st.title("💍 Il Mio Archivio")
    df = pd.read_sql("SELECT * FROM charms", conn)
    for _, row in df.iterrows():
        with st.expander(f"{row['nome']} ({row['sku']})"):
            c1, c2 = st.columns([1, 2])
            with c1:
                p = os.path.join(BASE_DIR, row['foto_path'])
                if os.path.exists(p): st.image(p, use_container_width=True)
            with c2:
                st.write(f"**Materiale:** {row['materiale']} | **Designer:** {row['designer']}")
                st.write(f"**Prezzo:** €{row['prezzo']}")
                st.info(f"**Descrizione:** {row['descrizione']}")
                if st.button("Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Dati")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_beads.db")
