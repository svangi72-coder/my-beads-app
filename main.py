import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. FUNZIONE DATABASE ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER,
                  posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. MENU E NAVIGAZIONE ---
st.sidebar.title("Menu")
menu = st.sidebar.radio("Vai a:", ["Catalogo", "Aggiungi Nuovo", "Ricerca Web"])

# --- SEZIONE: AGGIUNGI MANUALE (CON FOTO) ---
if menu == "Aggiungi Nuovo":
    st.header("➕ Aggiungi un nuovo Bead")
    
    with st.form("manual_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_sku = st.text_input("SKU (es. TAGBE-12345)")
            new_nome = st.text_input("Nome")
            new_designer = st.text_input("Designer")
        with col2:
            new_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=0.5)
            new_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
            new_retired = st.checkbox("Fuori Produzione (Retired)")

        new_desc = st.text_area("Descrizione")
        
        # CAMPO FOTO
        uploaded_file = st.file_uploader("Scegli o scatta una foto del bead", type=['jpg', 'jpeg', 'png'])
        
        submitted = st.form_submit_button("Salva nel Portagioie")
        
        if submitted:
            # Salviamo il nome del file nel database
            img_name = f"{new_sku}.jpg" if new_sku else "temp.jpg"
            
            # Se è stata caricata una foto, la salviamo (temporaneamente sul server)
            if uploaded_file is not None:
                img = Image.open(uploaded_file)
                img.save(img_name) # Questo salva il file nella cartella dell'app
            
            c = conn.cursor()
            c.execute('''INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,0)''', 
                      ('Trollbeads', new_sku, img_name, new_nome, new_nome, new_desc, new_prezzo, new_designer, new_mat, 1 if new_retired else 0))
            conn.commit()
            st.success(f"Bead {new_nome} salvato! Nota: Per rendere la foto permanente, caricala anche su GitHub con il nome {img_name}")

# --- SEZIONE: CATALOGO (MOSTRA FOTO CARICATA) ---
elif menu == "Catalogo":
    st.header("💎 Il Mio Catalogo")
    search = st.text_input("🔍 Cerca per Nome o SKU")
    
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search:
        df = df[df['nome_it'].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    for i, row in df.iterrows():
        c_img, c_info = st.columns([1, 4])
        with c_img:
            # Cerca la foto caricata o quella su GitHub
            if row['img_filename'] and os.path.exists(row['img_filename']):
                st.image(row['img_filename'], width=85)
            else:
                st.write("🖼️ (No foto)")
        
        with c_info:
            with st.expander(f"**{row['nome_it']}** ({row['sku']})"):
                if row['img_filename'] and os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']}")
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Descrizione:** {row['desc_it']}")
                if st.button("Lo possiedo", key=f"btn_{row['id']}"):
                    st.balloons()

# --- SEZIONE: RICERCA WEB ---
else:
    st.header("🌐 Ricerca Rapida")
    q = st.text_input("Cerca foto ufficiale per SKU")
    if q:
        st.markdown(f"[🔍 Clicca qui per vedere le foto di {q} su Google](https://www.google.it/search?q=trollbeads+{q}&tbm=isch)")
