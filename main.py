import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. FUNZIONE DATABASE (STRUTTURA COMPLETA) ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    # Creiamo la tabella con TUTTI i campi richiesti
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER,
                  posseduto INTEGER)''')
    
    # Inseriamo i dati reali solo se il database è appena stato creato (vuoto)
    c.execute("SELECT count(*) FROM charms")
    if c.fetchone()[0] == 0:
        beads_master = [
            ('Trollbeads', 'TAGBE-10052', 'fede_speranza_carita.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', "Croce, ancora e cuore.", "Cross, anchor and heart.", 45.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TAGBE-10197', 'intreccio.jpg', 'Stop Intreccio', 'Intertwined Spacer', "Simbolo di legami uniti.", "Symbol of bonds.", 35.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TGLBE-10431', 'raccolto.jpg', 'Raccolto', 'Harvest', "Gratitudine per la natura.", "Gratitude for nature.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 1, 0),
            ('Trollbeads', 'TAGPE-00012', 'canto_balena.jpg', 'Canto della Balena', 'Whale\'s Song', "Voce misteriosa dell'oceano.", "Voice of the ocean.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0),
            ('Trollbeads', 'TGLBE-20120', 'cielo_notturno.jpg', 'Cielo Notturno', 'Night Sky', "Stelle nel firmamento.", "Stars in the sky.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0)
        ]
        c.executemany('''INSERT INTO charms 
                         (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 2. INTERFACCIA E NAVIGAZIONE ---
st.sidebar.title("Menu")
menu = st.sidebar.radio("Vai a:", ["Catalogo", "Aggiungi Nuovo", "Ricerca Web"])
lang = st.sidebar.selectbox("Lingua", ["Italiano", "English"])

# --- SEZIONE: AGGIUNGI MANUALE ---
if menu == "Aggiungi Nuovo":
    st.header("➕ Aggiungi un nuovo Bead")
    with st.form("manual_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_sku = st.text_input("SKU (es. TAGBE-XXXXX)")
            new_nome = st.text_input("Nome")
            new_designer = st.text_input("Designer")
        with col2:
            new_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=0.5)
            new_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
            new_retired = st.checkbox("È fuori produzione (Retired)?")
        
        new_desc = st.text_area("Descrizione")
        submitted = st.form_submit_button("Salva nel Portagioie")
        
        if submitted:
            c = conn.cursor()
            c.execute('''INSERT INTO charms (brand, sku, nome_it, nome_en, desc_it, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,0)''', 
                      ('Trollbeads', new_sku, new_nome, new_nome, new_desc, new_prezzo, new_designer, new_mat, 1 if new_retired else 0))
            conn.commit()
            st.success(f"Bead {new_nome} salvato correttamente!")

# --- SEZIONE: RICERCA WEB ---
elif menu == "Ricerca Web":
    st.header("🌐 Cerca nel Museo/Web")
    query = st.text_input("Inserisci SKU o Nome per trovare la foto ufficiale")
    if query:
        search_url = f"https://www.google.it/search?q=trollbeads+official+photo+{query}&tbm=isch"
        st.markdown(f"### [👉 Clicca qui per vedere le foto di {query}]({search_url})")
        st.info("Consiglio: Una volta trovata la foto, salvala con il nome dello SKU (es: TAGBE-12345.jpg) e caricala su GitHub.")

# --- SEZIONE: CATALOGO (IL TUO DATABASE REALE) ---
else:
    st.header("💎 Il Mio Catalogo")
    search = st.text_input("🔍 Cerca nel tuo archivio (Nome o SKU)")
    
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if search:
        df = df[df['nome_it'].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    for i, row in df.iterrows():
        c_img, c_info = st.columns([1, 4])
        with c_img:
            # Miniatura nella lista
            if row['img_filename'] and os.path.exists(row['img_filename']):
                st.image(row['img_filename'], width=85)
            else:
                st.write("🖼️")
        
        with c_info:
            with st.expander(f"**{row['nome_it']}** ({row['sku']})"):
                # Foto grande nell'espansione
                if row['img_filename'] and os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                
                # Dati dal DB
                st.write(f"**Designer:** {row['designer']}")
                st.write(f"**Materiale:** {row['materiale']}")
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Stato:** {'🔴 Fuori Produzione' if row['fuori_produzione'] else '🟢 In Produzione'}")
                st.write(f"**Descrizione:** {row['desc_it']}")
                
                if st.button("Lo possiedo", key=f"btn_{row['id']}"):
                    st.balloons()
                    st.success("Aggiunto alla collezione fisica!")
