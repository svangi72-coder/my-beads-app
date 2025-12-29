import streamlit as st
import sqlite3
import pandas as pd

# --- 1. FUNZIONE DATABASE ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_url TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    
    # Lista Aggiornata con link stabili
    trollbeads_master = [
        ('Trollbeads', 'TAGBE-10197', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw1873836d/images/TAGBE-10197.jpg', 'Sogno a occhi aperti', 'Daydream', 'Libera la tua mente e vola con la fantasia.', 'Free your mind and fly with imagination.'),
        ('Trollbeads', 'TAGBE-00001', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw61e86895/images/TAGBE-00001.jpg', 'Quadrifoglio', 'Four-leaf Clover', 'Simbolo universale di fortuna e speranza.', 'Universal symbol of luck and hope.'),
        ('Trollbeads', 'TGLBE-10431', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw9e663806/images/TGLBE-10431.jpg', 'Vetro del Deserto', 'Desert Glass', 'Ispirato ai colori caldi delle dune sahariane.', 'Inspired by the warm colors of Saharan dunes.'),
        ('Trollbeads', 'TAGBE-10052', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw5b404439/images/TAGBE-10052.jpg', 'Elefante', 'Elephant', 'Forza, saggezza e memoria infinita.', 'Strength, wisdom and infinite memory.')
    ]

    for item in trollbeads_master:
        c.execute('''INSERT OR IGNORE INTO charms 
                     (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,0)''', item)
    conn.commit()
    return conn

conn = init_db()

# --- 2. INTERFACCIA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
txt = {
    "Italiano": {"titolo": "Catalogo Beads", "cerca": "Cerca nella Collezione", "dettagli": "Vedi Dettagli", "info": "Informazioni Tecniche"},
    "English": {"titolo": "Beads Catalog", "cerca": "Search Collection", "dettagli": "View Details", "info": "Technical Info"}
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- 3. RICERCA ---
search = st.text_input(txt['cerca'], placeholder="Es: Daydream...")

df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    # Griglia a 2 colonne ottimizzata per iPhone
    cols = st.columns(2)
    for i, row in df.iterrows():
        with cols[i % 2]:
            # Immagine con gestione errore se il link non carica
            st.image(row['img_url'], use_container_width=True)
            
            # Espander per i dettagli
            with st.expander(f"🔍 {row['nome_it'] if lang == 'Italiano' else row['nome_en']}"):
                st.write(f"**SKU:** {row['sku']}")
                st.write(f"**Brand:** {row['brand']}")
                st.write(f"---")
                st.write(row['desc_it'] if lang == 'Italiano' else row['desc_en'])
                
                # Bottone per stato posseduto
                if st.button(f"Possiedo", key=f"btn_{row['id']}"):
                    st.balloons()
                    st.success("Aggiunto!")

else:
    st.warning("Database vuoto.")
