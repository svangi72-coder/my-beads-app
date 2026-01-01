import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE ESTETICA E PAGINA ---
st.set_page_config(page_title="Trollbeads Collector v2", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FDFDFD; }
    .bead-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E0E0E0;
        background-color: #FFFFFF;
        box-shadow: 2px 2px 12px rgba(0,0,0,0.03);
        margin-bottom: 25px;
    }
    .bead-title {
        color: #1A2530;
        font-family: 'Georgia', serif;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .stButton>button {
        border-radius: 20px;
        width: 100%;
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

# --- 3. FUNZIONE VISUALIZZAZIONE STABILE ---
def mostra_beads(dataframe, is_collezione_personale=False):
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'><div class='bead-title'>{row['nome_it']}</div></div>", unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 3])
            
            with col_img:
                if row['img_filename'] and os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                else:
                    st.markdown("<h2 style='text-align: center;'>💎</h2>", unsafe_allow_html=True)
            
            with col_info:
                st.write(f"**Brand:** {row['brand']} | **SKU:** {row['sku']} | **Materiale:** {row['materiale']}")
                with st.expander("Dettagli e Azioni"):
                    st.write(f"**Prezzo:** €{row['prezzo']:.2f}")
                    st.write(f"**Designer:** {row['designer']}")
                    st.write(f"**Stato:** {'🔴 Retired' if row['fuori_produzione'] else '🟢 Attivo'}")
                    st.write(f"**Note:** {row['desc_it']}")
                    
                    st.divider()
                    btn_a, btn_b = st.columns(2)
                    with btn_a:
                        if not is_collezione_personale:
                            if st.button(f"❤️ Possiedo", key=f"p_{row['id']}"):
                                c = conn.cursor()
                                c.execute("UPDATE charms SET posseduto = 1 WHERE id = ?", (row['id'],))
                                conn.commit()
                                st.rerun()
                        else:
                            if st.button(f"❌ Rimuovi", key=f"r_{row['id']}"):
                                c = conn.cursor()
                                c.execute("UPDATE charms SET posseduto = 0 WHERE id = ?", (row['id'],))
                                conn.commit()
                                st.rerun()
                    with btn_b:
                        if st.button(f"🗑️ Elimina", key=f"d_{row['id']}"):
                            c = conn.cursor()
                            c.execute("DELETE FROM charms WHERE id=?", (row['id'],))
                            conn.commit()
                            st.rerun()
        st.write("")

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Naviga:", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Ricerca Avanzata", "Statistiche"])

if menu == "Catalogo Generale":
    st.header("📖 Catalogo Completo")
    search = st.text_input("🔍 Ricerca rapida (Nome o SKU)")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search:
        df = df[df['nome_it'].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]
    mostra_beads(df, is_collezione_personale=False)

elif menu == "Mia Collezione":
    st.header("💍 La Mia Bacheca")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if df_p.empty:
        st.info("La tua collezione è vuota.")
    else:
        mostra_beads(df_p, is_collezione_personale=True)

elif menu == "Aggiungi Nuovo":
    st.header("➕ Nuovo Inserimento")
    metodo = st.radio("Sorgente Foto:", ["Fotocamera iPad 📸", "Galleria 🖼️"])
    foto = st.camera_input("Scatta") if metodo == "Fotocamera iPad 📸" else st.file_uploader("Carica", type=['jpg','png','jpeg'])
    
    with st.form("form_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Ohm Beads", "Altro"])
            f_sku = st.text_input("SKU / Codice")
            f_nome = st.text_input("Nome")
        with c2:
            f_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=1.0)
            f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro", "Rame", "Altro"])
            f_retired = st.checkbox("Fuori Produzione (Retired)")
        
        f_desc = st.text_area("Descrizione o Note")
        
        if st.form_submit_button("✨ Salva nel Catalogo"):
            fname = f"{f_sku}.jpg" if f_sku else "temp.jpg"
            if foto:
                img = Image.open(foto)
                if img.mode != 'RGB': img = img.convert('RGB')
                img.save(fname)
            c = conn.cursor()
            c.execute('''INSERT INTO charms (brand, sku, img_filename, nome_it, prezzo, materiale, fuori_produzione, desc_it, posseduto, designer) 
                         VALUES (?,?,?,?,?,?,?,?,0,?)''', 
                      (f_brand, f_sku, fname, f_nome, f_prezzo, f_mat, 1 if f_retired else 0, f_desc, "Inserito da utente"))
            conn.commit()
            st.success(f"Bead '{f_nome}' aggiunto con successo!")

elif menu == "Ricerca Avanzata":
    st.header("🔍 Filtri Ricerca nel Database")
    
    with st.container():
        st.write("Configura i filtri per restringere la visualizzazione del catalogo:")
        c1, c2, c3 = st.columns(3)
        with c1:
            s_brand = st.multiselect("Filtra per Brand", ["Trollbeads", "Pandora", "Ohm Beads", "Altro"])
            s_mat = st.multiselect("Filtra per Materiale", ["Argento 925", "Vetro", "Pietra", "Oro", "Rame"])
        with c2:
            s_sku = st.text_input("Cerca SKU")
            s_nome = st.text_input("Cerca Nome")
        with c3:
            s_stato = st.radio("Stato Produzione", ["Tutti", "Attivi", "Retired"])
            s_possesso = st.radio("Possesso", ["Tutti", "Solo i miei", "Solo quelli che mi mancano"])

    # Logica di filtraggio SQL dinamica
    query = "SELECT * FROM charms WHERE 1=1"
    params = []
    
    if s_brand:
        query += f" AND brand IN ({','.join(['?']*len(s_brand))})"
        params.extend(s_brand)
    if s_mat:
        query += f" AND materiale IN ({','.join(['?']*len(s_mat))})"
        params.extend(s_mat)
    if s_sku:
        query += " AND sku LIKE ?"
        params.append(f"%{s_sku}%")
    if s_nome:
        query += " AND nome_it LIKE ?"
        params.append(f"%{s_nome}%")
    if s_stato == "Attivi":
        query += " AND fuori_produzione = 0"
    elif s_stato == "Retired":
        query += " AND fuori_produzione = 1"
    
    if s_possesso == "Solo i miei":
        query += " AND posseduto = 1"
    elif s_possesso == "Solo quelli che mi mancano":
        query += " AND posseduto = 0"

    df_filtered = pd.read_sql(query, conn, params=params)

    st.divider()
    st.subheader(f"Risultati trovati: {len(df_filtered)}")
    
    if not df_filtered.empty:
        mostra_beads(df_filtered)
    else:
        st.warning("Nessun bead corrisponde ai filtri selezionati.")
    
    # Sezione Ricerca Esterna (Web) integrata in fondo
    st.divider()
    st.subheader("🌐 Ricerca Esterna (Web)")
    if s_sku:
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown(f"[🔍 Cerca Immagini di {s_sku} su Google](https://www.google.it/search?q=trollbeads+{s_sku}&tbm=isch)")
        with col_w2:
            st.markdown(f"[💰 Controlla prezzi di {s_sku} su eBay](https://www.ebay.it/sch/i.html?_nkw=trollbeads+{s_sku})")

elif menu == "Statistiche":
    st.header("📊 Analisi della Collezione")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if not df_p.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Totale Pezzi", len(df_p))
        m2.metric("Valore Stimato", f"€{df_p['prezzo'].sum():.2f}")
        m3.metric("Brand diversi", len(df_p['brand'].unique()))
        
        st.subheader("Distribuzione per Materiale")
        st.bar_chart(df_p['materiale'].value_counts())
    else:
        st.warning("Nessun dato disponibile.")
