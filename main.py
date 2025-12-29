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
    
    # Pulizia per test (Rimuovi questa riga dopo il primo test riuscito)
    c.execute("DELETE FROM charms")

    # DATI CON LINK OTTIMIZZATI
    trollbeads_master = [
        ('Trollbeads', 'TAGBE-10197', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw1873836d/images/TAGBE-10197.jpg', 'Sogno a occhi aperti', 'Daydream', 'Libera la mente.', 'Free your mind.'),
        ('Trollbeads', 'TAGBE-00001', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw61e86895/images/TAGBE-00001.jpg', 'Quadrifoglio', 'Four-leaf Clover', 'Fortuna universale.', 'Universal luck.'),
        ('Trollbeads', 'TGLBE-10431', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw9e663806/images/TGLBE-10431.jpg', 'Vetro del Deserto', 'Desert Glass', 'Sabbie dorate.', 'Golden sands.'),
        ('Trollbeads', 'TAGBE-10052', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw5b404439/images/TAGBE-10052.jpg', 'Elefante', 'Elephant', 'Saggezza e forza.', 'Wisdom and strength.')
    ]

    for item in trollbeads_master:
        c.execute('''INSERT INTO charms 
                     (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,0)''', item)
    conn.commit()
    return conn

conn = init_db()

# --- 2. INTERFACCIA ---
st.title("💎 Beads Catalog")

# Lingua sidebar
lang = st.sidebar.selectbox("Lingua", ["Italiano", "English"])

# --- 3. RICERCA ---
search = st.text_input("🔍 Cerca per nome o SKU", placeholder="Es: Elephant...")

# Leggiamo i dati
df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    # Layout a 2 colonne per iPhone
    cols = st.columns(2)
    for i, row in df.iterrows():
        with cols[i % 2]:
            # TRUCCO PER LE IMMAGINI: Se il link fallisce, mostriamo un testo
            try:
                st.image(row['img_url'], use_container_width=True)
            except:
                st.warning("⚠️ Immagine non caricata")
            
            # Espandibile per i dettagli
            with st.expander(f"ℹ️ {row['nome_it'] if lang == 'Italiano' else row['nome_en']}"):
                st.write(f"**Brand:** {row['brand']}")
                st.write(f"**SKU:** {row['sku']}")
                st.write(row['desc_it'] if lang == 'Italiano' else row['desc_en'])
                if st.button(f"Lo possiedo", key=f"p_{row['id']}"):
                    st.success("Aggiunto!")
else:
    st.error("Nessun dato trovato nel database.")
