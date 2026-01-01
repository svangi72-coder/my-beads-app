import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image

# --- 1. CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'beads.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'immagini')

if not os.path.exists(IMG_FOLDER):
    os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="Trollbeads Collector PRO", page_icon="💎", layout="wide")

# --- 2. DIZIONARIO INTELLIGENTE (DATABASE DI CONOSCENZA) ---
# Usiamo chiavi semplici per facilitare il riconoscimento
conoscenza_beads = {
    "balena": {
        "sku": "TAGPE-00012",
        "nome": "Il Canto della Balena",
        "designer": "Lise Aagaard",
        "materiale": "Vetro",
        "prezzo": 55.0,
        "note": "Bead in vetro sfaccettato con sfumature blu e verdi."
    },
    "fede": {
        "sku": "TAGBE-10052",
        "nome": "Fede, Speranza e Carità",
        "designer": "Søren Nielsen",
        "materiale": "Argento 925",
        "prezzo": 45.0,
        "note": "Classico simbolo con croce, ancora e cuore."
    }
}

# --- 3. INIZIALIZZAZIONE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, brand TEXT, sku TEXT, img_filename TEXT, 
                  nome_it TEXT, nome_en TEXT, desc_it TEXT, prezzo REAL, designer TEXT, 
                  materiale TEXT, fuori_produzione INTEGER, posseduto INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- 4. FUNZIONE DI RICERCA NEL DIZIONARIO ---
def cerca_nel_dizionario(testo):
    testo = testo.lower()
    # Se il testo contiene una delle parole chiave, restituisci i dati
    for chiave, dati in conoscenza_beads.items():
        if chiave in testo:
            return dati
    # Se non trova nulla, restituisce campi vuoti
    return {"sku": "", "nome": "", "designer": "", "materiale": "Argento 925", "prezzo": 0.0, "note": ""}

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("Scegli:", ["📖 Catalogo", "💍 Mia Collezione", "🌐 Ricerca & Acquisizione"])

if menu == "🌐 Ricerca & Acquisizione":
    st.header("🌐 Centro Acquisizione Intelligente")
    
    # Campo di ricerca principale
    input_utente = st.text_input("🔍 Cerca il bead nel database mondiale (es: 'balena' o 'fede')", key="global_search")
    
    # Otteniamo i dati (precompilati o vuoti)
    dati_trovati = cerca_nel_dizionario(input_utente)
    
    if input_utente:
        # Link Google aggiornato dinamicamente
        q_google = f"trollbeads {dati_trovati['sku'] if dati_trovati['sku'] else input_utente}".replace(" ", "+")
        st.markdown(f"### [🔗 Cerca foto e info ufficiali per '{input_utente}' su Google]({f'https://www.google.it/search?q={q_google}&tbm=isch'})")
        
        with st.form("scheda_acquisizione"):
            st.subheader("📝 Verifica e Salva nel Catalogo Generale")
            col1, col2 = st.columns(2)
            
            with col1:
                # Se il dizionario ha trovato lo SKU, lo inserisce qui automaticamente
                w_sku = st.text_input("SKU ufficiale", value=dati_trovati['sku'])
                w_nome = st.text_input("Nome del Bead", value=dati_trovati['nome'] if dati_trovati['nome'] else input_utente.capitalize())
                w_designer = st.text_input("Designer", value=dati_trovati['designer'])
            
            with col2:
                w_prezzo = st.number_input("Prezzo di listino (€)", value=dati_trovati['prezzo'], step=1.0)
                lista_mat = ["Argento 925", "Vetro", "Pietra", "Oro", "Ambra"]
                idx_mat = lista_mat.index(dati_trovati['materiale']) if dati_trovati['materiale'] in lista_mat else 0
                w_mat = st.selectbox("Materiale", lista_mat, index=idx_mat)
                w_foto = st.file_uploader("Trascina qui la foto trovata", type=['jpg', 'jpeg', 'png'])
            
            w_note = st.text_area("Note e Storia", value=dati_trovati['note'])
            
            if st.form_submit_button("✨ SALVA NEL CATALOGO GENERALE"):
                if not w_sku or not w_nome:
                    st.error("Inserisci almeno SKU e Nome per salvare.")
                else:
                    fname = f"immagini/{w_sku}.jpg"
                    if w_foto:
                        Image.open(w_foto).convert('RGB').save(os.path.join(BASE_DIR, fname), "JPEG")
                    
                    conn.execute('''INSERT INTO charms (brand, sku, nome_it, materiale, designer, prezzo, desc_it, img_filename, posseduto, fuori_produzione) 
                                    VALUES ('Trollbeads',?,?,?,?,?,?,?,0,0)''', 
                                 (w_sku, w_nome, w_mat, w_designer, w_prezzo, w_note, fname))
                    conn.commit()
                    st.success(f"✅ {w_nome} salvato con successo!")

# (Sezioni Catalogo e Collezione per visualizzare i dati salvati)
elif menu == "📖 Catalogo":
    st.header("📖 Catalogo Generale")
    df = pd.read_sql("SELECT * FROM charms", conn)
    if df.empty:
        st.info("Il catalogo è vuoto. Usa la sezione 'Ricerca & Acquisizione' per aggiungere beads.")
    else:
        for i, row in df.iterrows():
            with st.expander(f"{row['nome_it']} ({row['sku']})"):
                st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']} | **Prezzo:** €{row['prezzo']}")
                if row['img_filename'] and os.path.exists(os.path.join(BASE_DIR, row['img_filename'])):
                    st.image(os.path.join(BASE_DIR, row['img_filename']), width=200)
