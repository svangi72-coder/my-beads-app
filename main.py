import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. FUNZIONE DATABASE & DATI ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    
    # Lista Master (Puoi cambiare i nomi dei file con quelli che carichi su GitHub)
    beads_master = [
        ('Trollbeads', 'TAGBE-10197', 'sogno.jpg', 'Sogno a occhi aperti', 'Daydream', 'Libera la mente.', 'Free your mind.'),
        ('Trollbeads', 'TAGBE-00001', 'quadrifoglio.jpg', 'Quadrifoglio', 'Four-leaf Clover', 'Fortuna.', 'Luck.'),
        ('Trollbeads', 'TGLBE-10431', 'vetro_deserto.jpg', 'Vetro del Deserto', 'Desert Glass', 'Sabbie dorate.', 'Golden sands.')
        # Aggiungi qui gli altri 27 che avevamo listato prima...
    ]

    for item in beads_master:
        c.execute('''INSERT OR IGNORE INTO charms 
                     (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,0)''', item)
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE LINGUA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
txt = {
    "Italiano": {
        "titolo": "Mio Catalogo Beads",
        "cam": "Inquadra per Ricerca Visiva",
        "cerca": "Cerca nella Collezione",
        "possiedo": "Lo possiedo",
        "dettagli": "Dettagli"
    },
    "English": {
        "titolo": "My Beads Catalog",
        "cam": "Scan for Visual Search",
        "cerca": "Search Collection",
        "possiedo": "I own this",
        "dettagli": "Details"
    }
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- 3. RICERCA VISIVA (FOTOCAMERA) ---
with st.expander(f"📸 {txt['cam']}"):
    foto = st.camera_input("Scanner")
    if foto:
        st.image(foto, caption="Analisi immagine...")
        st.info("Confronto con il database in corso...")

st.divider()

# --- 4. RICERCA TESTUALE ---
search = st.text_input(f"🔍 {txt['cerca']}", placeholder="Es: Daydream o TAGBE...")

# --- 5. VISUALIZZAZIONE GRIGLIA & SCHEDE ---
df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    cols = st.columns(2)
    for i, row in df.iterrows():
        with cols[i % 2]:
            # Gestione Immagine Locale
            if os.path.exists(row['img_filename']):
                st.image(row['img_filename'], use_container_width=True)
            else:
                # Se la foto non c'è ancora su GitHub, mostra un box grigio
                st.info(f"Carica {row['img_filename']} su GitHub")
            
            # Scheda Espandibile per Dettagli
            with st.expander(f"{row['nome_it'] if lang == 'Italiano' else row['nome_en']}"):
                st.caption(f"SKU: {row['sku']} | {row['brand']}")
                st.write(row['desc_it'] if lang == 'Italiano' else row['desc_en'])
                
                # --- 6. GESTIONE POSSESSO ---
                if st.button(txt['possiedo'], key=f"btn_{row['id']}"):
                    st.success("Aggiunto al portagioie!")
                    st.balloons()
else:
    st.warning("Database non ancora popolato.")
