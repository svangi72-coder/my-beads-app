import streamlit as st
import sqlite3
import pandas as pd

# --- FUNZIONI DATABASE ---
def init_db():
    conn = sqlite3.connect('beads.db')
    c = conn.cursor()
    # Creiamo la tabella se non esiste
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTO_INCREMENT, 
                  brand TEXT, sku TEXT, img_url TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    conn.commit()
    return conn

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Beads Collector Hub", layout="wide")

# Selezione Lingua nella barra laterale
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])

# Dizionario traduzioni Interfaccia
txt = {
    "Italiano": {
        "titolo": "Il Mio Catalogo Beads",
        "aggiungi": "Aggiungi nuovo Bead (Ricerca Internet)",
        "cerca": "Cerca nella mia collezione",
        "btn_salva": "Salva nel Database",
        "placeholder_url": "Incolla URL immagine o sito",
        "stato": "Stato: Posseduto"
    },
    "English": {
        "titolo": "My Beads Catalog",
        "aggiungi": "Add new Bead (Web Search)",
        "cerca": "Search in my collection",
        "btn_salva": "Save to Database",
        "placeholder_url": "Paste image or website URL",
        "stato": "Status: Owned"
    }
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- SEZIONE 1: AGGIUNTA E RICERCA INTERNET ---
with st.expander(txt['aggiungi']):
    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Brand", ["Trollbeads", "Pandora", "Ohm", "Altro"])
        sku = st.text_input("Codice SKU")
        img_url = st.text_input(txt['placeholder_url'])
    with col2:
        nome_it = st.text_input("Nome (Italiano)")
        nome_en = st.text_input("Name (English)")
        desc_it = st.text_area("Descrizione (IT)")
        desc_en = st.text_area("Description (EN)")
    
    if st.button(txt['btn_salva']):
        conn = sqlite3.connect('beads.db')
        c = conn.cursor()
        c.execute("INSERT INTO charms (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, posseduto) VALUES (?,?,?,?,?,?,?,?)",
                  (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, True))
        conn.commit()
        st.success("Bead aggiunto con successo!")

# --- SEZIONE 2: CONSULTAZIONE CATALOGO ---
st.divider()
st.subheader(txt['cerca'])
search = st.text_input("🔍 SKU / Nome")

# Caricamento dati
conn = sqlite3.connect('beads.db')
query = "SELECT * FROM charms"
df = pd.read_sql(query, conn)

if not df.empty:
    # Filtro ricerca semplice
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    # Visualizzazione a Griglia
    cols = st.columns(4)
    for i, row in df.iterrows():
        with cols[i % 4]:
            st.image(row['img_url'] if row['img_url'] else "https://via.placeholder.com/150")
            st.markdown(f"**{row['nome_it'] if lang == 'Italiano' else row['nome_en']}**")
            st.caption(f"{row['brand']} - {row['sku']}")
            if st.checkbox(txt['stato'], value=bool(row['posseduto']), key=row['id']):
                pass 
else:
    st.info("Il database è vuoto. Aggiungi il tuo primo bead sopra!")
