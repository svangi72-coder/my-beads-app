import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE ESTETICA (CSS) ---
st.set_page_config(page_title="Trollbeads Collector", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    /* Sfondo e Font */
    .stApp { background-color: #FDFDFD; }
    
    /* Scheda del Bead */
    .bead-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
        box-shadow: 2px 2px 12px rgba(0,0,0,0.03);
        margin-bottom: 25px;
    }
    
    /* Titoli Serif Eleganti */
    .bead-title {
        color: #1A2530;
        font-family: 'Georgia', serif;
        font-weight: bold;
        font-size: 1.5rem;
        margin-bottom: 2px;
    }
    
    /* Badge Prezzo */
    .price-tag {
        color: #71797E;
        font-weight: bold;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTIONE DATABASE ---
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
        c.executemany('''INSERT INTO charms (brand, sku, img_filename, nome_it, nome_en, desc_it, desc_en, prezzo, designer, materiale, fuori_produzione, posseduto) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', beads_master)
    conn.commit()
    return conn

conn = init_db()

# --- 3. FUNZIONE VISUALIZZAZIONE (VERSIONE STABILE) ---
def mostra_beads(dataframe, is_collezione_personale=False):
    for i, row in dataframe.iterrows():
        # HTML per la scheda
        st.markdown(f"""
            <div class="bead-card">
                <div class="bead-title">{row['nome_it']}</div>
                <div class="price-tag">€{row['prezzo']:.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Colonne per Foto e Dettagli (dentro la scheda visiva)
        col_img, col_info = st.columns([1, 3])
        
        with col_img:
            if row['img_filename'] and os.path.exists(row['img_filename']):
                st.image(row['img_filename'], use_container_width=True)
            else:
                st.markdown("<h2 style='text-align: center;'>💎</h2>", unsafe_allow_html=True)
        
        with col_info:
            st.caption(f"SKU: {row['sku']} | Materiale: {row['materiale']}")
            with st.expander("Apri dettagli e azioni"):
                st.write(f"**Designer:** {row['designer']}")
                st.write(f"**Stato:** {'🔴 Retired (Museo)' if row['fuori_produzione'] else '🟢 In Produzione'}")
                st.write(f"*Descrizione:* {row['desc_it']}")
                
                st.divider()
                
                # Bottoni definiti in modo sicuro
                btn_left, btn_right = st.columns(2)
                
                with btn_left:
                    if not is_collezione_personale:
                        if st.button(f"❤️ Possiedo", key=f"poss_{row['id']}"):
                            c = conn.cursor()
                            c.execute("UPDATE charms SET posseduto = 1 WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                    else:
                        if st.button(f"❌ Rimuovi", key=f"rem_{row['id']}"):
                            c = conn.cursor()
                            c.execute("UPDATE charms SET posseduto = 0 WHERE id = ?", (row['id'],))
                            conn.commit()
                            st.rerun()
                
                with btn_right:
                    if st.button(f"🗑️ Elimina", key=f"del_{row['id']}"):
                        c = conn.cursor()
                        c.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
        st.write("") # Spaziatore

# --- 4. LOGICA DI NAVIGAZIONE ---
menu = st.sidebar.radio("Menu Principale", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Statistiche", "Ricerca Web"])

if menu == "Catalogo Generale":
    st.header("📖 Catalogo Trollbeads")
    search = st.text_input("🔍 Cerca per nome o codice...")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search:
        df = df[df['nome_it'].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]
    mostra_beads(df, is_collezione_personale=False)

elif menu == "Mia Collezione":
    st.header("💍 La mia bacheca personale")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if df_p.empty:
        st.info("La tua collezione è ancora vuota. Aggiungi i pezzi dal Catalogo!")
    else:
        mostra_beads(df_p, is_collezione_personale=True)

elif menu == "Statistiche":
    st.header("📊 Statistiche Collezione")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if not df_p.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Totale Pezzi", len(df_p))
        m2.metric("Valore Stimato", f"€{df_p['prezzo'].sum():.2f}")
        m3.metric("Pezzi Museo", len(df_p[df_p['fuori_produzione'] == 1]))
        st.subheader("Ripartizione Materiali")
        st.bar_chart(df_p['materiale'].value_counts())
    else:
        st.warning("Nessun dato. Popola la tua collezione per vedere i grafici.")

elif menu == "Aggiungi Nuovo":
    st.header("➕ Nuovo Bead")
    with st.form("add_form", clear_on_submit=True):
        f_sku = st.text_input("SKU")
        f_nome = st.text_input("Nome")
        f_prezzo = st.number_input("Prezzo (€)", min_value=0.0)
        f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        f_foto = st.file_uploader("Allega foto", type=['jpg', 'png'])
        if st.form_submit_button("Salva nel Catalogo"):
            fname = f"{f_sku}.jpg" if f_sku else "temp.jpg"
            if f_foto: Image.open(f_foto).save(fname)
            c = conn.cursor()
            c.execute("INSERT INTO charms (brand, sku, img_filename, nome_it, prezzo, materiale, posseduto) VALUES (?,?,?,?,?,?,0)", 
                      ('Trollbeads', f_sku, fname, f_nome, f_prezzo, f_mat))
            conn.commit()
            st.success("Salvato correttamente!")

elif menu == "Ricerca Web":
    st.header("🌐 Ricerca Esterna")
    q = st.text_input("Inserisci SKU")
    if q: st.markdown(f"[🔍 Cerca su Google Immagini](https://www.google.it/search?q=trollbeads+{q}&tbm=isch)")
