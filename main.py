import streamlit as st
import sqlite3
import pandas as pd

# --- 1. FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_url TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE PAGINA E LINGUA ---
st.set_page_config(page_title="Beads Collector Hub", layout="wide")

# Traduzioni interfaccia
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
txt = {
    "Italiano": {
        "titolo": "Catalogo Beads",
        "camera_btn": "Scatta una foto per cercare",
        "aggiungi": "Aggiungi Nuovo / Ricerca Internet",
        "cerca": "La mia collezione",
        "btn_salva": "Salva nel Database",
        "nome": "Nome", "desc": "Descrizione", "stato": "Posseduto"
    },
    "English": {
        "titolo": "Beads Catalog",
        "camera_btn": "Take a photo to search",
        "aggiungi": "Add New / Web Search",
        "cerca": "My Collection",
        "btn_salva": "Save to Database",
        "nome": "Name", "desc": "Description", "stato": "Owned"
    }
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- 3. RICERCA VISIVA (FOTOCAMERA) ---
st.subheader(f"📸 {txt['camera_btn']}")
foto_scattata = st.camera_input("Scanner")

if foto_scattata:
    st.image(foto_scattata, caption="Analisi immagine...")
    st.info("AI: Ricerca visiva in corso... Questa funzione collegherà il database globale via internet.")

st.divider()

# --- 4. VISUALIZZAZIONE COLLEZIONE (RICERCA DB) ---
st.subheader(f"🔍 {txt['cerca']}")
search = st.text_input("Cerca per SKU o Nome", placeholder="Es: TAGBE-101...")

# Caricamento dati dal database
query = "SELECT * FROM charms"
df = pd.read_sql(query, conn)

if not df.empty:
    # Filtro ricerca
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    # Griglia di visualizzazione
    cols = st.columns(2) # 2 colonne sono meglio per lo schermo dell'iPhone
    for i, row in df.iterrows():
        with cols[i % 2]:
            st.image(row['img_url'] if row['img_url'] else "https://via.placeholder.com/150")
            st.write(f"**{row['nome_it'] if lang == 'Italiano' else row['nome_en']}**")
            st.caption(f"{row['brand']} | {row['sku']}")
            st.checkbox(txt['stato'], value=True, key=f"check_{row['id']}")
else:
    st.write("Nessun bead presente. Usa il modulo sotto per aggiungere il primo!")

st.divider()

# --- 5. AGGIUNTA MANUALE / RISULTATI INTERNET ---
with st.expander(f"➕ {txt['aggiungi']}"):
    col1, col2 = st.columns(2)
    with col1:
        new_brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Ohm", "Altro"])
        new_sku = st.text_input("Codice SKU")
        new_img = st.text_input("URL Immagine (Copia/Incolla da Internet)")
    with col2:
        new_n_it = st.text_input("Nome (IT)")
        new_n_en = st.text_input("Name (EN)")
        new_d_it = st.text_area("Descrizione (IT)")
        new_d_en = st.text_area("Description (EN)")
    
    if st.button(txt['btn_salva']):
        c = conn.cursor()
        c.execute("""INSERT INTO charms (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (new_brand, new_sku, new_img, new_n_it, new_n_en, new_d_it, new_d_en, True))
        conn.commit()
        st.success("Salvato!")
        st.rerun() # Ricarica l'app per mostrare il nuovo bead
