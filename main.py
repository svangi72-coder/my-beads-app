import streamlit as st
import google.generativeai as genai
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
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            fb_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        else:
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

# --- DEFINIZIONE TIPI ---
APP_TYPES = ['Beads', 'Stop', 'Bracciale', 'Collana', 'Orecchini', 'Anelli', 'Vetro', 'Pietra', 'Chiusura', 'Accessorio', 'Pendenti']

# --- INTERFACCIA UTENTE ---

if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'edit_bead' not in st.session_state:
    st.session_state.edit_bead = None

with st.sidebar:
    st.title("Menu")
    if st.button("🏠 La mia Collezione"):
        st.session_state.page = 'home'
    if st.button("🔍 Cerca nel Museo/Catalogo"):
        st.session_state.page = 'search'
    if st.button("✨ Ispirazione AI"):
        st.session_state.page = 'ai'

if st.session_state.page == 'home':
    st.title("📿 La mia Collezione")
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

elif st.session_state.page == 'search':
    st.title("🔍 Ricerca Enciclopedica")
    query = st.text_input("Cosa stai cercando?", placeholder="Esempio: Papavero, Rosa...")
    if st.button("Esegui Scansione AI"):
        if query:
            with st.spinner("Consultando l'archivio..."):
                sys_inst = """Sei l'esperto mondiale Trollbeads. Restituisci i dati in JSON: [{"name": "...", "sku": "...", "material": "...", "price": "...", "type": "..."}]"""
                try:
                    raw_res = call_gemini_ai(f"Trova ogni variante di: {query}", sys_inst)
                    json_str = raw_res.replace("```json", "").replace("```", "").strip()
                    results = json.loads(json_str)
                    for res in results:
                        with st.expander(f"{res['name']} ({res.get('sku', 'N/A')})"):
                            st.write(f"**Materiale:** {res.get('material')}")
                            if st.button("Aggiungi alla Collezione", key=f"add_{res.get('sku')}_{res['name']}"):
                                save_bead(res)
                                st.success("Aggiunto!")
                except:
                    st.error("Errore dati AI. Riprova.")

elif st.session_state.page == 'ai':
    st.title("✨ Ispirazione & Stile")
    beads = get_beads()
    if not beads:
        st.warning("Aggiungi dei pezzi per sbloccare l'AI.")
    else:
        tab1, tab2 = st.tabs(["📖 Storyteller", "🎨 Consulente di Stile"])
        with tab1:
            if st.button("Genera Storia"):
                names = ", ".join([b['name'] for b in beads[:10]])
                story = call_gemini_ai(f"Crea una storia di 4 righe per: {names}", "Sei un poeta.")
                st.markdown(f"*{story}*")
        with tab2:
            target = st.selectbox("Scegli un pezzo:", [b['name'] for b in beads])
            if st.button("Consigli Stile"):
                advice = call_gemini_ai(f"Suggerisci 3 abbinamenti per: {target}", "Sei un designer.")
                st.info(advice)

elif st.session_state.page == 'edit':
    st.title("📝 Scheda Tecnica")
    bead = st.session_state.edit_bead if st.session_state.edit_bead else {}
    with st.form("edit_form"):
        name = st.text_input("Nome", value=bead.get('name', ''))
        sku = st.text_input("SKU", value=bead.get('sku', ''))
        price = st.text_input("Prezzo (€)", value=bead.get('price', '0.00'))
        b_type = st.selectbox("Tipo", APP_TYPES, index=0)
        img_file = st.file_uploader("Carica Foto", type=['jpg', 'png'])
        if st.form_submit_button("Salva"):
            new_data = {"name": name, "sku": sku, "price": price, "type": b_type}
            if bead.get('id'): new_data["id"] = bead['id']
            if img_file:
                b64 = base64.b64encode(img_file.getvalue()).decode()
                new_data["imageUrl"] = f"data:image/jpeg;base64,{b64}"
            save_bead(new_data)
            st.session_state.page = 'home'
            st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>Trollbeads Collector v7</p>", unsafe_allow_html=True)
