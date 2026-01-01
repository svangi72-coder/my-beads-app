import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="Trollbeads Collector PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO INTELLIGENTE AGGIORNATO (CON I TUOI DATI CORRETTI) ---
conoscenza_beads = {
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

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER, posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. FUNZIONE VISUALIZZAZIONE COMPLETA (RIPRISTINATA) ---
def mostra_beads(df, titolo):
    st.header(titolo)
    if df.empty:
        st.info("Nessun bead trovato.")
        return
    
    for i, row in df.iterrows():
        with st.container():
            st.markdown(f"### {row['nome_it']}")
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                img_path = os.path.join(BASE_DIR, row['img_filename']) if row['img_filename'] else ""
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.markdown("📷 **Immagine non disponibile**")
            
            with col_info:
                st.write(f"**SKU:** {row['sku']}")
                st.write(f"**Designer:** {row['designer']}")
                st.write(f"**Materiale:** {row['materiale']}")
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Note:** {row['desc_it']}")
                
                # Azioni
                c1, c2 = st.columns(2)
                with c1:
                    lbl = "❌ Rimuovi dai miei" if row['posseduto'] else "❤️ Aggiungi ai miei"
                    if st.button(lbl, key=f"p_{row['id']}"):
                        conn.execute("UPDATE charms SET posseduto=? WHERE id=?", (1-row['posseduto'], row['id']))
                        conn.commit()
                        st.rerun()
                with c2:
                    if st.button("🗑️ Elimina dal DB", key=f"d_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
            st.divider()

# --- 5. LOGICA DI RICERCA SEPARATA ---
def cerca_info(testo):
    testo = testo.lower()
    for chiave, dati in conoscenza_beads.items():
        if chiave in testo:
            return dati
    return {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 6. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione"])

if menu == "🌐 Ricerca & Acquisizione":
    st.header("🌐 Ricerca e Acquisizione Separata")
    
    # Ricerca separata per Nome
    search_name = st.text_input("🔍 Cerca per Nome (es: balena)", key="s_name")
    info = cerca_info(search_name)
    
    if search_name:
        st.markdown(f"### [🔗 Cerca '{search_name}' su Google Immagini](https://www.google.it/search?q=trollbeads+{search_name}&tbm=isch)")
        
        with st.form("nuova_acquisizione"):
            st.subheader("Verifica e Salva nel Catalogo")
            c1, c2 = st.columns(2)
            with c1:
                w_sku = st.text_input("SKU ufficiale", value=info['sku'])
                w_nome = st.text_input("Nome del Bead", value=info['nome'] if info['nome'] else search_name.capitalize())
                w_des = st.text_input("Designer", value=info['designer'])
            with c2:
                w_pre = st.number_input("Prezzo (€)", value=info['prezzo'])
                w_mat = st.selectbox("Materiale", ["Vetro", "Argento 925", "Oro", "Pietra"], index=0 if info['materiale']=="Vetro" else 1)
                w_foto = st.file_uploader("Carica foto trovata", type=['jpg', 'png', 'jpeg'])
            
            w_note = st.text_area("Note e Storia", value=info['note'])
            
            if st.form_submit_button("✨ SALVA NEL CATALOGO GENERALE"):
                fname = f"immagini/{w_sku}.jpg"
                if w_foto:
                    Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                VALUES ('Trollbeads',?,?,?,?,?,?,?,0,0)''', 
                             (w_sku, w_nome, w_mat, w_des, w_pre, w_note, fname))
                conn.commit()
                st.success("Salvato!")

elif menu == "📖 Catalogo":
    df_all = pd.read_sql("SELECT * FROM charms", conn)
    mostra_beads(df_all, "📖 Catalogo Generale")

elif menu == "💍 Mia Collezione":
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads(df_my, "💍 La Mia Collezione")
