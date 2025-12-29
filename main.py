import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. FUNZIONE DATABASE CON RESET STRUTTURA ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    
    # FORZIAMO IL RESET: Eliminiamo la vecchia tabella incompatibile
    c.execute("DROP TABLE IF EXISTS charms")
    
    # Creazione tabella con TUTTE le 13 colonne richieste
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER,
                  posseduto INTEGER)''')

    # DATI REALI VERIFICATI (12 valori per riga, l'ID è automatico)
    beads_master = [
        ('Trollbeads', 'TAGBE-10052', 'fede_speranza_carita.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', "Croce, ancora e cuore.", "Cross, anchor and heart.", 45.0, 'Søren Nielsen', 'Argento 925', 0, 0),
        ('Trollbeads', 'TAGBE-10197', 'intreccio.jpg', 'Stop Intreccio', 'Intertwined Spacer', "Simbolo di legami uniti.", "Symbol of bonds.", 35.0, 'Søren Nielsen', 'Argento 925', 0, 0),
        ('Trollbeads', 'TGLBE-10431', 'raccolto.jpg', 'Raccolto', 'Harvest', "Gratitudine per la natura.", "Gratitude for nature.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 1, 0),
        ('Trollbeads', 'TGLBE-10425', 'canto_balena.jpg', 'Canto della Balena', 'Whale\'s Song', "Voce misteriosa dell'oceano.", "Voice of the ocean.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0),
        ('Trollbeads', 'TGLBE-20120', 'cielo_notturno.jpg', 'Cielo Notturno', 'Night Sky', "Stelle nel firmamento.", "Stars in the sky.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0)
    ]

    # Inserimento: 12 punti interrogativi per i dati
    c.executemany('''INSERT INTO charms 
                     (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, prezzo, designer, materiale, fuori_produzione, posseduto) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE INTERFACCIA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
t = {
    "Italiano": {"prezzo": "Prezzo", "des": "Designer", "mat": "Materiale", "status": "Stato", "retired": "Fuori Produzione", "active": "In Produzione"},
    "English": {"prezzo": "Price", "des": "Designer", "mat": "Material", "status": "Status", "retired": "Retired", "active": "Active"}
}[lang]

st.title("💎 My Beads Catalog")

# --- 3. RICERCA ---
search = st.text_input("🔍 Cerca per Nome o SKU", placeholder="Es: 10052...")

# --- 4. VISUALIZZAZIONE ---
df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    for i, row in df.iterrows():
        # Layout con MINIATURA (width=85)
        col_img, col_info = st.columns([1, 4])
        
        with col_img:
            if os.path.exists(row['img_filename']):
                st.image(row['img_filename'], width=85)
            else:
                st.write("🖼️")

        with col_info:
            nome_display = row['nome_it'] if lang == "Italiano" else row['nome_en']
            with st.expander(f"**{nome_display}** ({row['sku']})"):
                # Foto GRANDE solo nell'espansione
                if os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**{t['des']}:** {row['designer']}")
                    st.write(f"**{t['mat']}:** {row['materiale']}")
                with c2:
                    st.write(f"**{t['prezzo']}:** €{row['prezzo']:.2f}")
                    color = "red" if row['fuori_produzione'] else "green"
                    label = t['retired'] if row['fuori_produzione'] else t['active']
                    st.markdown(f"**{t['status']}:** :{color}[{label}]")
                
                st.write("---")
                st.write(row['desc_it'] if lang == "Italiano" else row['desc_en'])
                
                if st.button(f"Lo possiedo", key=f"p_{row['id']}"):
                    st.success("Aggiunto!")
