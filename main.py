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

# --- 2. DIZIONARIO INTELLIGENTE AGGIORNATO ---
conoscenza_beads = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Morten Pol Engell Nørregård",
        "materiale": "Vetro",
        "prezzo": 85.0,
        "note": "Una splendida vista sul mare tropicale: la megattera produce un fitto intreccio di suoni."
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

LISTA_MATERIALI = ["Argento 925", "Vetro", "Pietra", "Oro", "Rame", "Ambra"]

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

# --- 4. FUNZIONE VISUALIZZAZIONE CON FILTRI ---
def mostra_beads_con_filtri(df_input, titolo):
    st.header(titolo)
    
    # --- BARRA FILTRI ---
    with st.expander("🔍 Filtri Avanzati", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_nome = st.text_input("Cerca per nome/SKU", key=f"f_n_{titolo}")
        with c2:
            f_mat = st.multiselect("Materiale", LISTA_MATERIALI, key=f"f_m_{titolo}")
        with c3:
            f_stato = st.radio("Stato", ["Tutti", "In Produzione", "Retired"], key=f"f_s_{titolo}")

    # Applicazione Filtri al DataFrame
    df = df_input.copy()
    if f_nome:
        df = df[df['nome_it'].str.contains(f_nome, case=False) | df['sku'].str.contains(f_nome, case=False)]
    if f_mat:
        df = df[df['materiale'].isin(f_mat)]
    if f_stato == "Retired":
        df = df[df['fuori_produzione'] == 1]
    elif f_stato == "In Produzione":
        df = df[df['fuori_produzione'] == 0]

    if df.empty:
        st.info("Nessun bead trovato con questi filtri.")
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
                    st.warning("📷 Foto mancante")
            
            with col_info:
                st.write(f"**SKU:** {row['sku']} | **Designer:** {row['designer']}")
                st.write(f"**Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Note:** {row['desc_it']}")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    lbl = "❌ Rimuovi" if row['posseduto'] else "❤️ Aggiungi"
                    if st.button(lbl, key=f"btn_p_{row['id']}"):
                        conn.execute("UPDATE charms SET posseduto=? WHERE id=?", (1-row['posseduto'], row['id']))
                        conn.commit()
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ Elimina", key=f"btn_d_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
            st.divider()

# --- 5. NAVIGAZIONE ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione"])

if menu == "🌐 Ricerca & Acquisizione":
    st.header("🌐 Acquisizione Intelligente")
    search_input = st.text_input("🔍 Cerca Nome (es: fede o balena)").strip().lower()
    
    # Logica recupero dati da dizionario
    info = conoscenza_beads.get(search_input, {"sku":"", "nome":"", "designer":"", "materiale":"Argento 925", "prezzo":0.0, "note":""})
    # Se non trova nel dizionario ma c'è input, prova ricerca parziale
    if search_input and info["sku"] == "":
        for k, v in conoscenza_beads.items():
            if k in search_input: info = v; break

    if search_input:
        st.markdown(f"[📸 Foto su Google](https://www.google.it/search?q=trollbeads+{search_input})")
        
        with st.form("acq_form"):
            c1, c2 = st.columns(2)
            with c1:
                w_sku = st.text_input("SKU ufficiale", value=info['sku'])
                w_nome = st.text_input("Nome", value=info['nome'] if info['nome'] else search_input.capitalize())
                w_des = st.text_input("Designer", value=info['designer'])
            with c2:
                w_pre = st.number_input("Prezzo (€)", value=info['prezzo'])
                # FIX MATERIALE: Calcolo indice dinamico
                idx_m = LISTA_MATERIALI.index(info['materiale']) if info['materiale'] in LISTA_MATERIALI else 0
                w_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=idx_m)
                w_foto = st.file_uploader("Carica foto", type=['jpg', 'png', 'jpeg'])
            
            w_note = st.text_area("Note", value=info['note'])
            w_ret = st.checkbox("Fuori Produzione (Retired)")

            if st.form_submit_button("✨ SALVA NEL CATALOGO"):
                fname = f"immagini/{w_sku}.jpg"
                if w_foto:
                    Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                VALUES ('Trollbeads',?,?,?,?,?,?,?,0,?)''', 
                             (w_sku, w_nome, w_mat, w_des, w_pre, w_note, fname, 1 if w_ret else 0))
                conn.commit()
                st.success("Bead salvato!")

elif menu == "📖 Catalogo":
    df_all = pd.read_sql("SELECT * FROM charms", conn)
    mostra_beads_con_filtri(df_all, "📖 Catalogo Generale")

elif menu == "💍 Mia Collezione":
    df_my = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    mostra_beads_con_filtri(df_my, "💍 La Mia Collezione")
