import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. FUNZIONE DATABASE (DATI AGGIORNATI) ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    # Creazione tabella con i nuovi campi richiesti
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione BOOLEAN,
                  posseduto BOOLEAN)''')
    
    # Pulizia per caricare i nuovi dati completi
    c.execute("DELETE FROM charms")

    # DATABASE REALE TROLLBEADS ITALIA CON NUOVI DATI
    # Struttura: (Brand, SKU, Immagine, Nome IT, Nome EN, Desc IT, Desc EN, Prezzo, Designer, Materiale, Fuori Produzione)
    beads_master = [
        ('Trollbeads', 'TAGBE-10052', 'fede_speranza_carita.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', "Croce, ancora e cuore.", "Cross, anchor and heart.", 45.0, 'Søren Nielsen', 'Argento 925', False),
        ('Trollbeads', 'TAGBE-10197', 'intreccio.jpg', 'Stop Intreccio', 'Intertwined Spacer', "Simbolo di legami uniti.", "Symbol of bonds.", 35.0, 'Søren Nielsen', 'Argento 925', False),
        ('Trollbeads', 'TGLBE-10431', 'raccolto.jpg', 'Raccolto', 'Harvest', "Gratitudine per la natura.", "Gratitude for nature.", 55.0, 'Lise Aagaard', 'Vetro / Argento', True),
        ('Trollbeads', 'TAGPE-00012', 'IMG_3861.jpeg', 'Canto della Balena', 'Whale\'s Song', "Voce misteriosa dell'oceano.", "Voice of the ocean.", 55.0, 'Lise Aagaard', 'Vetro / Argento', False),
        ('Trollbeads', 'TGLBE-20120', 'cielo_notturno.jpg', 'Cielo Notturno', 'Night Sky', "Stelle nel firmamento.", "Stars in the sky.", 55.0, 'Lise Aagaard', 'Vetro / Argento', False)
    ]

    for item in beads_master:
        c.execute('''INSERT INTO charms 
                     (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, prezzo, designer, materiale, fuori_produzione, posseduto) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,0)''', item)
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE LINGUA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
t = {
    "Italiano": {"prezzo": "Prezzo", "designer": "Designer", "materiale": "Materiale", "stato": "Stato", "ritirato": "Fuori Produzione (Retired)", "attivo": "In Produzione"},
    "English": {"prezzo": "Price", "designer": "Designer", "materiale": "Material", "stato": "Status", "ritirato": "Retired", "attivo": "Active"}
}[lang]

st.title("💎 My Detailed Beads Catalog")

# --- 3. RICERCA ---
search = st.text_input("🔍 Cerca per Nome o SKU", placeholder="Es: 10052...")

# --- 4. VISUALIZZAZIONE ---
df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_nome = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_nome].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    # Layout Lista
    for i, row in df.iterrows():
        col_img, col_info = st.columns([1, 4]) # 1 parte per l'immagine, 4 per il testo
        
        with col_img:
            # MINIATURA (Piccola nella lista)
            if os.path.exists(row['img_filename']):
                st.image(row['img_filename'], width=80) # Imposta la larghezza a 80 pixel
            else:
                st.write("🖼️")

        with col_info:
            nome = row['nome_it'] if lang == "Italiano" else row['nome_en']
            # ESPANDER (Cliccando qui si apre il dettaglio)
            with st.expander(f"**{nome}** - {row['sku']}"):
                # IMMAGINE GRANDE (Solo dentro l'espansione)
                if os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                
                # DATI AGGIUNTIVI
                st.write(f"**{t['designer']}:** {row['designer']}")
                st.write(f"**{t['materiale']}:** {row['materiale']}")
                st.write(f"**{t['prezzo']}:** €{row['prezzo']:.2f}")
                
                # Stato Fuori Produzione
                stato_testo = t['ritirato'] if row['fuori_produzione'] else t['attivo']
                colore = "red" if row['fuori_produzione'] else "green"
                st.markdown(f"**{t['stato']}:** :{colore}[{stato_testo}]")
                
                st.write("---")
                st.write(row['desc_it'] if lang == "Italiano" else row['desc_en'])
                
                if st.button(f"Possiedo", key=f"btn_{row['id']}"):
                    st.success("Aggiunto!")

else:
    st.error("Database non caricato correttamente.")
