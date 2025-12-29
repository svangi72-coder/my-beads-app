import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. FUNZIONE DATABASE (BASE STABILE) ---
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

    c.execute("SELECT count(*) FROM charms")
    if c.fetchone()[0] == 0:
        beads_master = [
            ('Trollbeads', 'TAGBE-10052', 'fede_speranza_carita.jpg', 'Fede, Speranza e Carità', 'Faith, Hope and Charity', "Croce, ancora e cuore.", "Cross, anchor and heart.", 45.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TAGBE-10197', 'intreccio.jpg', 'Stop Intreccio', 'Intertwined Spacer', "Simbolo di legami uniti.", "Symbol of bonds.", 35.0, 'Søren Nielsen', 'Argento 925', 0, 0),
            ('Trollbeads', 'TGLBE-10431', 'raccolto.jpg', 'Raccolto', 'Harvest', "Gratitudine per la natura.", "Gratitude for nature.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 1, 0),
            ('Trollbeads', 'TAGPE-00012', 'IMG_3861.jpeg', 'Canto della Balena', 'Whale\'s Song', "Voce misteriosa dell'oceano.", "Voice of the ocean.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0),
            ('Trollbeads', 'TGLBE-20120', 'cielo_notturno.jpg', 'Cielo Notturno', 'Night Sky', "Stelle nel firmamento.", "Stars in the sky.", 55.0, 'Lise Aagaard', 'Vetro / Argento', 0, 0)
        ]
        c.executemany('''INSERT INTO charms 
                         (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 2. MENU LATERALE ---
st.sidebar.title("💎 Beads Manager")
menu = st.sidebar.radio("Naviga:", ["Catalogo", "Aggiungi Nuovo", "Statistiche", "Ricerca Web"])

# --- SEZIONE: AGGIUNGI NUOVO ---
if menu == "Aggiungi Nuovo":
    st.header("➕ Inserimento Manuale")
    with st.form("new_bead_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU (es. TAGBE-10052)")
            nome = st.text_input("Nome Bead")
            designer = st.text_input("Designer")
        with col2:
            prezzo = st.number_input("Prezzo (€)", min_value=0.0)
            mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
            retired = st.checkbox("Fuori Produzione?")
        
        desc = st.text_area("Descrizione")
        file_foto = st.file_uploader("Scatta o allega foto", type=['jpg', 'png'])
        
        if st.form_submit_button("Salva nel Database"):
            filename = f"{sku}.jpg" if sku else "temp.jpg"
            if file_foto:
                img = Image.open(file_foto)
                img.save(filename)
            
            c = conn.cursor()
            c.execute('''INSERT INTO charms (brand, sku, img_filename, nome_it, desc_it, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,0)''', 
                      ('Trollbeads', sku, filename, nome, desc, prezzo, designer, mat, 1 if retired else 0))
            conn.commit()
            st.success(f"Bead {nome} aggiunto!")

# --- SEZIONE: STATISTICHE ---
elif menu == "Statistiche":
    st.header("📊 Statistiche Collezione")
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if not df.empty:
        total_beads = len(df)
        total_value = df['prezzo'].sum()
        retired_count = df[df['fuori_produzione'] == 1].shape[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Totale Beads", total_beads)
        c2.metric("Valore Stimato", f"€{total_value:.2f}")
        c3.metric("Fuori Produzione", retired_count)
        
        st.subheader("Distribuzione Materiali")
        st.bar_chart(df['materiale'].value_counts())
    else:
        st.info("Aggiungi dei beads per vedere le statistiche.")

# --- SEZIONE: RICERCA WEB ---
elif menu == "Ricerca Web":
    st.header("🌐 Cerca Foto Ufficiali")
    q = st.text_input("Inserisci lo SKU da cercare")
    if q:
        url = f"https://www.google.it/search?q=trollbeads+{q}&tbm=isch"
        st.markdown(f"### [🔍 Clicca qui per cercare {q} su Google Immagini]({url})")

# --- SEZIONE: CATALOGO ---
else:
    st.header("💎 Il Mio Catalogo")
    cerca = st.text_input("🔍 Cerca per Nome o SKU")
    
    df = pd.read_sql("SELECT * FROM charms", conn)
    if cerca:
        df = df[df['nome_it'].str.contains(cerca, case=False) | df['sku'].str.contains(cerca, case=False)]

    for i, row in df.iterrows():
        c1, c2 = st.columns([1, 4])
        with c1:
            if row['img_filename'] and os.path.exists(row['img_filename']):
                st.image(row['img_filename'], width=85)
            else:
                st.write("🖼️")
        
        with c2:
            with st.expander(f"**{row['nome_it']}** ({row['sku']})"):
                if row['img_filename'] and os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                
                st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']}")
                st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                st.write(f"**Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 Attivo'}")
                st.write(f"**Descrizione:** {row['desc_it']}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Lo possiedo", key=f"poss_{row['id']}"):
                        st.success("In collezione!")
                with col_btn2:
                    # Tasto per eliminare/vendere
                    if st.button("🗑️ Vendi / Elimina", key=f"del_{row['id']}"):
                        c = conn.cursor()
                        c.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.warning(f"Bead rimosso. Ricarica la pagina.")
                        st.rerun()
