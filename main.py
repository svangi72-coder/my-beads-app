import streamlit as st
import google.generativai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import json
import base64
from datetime import datetime
import pandas as pd

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Trollbeads Collector",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZZATO (Stile Premium Indaco) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 15px;
        height: 3em;
        background-color: #4f46e5;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #4338ca; border: none; color: white; }
    .bead-card {
        background-color: white;
        padding: 20px;
        border-radius: 25px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 20px;
    }
    .ai-badge {
        background: linear-gradient(45deg, #4f46e5, #9333ea);
        color: white;
        padding: 5px 12px;
        border-radius: 10px;
        font-size: 0.7em;
        font-weight: 800;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE FIREBASE ---
# Nota: Su Streamlit Cloud inserisci il contenuto del JSON del service account nei Secrets
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            # Carica credenziali dai segreti di Streamlit
            fb_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback locale (se hai il file json nella stessa cartella)
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Errore connessione Firebase: {e}")

db = firestore.client()

# --- CONFIGURAZIONE GEMINI AI ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
else:
    st.warning("⚠️ Chiave API Gemini mancante nei Secrets.")

# --- FUNZIONI DI SUPPORTO ---

def call_gemini_ai(prompt, system_instruction=""):
    """Invia una richiesta a Gemini e restituisce il testo"""
    full_prompt = f"{system_instruction}\n\nUser: {prompt}"
    response = model.generate_content(full_prompt)
    return response.text

def get_beads():
    """Recupera la collezione da Firestore"""
    # Usiamo un ID utente fisso per ora o lo stato della sessione
    user_id = "default_user" 
    docs = db.collection("artifacts").document("trollbeads-v7").collection("users").document(user_id).collection("beads").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in docs]

def save_bead(data):
    """Salva o aggiorna un bead"""
    user_id = "default_user"
    bead_ref = db.collection("artifacts").document("trollbeads-v7").collection("users").document(user_id).collection("beads")
    if "id" in data and data["id"]:
        bead_id = data.pop("id")
        bead_ref.document(bead_id).update(data)
    else:
        data["timestamp"] = datetime.now()
        bead_ref.add(data)

def delete_bead(bead_id):
    """Elimina un bead"""
    user_id = "default_user"
    db.collection("artifacts").document("trollbeads-v7").collection("users").document(user_id).collection("beads").document(bead_id).delete()

# --- INTERFACCIA UTENTE ---

# Navigazione
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'edit_bead' not in st.session_state:
    st.session_state.edit_bead = None

# Sidebar (Menu)
with st.sidebar:
    st.title("Menu")
    if st.button("🏠 La mia Collezione"):
        st.session_state.page = 'home'
    if st.button("🔍 Cerca nel Museo/Catalogo"):
        st.session_state.page = 'search'
    if st.button("✨ Ispirazione AI"):
        st.session_state.page = 'ai'

# --- PAGINA: HOME (COLLEZIONE) ---
if st.session_state.page == 'home':
    st.title("📿 La mia Collezione")
    
    # Barra di ricerca locale
    search_local = st.text_input("Filtra i tuoi pezzi...", placeholder="Cerca per nome o SKU")
    
    beads = get_beads()
    if search_local:
        beads = [b for b in beads if search_local.lower() in b.get('name', '').lower() or search_local.lower() in b.get('sku', '').lower()]

    if not beads:
        st.info("La tua collezione è vuota. Inizia cercando un pezzo nell'archivio!")
    else:
        cols = st.columns(2)
        for i, bead in enumerate(beads):
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"""
                        <div class="bead-card">
                            <h3 style="margin-bottom:5px; font-size:1.1em;">{bead.get('name', 'Senza Nome')}</h3>
                            <p style="color:#64748b; font-size:0.8em; font-weight:bold;">{bead.get('type', 'Beads')} • {bead.get('sku', 'No SKU')}</p>
                            <p style="font-size:1.2em; font-weight:900; color:#1e293b;">{bead.get('price', '0.00')}€</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if bead.get('imageUrl'):
                        st.image(bead['imageUrl'], use_container_width=True)
                    
                    btn_cols = st.columns(2)
                    if btn_cols[0].button("Modifica", key=f"edit_{bead['id']}"):
                        st.session_state.edit_bead = bead
                        st.session_state.page = 'edit'
                        st.rerun()
                    if btn_cols[1].button("Elimina", key=f"del_{bead['id']}"):
                        delete_bead(bead['id'])
                        st.success("Rimosso!")
                        st.rerun()

# --- PAGINA: RICERCA AI ---
elif st.session_state.page == 'search':
    st.title("🔍 Ricerca Enciclopedica")
    st.markdown("Interroga l'archivio storico e il catalogo ufficiale Trollbeads.")
    
    query = st.text_input("Cosa stai cercando?", placeholder="Esempio: Papavero, Rosa, Vetro di Murano...")
    
    if st.button("Esegui Scansione AI"):
        if query:
            with st.spinner("L'intelligenza artificiale sta consultando l'archivio..."):
                sys_inst = """Sei l'esperto mondiale Trollbeads. Cerca nel database ufficiale e nel museo. 
                Restituisci i dati ESCLUSIVAMENTE in formato JSON (array di oggetti).
                Schema: {"name": "...", "sku": "...", "material": "...", "price": "...", "type": "..."}"""
                
                try:
                    raw_res = call_gemini_ai(f"Trova ogni variante di: {query}", sys_inst)
                    # Pulizia del JSON
                    json_str = raw_res.replace("```json", "").replace("```", "").strip()
                    results = json.loads(json_str)
                    
                    st.subheader(f"Risultati per '{query}'")
                    for res in results:
                        with st.expander(f"{res['name']} ({res.get('sku', 'N/A')})"):
                            st.write(f"**Materiale:** {res.get('material')}")
                            st.write(f"**Tipo:** {res.get('type')}")
                            st.write(f"**Prezzo stimato:** {res.get('price')}€")
                            if st.button("Aggiungi alla Collezione", key=f"add_{res.get('sku')}_{res['name']}"):
                                save_bead(res)
                                st.success("Aggiunto!")
                except Exception as e:
                    st.error("Errore nell'elaborazione dei dati AI. Riprova con un termine più semplice.")
        else:
            st.warning("Inserisci un termine di ricerca.")

# --- PAGINA: AI INSIGHTS ---
elif st.session_state.page == 'ai':
    st.title("✨ Ispirazione & Stile")
    
    beads = get_beads()
    if not beads:
        st.warning("Aggiungi dei pezzi alla tua collezione per sbloccare le funzioni AI.")
    else:
        tab1, tab2 = st.tabs(["📖 Storyteller", "🎨 Consulente di Stile"])
        
        with tab1:
            if st.button("Genera la Storia della mia Collezione"):
                names = ", ".join([b['name'] for b in beads[:10]])
                with st.spinner("Scrivendo la tua storia..."):
                    story = call_gemini_ai(f"Crea una storia poetica di 4 righe basata su questi gioielli: {names}", "Sei un poeta del simbolismo.")
                    st.markdown(f"### ✨ La tua favola\n\n*{story}*")
        
        with tab2:
            target_bead = st.selectbox("Scegli un pezzo da abbinare:", [b['name'] for b in beads])
            if st.button("Ricevi Consigli di Stile"):
                with st.spinner("Analizzando abbinamenti ideali..."):
                    advice = call_gemini_ai(f"Suggerisci 3 abbinamenti per il pezzo: {target_bead}", "Sei un jewelry designer esperto.")
                    st.info(advice)

# --- PAGINA: EDIT / MANUAL ADD ---
elif st.session_state.page == 'edit':
    st.title("📝 Scheda Tecnica")
    bead = st.session_state.edit_bead if st.session_state.edit_bead else {}
    
    with st.form("edit_form"):
        name = st.text_input("Nome", value=bead.get('name', ''))
        sku = st.text_input("SKU", value=bead.get('sku', ''))
        price = st.text_input("Prezzo (€)", value=bead.get('price', '0.00'))
        b_type = st.selectbox("Tipo", APP_TYPES, index=APP_TYPES.index(bead.get('type', 'Beads')) if bead.get('type') in APP_TYPES else 0)
        
        # Caricamento Immagine
        img_file = st.file_uploader("Carica Foto", type=['jpg', 'png', 'jpeg'])
        
        submitted = st.form_submit_state("Salva nel Cloud")
        if submitted:
            new_data = {
                "name": name,
                "sku": sku,
                "price": price,
                "type": b_type,
            }
            if bead.get('id'): new_data["id"] = bead['id']
            
            if img_file:
                # Conversione in Base64 per salvataggio semplice in Firestore
                bytes_data = img_file.getvalue()
                b64_str = base64.b64encode(bytes_data).decode()
                new_data["imageUrl"] = f"data:image/jpeg;base64,{b64_str}"
            elif bead.get('imageUrl'):
                new_data["imageUrl"] = bead['imageUrl']
                
            save_bead(new_data)
            st.session_state.page = 'home'
            st.session_state.edit_bead = None
            st.rerun()

    if st.button("Annulla"):
        st.session_state.page = 'home'
        st.session_state.edit_bead = None
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>Trollbeads Collector v7 - Python Edition</p>", unsafe_allow_html=True)
