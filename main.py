import streamlit as st
import sqlite3
import pandas as pd
import os
from PIL import Image
import requests
from io import BytesIO
import google.generativeai as genai # Per l'IA di Google

# --- 1. CONFIGURAZIONE AMBIENTE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'mio_database_personale.db')
IMG_FOLDER = os.path.join(BASE_DIR, 'mie_immagini')
if not os.path.exists(IMG_FOLDER): os.makedirs(IMG_FOLDER)

st.set_page_config(page_title="MyBeads AI Collector", page_icon="✨", layout="wide")

# --- 2. CONFIGURAZIONE GOOGLE AI (IMPORTANTE: LA TUA API KEY QUI!) ---
# Per ottenere la tua API Key: https://aistudio.google.com/app/apikey
# CONSIGLIO: NON SALVARE LA CHIAVE NEL CODICE PER LA PRODUZIONE. USA ST.SECRETS.
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    st.error("ERRORE: API Key di Google AI non trovata. Inseriscila in .streamlit/secrets.toml o come variabile d'ambiente.")
    model = None

# --- 3. DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT, nome TEXT, 
                  designer TEXT, materiale TEXT, prezzo REAL, peso REAL, descrizione TEXT, foto_path TEXT)''') # AGGIUNTO CAMPO PESO
    conn.commit()
    return conn

conn = init_db()

LISTA_MATERIALI = ["Vetro", "Argento 925", "Oro", "Pietra", "Ambra", "Rame", "Perla", "Altro"]

# --- 4. FUNZIONE DI ESTRAZIONE DATI CON IA ---
@st.cache_data(show_spinner="Analizzo il testo con l'IA di Google...")
def estrai_dati_con_ia(testo_da_analizzare):
    if not model:
        return {"error": "Modello IA non configurato."}
    
    prompt = f"""
    Estrai le seguenti informazioni dal testo fornito. Se un dato non è presente, lascia il campo vuoto.
    Formato JSON richiesto:
    {{
      "sku": "...",
      "nome": "...",
      "designer": "...",
      "materiale": "...",
      "prezzo": ...,
      "peso": ...,
      "descrizione": "..."
    }}

    Testo:
    {testo_da_analizzare}
    """
    try:
        response = model.generate_content(prompt)
        # Tenta di pulire la stringa JSON extra
        json_str = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(json_str)
        return data
    except Exception as e:
        st.error(f"Errore nell'estrazione dati con IA: {e}")
        return {"error": str(e)}

# --- 5. INTERFACCIA ---
menu = st.sidebar.radio("Menu", ["✨ Auto-Estrazione AI", "💍 Mia Collezione", "💾 Backup"])

if menu == "✨ Auto-Estrazione AI":
    st.title("✨ Acquisisci Dati con IA")
    
    st.info("Cerca il tuo bead online, copia il testo della descrizione (anche lungo) e incollalo qui. L'IA di Google estrarrà i dati per te!")
    
    testo_per_ia = st.text_area("Incolla qui il testo del bead (da siti, forum, ecc.)", height=200)
    
    dati_estratti = {}
    if st.button("🤖 Estrai Dati con IA"):
        if testo_per_ia:
            dati_estratti = estrai_dati_con_ia(testo_per_ia)
            if "error" in dati_estratti:
                st.error(f"Errore IA: {dati_estratti['error']}")
                dati_estratti = {} # Reset per non mostrare campi con errori
            else:
                st.success("Dati estratti con successo!")
        else:
            st.warning("Inserisci del testo per l'analisi.")

    st.divider()

    with st.form("form_estrazione_ai"):
        st.subheader("📝 Dati Bead Estratti e Modificabili")
        
        col_a, col_b = st.columns(2)
        with col_a:
            in_sku = st.text_input("SKU", value=dati_estratti.get("sku", ""))
            in_nome = st.text_input("Nome", value=dati_estratti.get("nome", ""))
            in_des = st.text_input("Designer", value=dati_estratti.get("designer", ""))
        with col_b:
            in_pre = st.number_input("Prezzo (€)", value=float(dati_estratti.get("prezzo", 0.0)), step=1.0)
            in_peso = st.number_input("Peso (grammi)", value=float(dati_estratti.get("peso", 0.0)), step=0.1) # CAMPO PESO
            
            # Seleziona il materiale con default
            try:
                mat_default_idx = LISTA_MATERIALI.index(dati_estratti.get("materiale", "Altro"))
            except ValueError:
                mat_default_idx = LISTA_MATERIALI.index("Altro")
            in_mat = st.selectbox("Materiale", LISTA_MATERIALI, index=mat_default_idx)
        
        in_desc = st.text_area("Descrizione (Significato)", value=dati_estratti.get("descrizione", ""), height=150)
        
        st.write("**🖼️ Cattura Foto**")
        st.info("Copia l'URL dell'immagine da Safari o caricala manualmente.")
        url_img_input = st.text_input("URL Immagine Web (opzionale)")
        
        uploaded_file = st.file_uploader("Carica foto manualmente (prioritario sull'URL)", type=['jpg', 'png', 'jpeg'])
        
        submit_form = st.form_submit_button("💾 SALVA NEL MIO DATABASE")
        
        if submit_form:
            if not GOOGLE_API_KEY:
                st.error("API Key di Google AI non configurata. Impossibile salvare.")
            elif in_sku and in_nome:
                nome_f = f"{in_sku.replace('/', '_')}.jpg"
                path_rel = os.path.join('mie_immagini', nome_f)
                path_abs = os.path.join(BASE_DIR, path_rel)
                
                # Logica di salvataggio foto: priorità al file caricato, poi URL
                if uploaded_file:
                    Image.open(uploaded_file).convert('RGB').save(path_abs, "JPEG")
                elif url_img_input:
                    try:
                        resp = requests.get(url_img_input, timeout=10)
                        Image.open(BytesIO(resp.content)).convert('RGB').save(path_abs, "JPEG")
                        st.success("Foto scaricata dall'URL!")
                    except Exception as e:
                        st.warning(f"Impossibile scaricare dall'URL: {e}. Salva il bead senza foto o caricala manualmente.")
                        path_rel = "" # Nessuna foto salvata
                else:
                    path_rel = "" # Nessuna foto
                
                conn.execute('''INSERT INTO charms (sku, nome, designer, materiale, prezzo, peso, descrizione, foto_path) 
                                VALUES (?,?,?,?,?,?,?,?)''', 
                             (in_sku, in_nome, in_des, in_mat, in_pre, in_peso, in_desc, path_rel))
                conn.commit()
                st.success(f"Bead '{in_nome}' salvato con successo!")
            else:
                st.error("SKU e Nome sono obbligatori per salvare.")

elif menu == "💍 Mia Collezione":
    st.title("💍 Il Mio Archivio Completo")
    df = pd.read_sql("SELECT * FROM charms", conn)
    
    if df.empty:
        st.info("Nessun bead salvato.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"{row['nome']} ({row['sku']})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if row['foto_path']:
                        full_path = os.path.join(BASE_DIR, row['foto_path'])
                        if os.path.exists(full_path):
                            st.image(full_path, use_container_width=True)
                        else:
                            st.warning("Foto non trovata.")
                with c2:
                    st.write(f"**Designer:** {row['designer']} | **Materiale:** {row['materiale']}")
                    st.write(f"**Prezzo:** €{row['prezzo']:.2f} | **Peso:** {row['peso']:.2f}g") # MOSTRA PESO
                    st.info(f"**Significato:** {row['descrizione']}")
                    if st.button("Elimina", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM charms WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

elif menu == "💾 Backup":
    st.header("💾 Backup Dati")
    with open(DB_PATH, "rb") as f:
        st.download_button("📤 Scarica Database (.db)", f, "backup_mybeads_ai.db")
