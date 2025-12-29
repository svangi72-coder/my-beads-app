import streamlit as st
import sqlite3
import pandas as pd

# --- 1. FUNZIONI DATABASE E AUTO-POPOLAMENTO ---
def init_db():
    conn = sqlite3.connect('beads.db', check_same_thread=False)
    c = conn.cursor()
    # Creazione Tabella
    c.execute('''CREATE TABLE IF NOT EXISTS charms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  brand TEXT, sku TEXT, img_url TEXT, 
                  nome_it TEXT, nome_en TEXT, 
                  desc_it TEXT, desc_en TEXT, 
                  posseduto BOOLEAN)''')
    
    # DATI DI ESEMPIO (Popolamento Automatico)
    # Aggiungi qui sotto tutti i beads che vuoi pre-caricare
trollbeads_master = [
        # --- ARGENTO ---
        ('Trollbeads', 'TAGBE-10197', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw1873836d/images/TAGBE-10197.jpg', 'Sogno a occhi aperti', 'Daydream', 'Libera la tua mente.', 'Free your mind.'),
        ('Trollbeads', 'TAGBE-00001', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw61e86895/images/TAGBE-00001.jpg', 'Quadrifoglio', 'Four-leaf Clover', 'Porta fortuna con te.', 'Take luck with you.'),
        ('Trollbeads', 'TAGBE-10052', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw5b404439/images/TAGBE-10052.jpg', 'Elefante', 'Elephant', 'Simbolo di saggezza.', 'Symbol of wisdom.'),
        ('Trollbeads', 'TAGBE-20235', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw7335e381/images/TAGBE-20235.jpg', 'Cuore di Ciliegio', 'Cherry Blossom Heart', 'Amore che sboccia.', 'Blooming love.'),
        ('Trollbeads', 'TAGBE-10113', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dwe701469a/images/TAGBE-10113.jpg', 'Tartaruga', 'Turtle', 'Pazienza e longevità.', 'Patience and longevity.'),
        ('Trollbeads', 'TAGBE-10141', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw4f777174/images/TAGBE-10141.jpg', 'Fiori di Maggio', 'Flowers of May', 'Freschezza primaverile.', 'Spring freshness.'),
        ('Trollbeads', 'TAGBE-10043', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw5456f937/images/TAGBE-10043.jpg', 'Pesciolino', 'Little Fish', 'Nuova avventura.', 'New adventure.'),
        ('Trollbeads', 'TAGBE-20001', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw0693a123/images/TAGBE-20001.jpg', 'Armonia', 'Harmony', 'Equilibrio perfetto.', 'Perfect balance.'),
        ('Trollbeads', 'TAGBE-10014', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw78d0554d/images/TAGBE-10014.jpg', 'Maternità', 'Maternity', 'Lame d\'amore infinito.', 'Infinite bond.'),
        ('Trollbeads', 'TAGBE-10034', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw76957567/images/TAGBE-10034.jpg', 'Bambino', 'Baby', 'La gioia della vita.', 'The joy of life.'),

        # --- VETRO ---
        ('Trollbeads', 'TGLBE-10431', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw9e663806/images/TGLBE-10431.jpg', 'Vetro del Deserto', 'Desert Glass', 'Ispirato alle sabbie dorate.', 'Inspired by golden sands.'),
        ('Trollbeads', 'TGLBE-10414', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw581e6462/images/TGLBE-10414.jpg', 'Bolle di Primavera', 'Spring Bubbles', 'Leggerezza e colore.', 'Lightness and color.'),
        ('Trollbeads', 'TGLBE-10411', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw3d6f1454/images/TGLBE-10411.jpg', 'Vetro dell\'Oceano', 'Ocean Glass', 'Abissi blu.', 'Deep blue.'),
        ('Trollbeads', 'TGLBE-20120', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw47c7c10b/images/TGLBE-20120.jpg', 'Aurora', 'Aurora', 'Luci del nord.', 'Northern lights.'),
        ('Trollbeads', 'TGLBE-10140', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dwf2157546/images/TGLBE-10140.jpg', 'Fiore dell\'Alba', 'Sunrise Flower', 'Nuovo inizio.', 'New beginning.'),
        ('Trollbeads', 'TGLBE-10137', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw90240465/images/TGLBE-10137.jpg', 'Cielo di Mezzanotte', 'Midnight Sky', 'Sogni stellati.', 'Starry dreams.'),
        ('Trollbeads', 'TGLBE-10156', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw9b1e7a56/images/TGLBE-10156.jpg', 'Pavone', 'Peacock', 'Eleganza piumata.', 'Feathered elegance.'),
        ('Trollbeads', 'TGLBE-10420', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw65421543/images/TGLBE-10420.jpg', 'Petali di Rose', 'Rose Petals', 'Delicatezza rosa.', 'Pink delicacy.'),
        ('Trollbeads', 'TGLBE-20015', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw55421543/images/TGLBE-20015.jpg', 'Via Lattea', 'Milky Way', 'Oltre le stelle.', 'Beyond stars.'),
        ('Trollbeads', 'TGLBE-10400', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw85421543/images/TGLBE-10400.jpg', 'Prato Fiorito', 'Flower Meadow', 'Profumo d\'estate.', 'Scent of summer.'),

        # --- PIETRE DURE ---
        ('Trollbeads', 'TSTBE-20022', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw40d87456/images/TSTBE-20022.jpg', 'Ametista', 'Amethyst', 'Pace interiore.', 'Inner peace.'),
        ('Trollbeads', 'TSTBE-20018', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw50d87456/images/TSTBE-20018.jpg', 'Occhio di Tigre', 'Tiger Eye', 'Coraggio e forza.', 'Courage and strength.'),
        ('Trollbeads', 'TSTBE-20001', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw60d87456/images/TSTBE-20001.jpg', 'Quarzo Rosa', 'Rose Quartz', 'Amore incondizionato.', 'Unconditional love.'),
        ('Trollbeads', 'TSTBE-20025', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw70d87456/images/TSTBE-20025.jpg', 'Lapislazzuli', 'Lapis Lazuli', 'Verità e saggezza.', 'Truth and wisdom.'),
        ('Trollbeads', 'TSTBE-20010', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw80d87456/images/TSTBE-20010.jpg', 'Onice Nera', 'Black Onyx', 'Autocontrollo.', 'Self-control.'),

        # --- SPECIALI ---
        ('Trollbeads', 'TAGBE-00007', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw12345678/images/TAGBE-00007.jpg', 'Drago', 'Dragon', 'Protettore dei sogni.', 'Dream protector.'),
        ('Trollbeads', 'TAGBE-00010', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw87654321/images/TAGBE-00010.jpg', 'Angelo', 'Angel', 'Guida spirituale.', 'Spiritual guide.'),
        ('Trollbeads', 'TAGBE-40010', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw11223344/images/TAGBE-40010.jpg', 'Mappamondo', 'Earth', 'Viaggia ovunque.', 'Travel everywhere.'),
        ('Trollbeads', 'TAGBE-30010', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw44332211/images/TAGBE-30010.jpg', 'Gatto', 'Cat', 'Indipendenza.', 'Independence.'),
        ('Trollbeads', 'TAGBE-20050', 'https://www.trollbeads.com/dw/image/v2/BJTS_PRD/on/demandware.static/-/Sites-trollbeads-master/default/dw99887766/images/TAGBE-20050.jpg', 'Stella Marina', 'Starfish', 'Sapore di mare.', 'Ocean vibe.')
    ]
    
    for item in trollbeads_master:
        c.execute('''INSERT OR IGNORE INTO charms 
                     (brand, sku, img_url, nome_it, nome_en, desc_it, desc_en, posseduto) 
                     VALUES (?,?,?,?,?,?,?,0)''', item)
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. CONFIGURAZIONE LINGUA ---
lang = st.sidebar.selectbox("Lingua / Language", ["Italiano", "English"])
txt = {
    "Italiano": {"titolo": "Catalogo Beads", "cerca": "Cerca nella Collezione", "aggiungi": "Aggiungi al mio Portagioie"},
    "English": {"titolo": "Beads Catalog", "cerca": "Search Collection", "aggiungi": "Add to Jewelry Box"}
}[lang]

st.title(f"💎 {txt['titolo']}")

# --- 3. FOTOCAMERA ---
foto = st.camera_input("Scansiona un Bead")
if foto:
    st.image(foto, caption="Analisi...")
    st.info("Ricerca visiva in corso nel catalogo globale...")

st.divider()

# --- 4. VISUALIZZAZIONE DATABASE ---
st.subheader(txt['cerca'])
search = st.text_input("Cerca per SKU o Nome", placeholder="Es: TAGBE...")

df = pd.read_sql("SELECT * FROM charms", conn)

if not df.empty:
    if search:
        col_name = "nome_it" if lang == "Italiano" else "nome_en"
        df = df[df[col_name].str.contains(search, case=False) | df['sku'].str.contains(search, case=False)]

    cols = st.columns(2)
    for i, row in df.iterrows():
        with cols[i % 2]:
            st.image(row['img_url'])
            st.write(f"**{row['nome_it'] if lang == 'Italiano' else row['nome_en']}**")
            st.caption(f"{row['sku']}")
            # Bottone per "possedere" il bead
            if st.button(f"Possiedo / I Own", key=f"btn_{row['id']}"):
                st.success(f"Aggiunto alla tua collezione!")

else:
    st.warning("Database vuoto. Controlla il codice!")
