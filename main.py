import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE LOCALE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads Personal PRO", page_icon="💎", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, descrizione TEXT, foto_path TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 3. DIZIONARIO DI SUPPORTO (INTELLIGENZA LOCALE) ---
# Aggiungi qui i dati tecnici man mano che li scopri per non scriverli più
DIZIONARIO_RAPIDO = {
    "balena": {"sku": "TAGPE-00012", "nome": "Il Canto della Balena", "designer": "Morten Pol Engell Nørregård", "mat": "Vetro", "pre": 85.0, "desc": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni per comunicare con il suo balenottero."},
    "fede": {"sku": "TAGBE-10052", "nome": "Fede, Speranza e Carità", "designer": "Søren Nielsen", "mat": "Argento 925", "pre": 45.0, "desc": "I tre simboli classici: Croce, Ancora e Cuore."}
}

# --- 4. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["🔍 Ricerca e Acquisizione", "📖 La Mia Collezione", "💾 Backup"])

if menu == "🔍 Ricerca e Acquisizione":
    st.title("🌐 Centro Acquisizione Automatica")
    
    # Campo di ricerca principale
    query = st.text_input("🔍 Inserisci il nome del bead (es: balena)").lower().strip()
    
    # Logica di auto-completamento
    info = DIZIONARIO_RAPIDO.get(query, {"sku": "", "nome": query.capitalize(), "designer": "", "mat": "Argento 925", "pre": 0.0, "desc": ""})
    
    if query:
        st.subheader("🛠️ Strumenti di Ricerca Esterna")
        st.write("Usa questi link per trovare i dati corretti e la foto sul web:")
        
        c_web1, c_web2 = st.columns(2)
        with c_web1:
            st.link_button("📸 Trova Foto Ufficiale", f"https://www.google.it/search?q=trollbeads+{query.replace(' ', '+')}&tbm=isch")
        with c_web2:
            st.link_button("📜 Leggi Descrizione e Dati", f"https://www.google.it/search?q=site:trollbeads.com+{query.replace(' ', '+')}")

    st.divider()

    # SCHEDA TECNICA
    with st.form("form_acquisizione"):
        st.subheader("📝 Scheda del Bead")
        col1, col2 = st.columns(2)
        with col1:
            in_sku = st.text_input("SKU Tecnico", value=info['sku'])
            in_nome = st.text_input("Nome Ufficiale", value=info['nome'])
            in_des = st.text_input("Designer", value=info['designer'])
        with col2:
            in_pre = st.number_input("Prezzo (€)", value=float(info['pre']))
            lista_mat = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra"]
            idx_m = lista_mat.index(info['mat']) if info['mat'] in lista_mat else 0
            in_mat = st.selectbox("Materiale", lista_mat, index=idx_m)
            
        st.write("**📸 Immagine (Salva la foto da Google e caricala qui)**")
        # Su iPad, puoi salvare la foto da Safari nel Rullino e poi sceglierla qui
        in_foto = st.file_uploader("Carica l'immagine catturata", type=['jpg', 'jpeg', 'png'])
        
        in_desc = st.text_area("Descrizione (Significato del Bead)", value=info['desc'], height=150)
        
        if st.form_submit_button("💾 SALVA NEL DATABASE LOCALE"):
            if in_sku and in_nome:
                nome_f = f"{in_sku.replace('/', '_')}.jpg"
                path_rel = os.path.join('mie_immagini', nome_f)
                path_abs = os.path.join(BASE_DIR, path_rel)
                
                if in_foto:
                    Image.open(in_foto).convert('RGB').save(path_abs, "JPEG")
                
                conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, descrizione, foto_path) 
                                VALUES (?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_desc, path_rel))
                conn.commit()
                st.success(f"✅ {in_nome} salvato con successo!")
            else:
                st.error("Inserisci SKU e Nome.")

elif menu == "📖 La Mia Collezione":
    st.title("📖 Archivio Personale")
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
                if st.button("🗑️ Elimina", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Esporta Dati")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_beads.db")
