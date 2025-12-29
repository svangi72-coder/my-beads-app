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
menu = st.sidebar.radio("Naviga:", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Statistiche", "Ricerca Web"])

# --- FUNZIONE VISUALIZZAZIONE (RIUTILIZZABILE) ---
def mostra_beads(dataframe, is_collezione_personale=False):
    for i, row in dataframe.iterrows():
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
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if not is_collezione_personale:
                        if st.button("❤️ Lo possiedo", key=f"add_{row['id']}"):
                            c = conn.cursor()
                            c.execute("UPDATE charms SET posseduto = 1 WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.success("Aggiunto alla tua collezione!")
                            st.rerun()
                    else:
                        if st.button("❌ Rimuovi dalla collezione", key=f"rem_{row['id']}"):
                            c = conn.cursor()
                            c.execute("UPDATE charms SET posseduto = 0 WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                with col_b2:
                    if st.button("🗑️ Elimina dal DB", key=f"del_{row['id']}"):
                        c = conn.cursor()
                        c.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

# --- SEZIONI ---
if menu == "Catalogo Generale":
    st.header("📖 Catalogo Generale")
    cerca = st.text_input("🔍 Cerca nel catalogo")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if cerca:
        df = df[df['nome_it'].str.contains(cerca, case=False) | df['sku'].str.contains(cerca, case=False)]
    mostra_beads(df, is_collezione_personale=False)

elif menu == "Mia Collezione":
    st.header("💍 La Mia Collezione Personale")
    df_pers = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if df_pers.empty:
        st.info("La tua collezione è vuota. Aggiungi beads dal Catalogo Generale!")
    else:
        mostra_beads(df_pers, is_collezione_personale=True)

elif menu == "Statistiche":
    st.header("📊 Statistiche Mia Collezione")
    df_pers = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if not df_pers.empty:
        st.metric("Pezzi Posseduti", len(df_pers))
        st.metric("Valore Totale Collezione", f"€{df_pers['prezzo'].sum():.2f}")
        st.bar_chart(df_pers['materiale'].value_counts())
    else:
        st.warning("Nessun dato disponibile. Popola la tua collezione!")

elif menu == "Aggiungi Nuovo":
    st.header("➕ Nuovo Bead nel Catalogo")
    # ... (Codice del form di aggiunta rimane lo stesso della versione precedente)
    with st.form("new_bead_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            sku = st.text_input("SKU")
            nome = st.text_input("Nome")
            designer = st.text_input("Designer")
        with col2:
            prezzo = st.number_input("Prezzo (€)", min_value=0.0)
            mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
            retired = st.checkbox("Fuori Produzione?")
        file_foto = st.file_uploader("Foto", type=['jpg', 'png'])
        if st.form_submit_button("Salva"):
            filename = f"{sku}.jpg" if sku else "temp.jpg"
            if file_foto: Image.open(file_foto).save(filename)
            c = conn.cursor()
            c.execute("INSERT INTO charms (brand, sku, img_filename, nome_it, prezzo, designer, materiale, fuori_produzione, posseduto) VALUES (?,?,?,?,?,?,?,?,0)", 
                      ('Trollbeads', sku, filename, nome, prezzo, designer, mat, 1 if retired else 0))
            conn.commit()
            st.success("Aggiunto al catalogo!")

elif menu == "Ricerca Web":
    st.header("🌐 Ricerca")
    q = st.text_input("SKU da cercare")
    if q: st.markdown(f"[🔍 Cerca {q} su Google](https://www.google.it/search?q=trollbeads+{q}&tbm=isch)")
