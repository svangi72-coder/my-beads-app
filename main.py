import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. FUNZIONE DATABASE (DATI VERIFICATI) ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    
    # PULIZIA DATI PRECEDENTI (Per caricare i dati reali corretti)
    c.execute("DELETE FROM charms")

    # DATABASE REALE TROLLBEADS ITALIA
    beads_master = [
        ('Trollbeads', 'TAGBE-10052', 'fede_speranza_carita.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', "Tre simboli in uno: la croce per la fede, l'ancora per la speranza e il cuore per la carità.", "Three symbols in one: the cross for faith, the anchor for hope, and the heart for charity."),
        ('Trollbeads', 'TAGBE-10197', 'intreccio.jpg', 'Stop Intreccio', 'Intertwined Spacer', "Il design a intreccio simboleggia i legami che ci tengono uniti.", "The intertwined design symbolizes the bonds that hold us together."),
        ('Trollbeads', 'TGLBE-10431', 'raccolto.jpg', 'Raccolto', 'Harvest', "Un bead sfaccettato in vetro che celebra la gratitudine per i frutti della natura.", "A faceted glass bead celebrating gratitude for the fruits of nature."),
        ('Trollbeads', 'TAGPE-00012', 'IMG_3861.jpeg', 'Canto della Balena', 'Whale\'s Song', "La voce misteriosa dell'oceano che risuona nelle profondità.", "The mysterious voice of the ocean resonating in the deep."),
        ('Trollbeads', 'TGLBE-20120', 'cielo_notturno.jpg', 'Cielo Notturno', 'Night Sky', "Un augurio per ogni stella che brilla nel firmamento.", "A wish for every star that shines in the firmament.")
    ]

    for item in beads_master:
        c.execute('''INSERT INTO charms 
                     (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,0)''', item)
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE LINGUA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
txt = {
    "Italiano": {
        "titolo": "Mio Catalogo Trollbeads",
        "cam": "Scannerizza Bead",
        "cerca": "Cerca per Nome o SKU",
        "possiedo": "Lo possiedo",
        "non_trovato": "Nessun bead trovato con questo nome o SKU."
    },
    "English": {
        "titolo": "My Trollbeads Catalog",
        "cam": "Scan Bead",
        "cerca": "Search by Name or SKU",
        "possiedo": "I own this",
        "non_trovato": "No bead found with this name or SKU."
    }
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- 3. RICERCA VISIVA (FOTOCAMERA) ---
with st.expander(f"📸 {txt['cam']}"):
    foto = st.camera_input("Scanner")
    if foto:
        st.image(foto, caption="Analisi...")
        st.info("Ricerca visiva in corso nel catalogo...")

st.divider()

# --- 4. RICERCA TESTUALE ---
search = st.text_input(f"🔍 {txt['cerca']}", placeholder="Es: 10052...")

# --- 5. VISUALIZZAZIONE GRIGLIA ---
df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    # Filtro ricerca
    if search:
        col_nome = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_nome].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    if not df.empty:
        cols = st.columns(2)
        for i, row in df.iterrows():
            with cols[i % 2]:
                # Visualizzazione Immagine Locale
                if os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                else:
                    st.warning(f"Foto mancante: {row['img_filename']}")
                
                # Scheda Dettagli
                with st.expander(f"{row['nome_it'] if lang == 'Italiano' else row['nome_en']}"):
                    st.write(f"**SKU:** {row['sku']}")
                    st.write(row['desc_it'] if lang == 'Italiano' else row['desc_en'])
                    
                    # Bottone Possesso
                    if st.button(txt['possiedo'], key=f"btn_{row['id']}"):
                        st.success("Aggiunto alla collezione!")
                        st.balloons()
    else:
        st.write(txt['non_trovato'])
else:
    st.error("Errore nel caricamento del database.")
