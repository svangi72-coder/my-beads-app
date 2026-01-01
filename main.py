import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE ESTETICA E PAGINA ---
st.set_page_config(page_title="Trollbeads Global Collector", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FDFDFD; }
    .bead-card {
        padding: 20px; border-radius: 15px; border: 1px solid #E0E0E0;
        background-color: #FFFFFF; box-shadow: 2px 2px 12px rgba(0,0,0,0.03);
        margin-bottom: 25px;
    }
    .bead-title { color: #1A2530; font-family: 'Georgia', serif; font-weight: bold; font-size: 1.5rem; }
    .web-section { background-color: #F1F3F6; padding: 20px; border-radius: 15px; margin-top: 20px; }
    .link-button {
        text-decoration: none; padding: 8px 15px; border-radius: 8px;
        background-color: #FFFFFF; color: #1A2530; font-weight: bold;
        display: inline-block; margin: 5px; border: 1px solid #D1D3D8; font-size: 0.9rem;
    }
    .link-button:hover { background-color: #71797E; color: white; }
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

# --- 3. FUNZIONE VISUALIZZAZIONE ---
def mostra_beads(dataframe, is_collezione_personale=False):
    for i, row in dataframe.iterrows():
        with st.container():
            st.markdown(f"<div class='bead-card'><div class='bead-title'>{row['nome_it']}</div></div>", unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 3])
            with col_img:
                if row['img_filename'] and os.path.exists(row['img_filename']):
                    st.image(row['img_filename'], use_container_width=True)
                else: st.markdown("<h2 style='text-align: center;'>💎</h2>", unsafe_allow_html=True)
            with col_info:
                st.write(f"**Brand:** {row['brand']} | **SKU:** {row['sku']} | **Materiale:** {row['materiale']}")
                with st.expander("Azioni"):
                    b_a, b_b = st.columns(2)
                    with b_a:
                        if not is_collezione_personale:
                            if st.button(f"❤️ Possiedo", key=f"p_{row['id']}"):
                                conn.execute("UPDATE charms SET posseduto = 1 WHERE id = ?", (row['id'],)); conn.commit(); st.rerun()
                        else:
                            if st.button(f"❌ Rimuovi", key=f"r_{row['id']}"):
                                conn.execute("UPDATE charms SET posseduto = 0 WHERE id = ?", (row['id'],)); conn.commit(); st.rerun()
                    with b_b:
                        if st.button(f"🗑️ Elimina", key=f"d_{row['id']}"):
                            conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
        st.write("")

# --- 4. NAVIGAZIONE ---
menu = st.sidebar.radio("Naviga:", ["Catalogo Generale", "Mia Collezione", "Aggiungi Nuovo", "Ricerca Avanzata", "Statistiche"])

if menu == "Catalogo Generale":
    st.header("📖 Catalogo Completo")
    search = st.text_input("🔍 Cerca rapida")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if search: df = df[df['nome_it'].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]
    mostra_beads(df)

elif menu == "Mia Collezione":
    st.header("💍 La Mia Bacheca")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if df_p.empty: st.info("Collezione vuota.")
    else: mostra_beads(df_p, is_collezione_personale=True)

elif menu == "Aggiungi Nuovo":
    st.header("➕ Nuovo Inserimento")
    metodo = st.radio("Sorgente Foto:", ["Fotocamera iPad 📸", "Galleria 🖼️"])
    foto = st.camera_input("Scatta") if metodo == "Fotocamera iPad 📸" else st.file_uploader("Carica", type=['jpg','png','jpeg'])
    with st.form("form_add", clear_on_submit=True):
        f_sku = st.text_input("SKU / Codice")
        f_nome = st.text_input("Nome")
        f_prezzo = st.number_input("Prezzo (€)", min_value=0.0)
        f_mat = st.selectbox("Materiale", ["Argento 925", "Vetro", "Pietra", "Oro"])
        if st.form_submit_button("✨ Salva"):
            fname = f"{f_sku}.jpg" if f_sku else "temp.jpg"
            if foto: img = Image.open(foto).convert('RGB').save(fname)
            conn.execute("INSERT INTO charms (brand, sku, img_filename, nome_it, prezzo, materiale, fuori_produzione, posseduto) VALUES ('Trollbeads',?,?,?,?,?,0,0)", (f_sku, fname, f_nome, f_prezzo, f_mat))
            conn.commit(); st.success("Aggiunto!")

elif menu == "Ricerca Avanzata":
    st.header("🔍 Ricerca Globale (Database + Web)")
    
    with st.expander("🛠️ Filtri Interni Database", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            s_sku = st.text_input("Codice SKU")
            s_nome = st.text_input("Nome Bead (Italiano)")
        with c2:
            s_nome_en = st.text_input("Traduzione Nome (Inglese) - Opzionale")
            s_brand = st.selectbox("Brand", ["Trollbeads", "Tutti"])

    if s_sku or s_nome:
        st.markdown("<div class='web-section'>", unsafe_allow_html=True)
        st.subheader("🌐 Risultati Web e Siti Ufficiali")
        
        # Termini di ricerca ottimizzati
        q = f"{s_sku} {s_nome} {s_nome_en}".strip()
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.write("**🌍 Siti Ufficiali Trollbeads**")
            links = {
                "Danimarca (DK)": f"https://www.trollbeads.com/da-dk/search?q={s_sku}",
                "Stati Uniti (US)": f"https://www.trollbeads.com/en-us/search?q={s_sku}",
                "Germania (DE)": f"https://www.trollbeads.com/de-de/suche?q={s_sku}",
                "Regno Unito (UK)": f"https://www.trollbeads.com/en-gb/search?q={s_sku}"
            }
            for name, url in links.items():
                st.markdown(f"<a href='{url}' target='_blank' class='link-button'>{name}</a>", unsafe_allow_html=True)

        with col_b:
            st.write("**🏪 Venditori e Mercato**")
            market = {
                "eBay (Mondo)": f"https://www.ebay.it/sch/i.html?_nkw=trollbeads+{s_sku}",
                "Etsy (Artigianato)": f"https://www.etsy.com/search?q=trollbeads+{s_sku}",
                "Perlen Odense": f"https://www.perlenodense.com/searchcontrol/search?search={s_sku}"
            }
            for name, url in market.items():
                st.markdown(f"<a href='{url}' target='_blank' class='link-button'>{name}</a>", unsafe_allow_html=True)

        with col_c:
            st.write("**📸 Media e Recensioni**")
            media = {
                "Google Immagini": f"https://www.google.it/search?q=trollbeads+{q}&tbm=isch",
                "YouTube Video": f"https://www.youtube.com/results?search_query=trollbeads+{q}",
                "Pinterest": f"https://www.pinterest.it/search/pins/?q=trollbeads%20{s_sku}"
            }
            for name, url in media.items():
                st.markdown(f"<a href='{url}' target='_blank' class='link-button'>{name}</a>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("📂 Risultati nel tuo Database")
    df_f = pd.read_sql("SELECT * FROM charms WHERE sku LIKE ? OR nome_it LIKE ?", conn, params=(f"%{s_sku}%", f"%{s_nome}%"))
    if not df_f.empty: mostra_beads(df_f)
    else: st.warning("Nessun riscontro trovato nel tuo archivio locale.")

elif menu == "Statistiche":
    st.header("📊 Statistiche")
    df_p = pd.read_sql("SELECT * FROM charms WHERE posseduto = 1", conn)
    if not df_p.empty:
        st.metric("Pezzi in Collezione", len(df_p))
        st.metric("Valore Stimato", f"€{df_p['prezzo'].sum():.2f}")
        st.bar_chart(df_p['materiale'].value_counts())
