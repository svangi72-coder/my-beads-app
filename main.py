import React, { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  addDoc, 
  onSnapshot, 
  updateDoc, 
  deleteDoc, 
  doc, 
  query 
} from 'firebase/firestore';
import { 
  getAuth, 
  signInAnonymously, 
  signInWithCustomToken, 
  onAuthStateChanged 
} from 'firebase/auth';
import { 
  Search, 
  Plus, 
  Camera, 
  Trash2, 
  Edit2, 
  Save, 
  Loader2, 
  ChevronLeft,
  Info
} from 'lucide-react';

// --- CONFIGURAZIONE FIREBASE ---
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'trollbeads-catalog';
const apiKey = ""; 

const APP_TYPES = [
  'Beads', 'Stop', 'Bracciale', 'Collana', 'Orecchini', 'Anelli', 'Vetro', 'Pietra'
];

export default function App() {
  const [user, setUser] = useState(null);
  const [beads, setBeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [view, setView] = useState('list'); 
  const [selectedBead, setSelectedBead] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [aiQuery, setAiQuery] = useState("");
  const fileInputRef = useRef(null);

  // Inizializzazione Auth
  useEffect(() => {
    const initAuth = async () => {
      try {
        if (typeof __initial_auth_token !== 'undefined' && __initial_auth_token) {
          await signInWithCustomToken(auth, __initial_auth_token);
        } else {
          await signInAnonymously(auth);
        }
      } catch (error) {
        console.error("Errore Auth:", error);
      }
    };
    initAuth();
    const unsubscribe = onAuthStateChanged(auth, (u) => setUser(u));
    return () => unsubscribe();
  }, []);

  // Fetch dati da Firestore
  useEffect(() => {
    if (!user) return;
    setLoading(true);
    const beadsCollection = collection(db, 'artifacts', appId, 'users', user.uid, 'beads');
    const unsubscribe = onSnapshot(beadsCollection, 
      (snapshot) => {
        const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
        setBeads(data.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)));
        setLoading(false);
      },
      (error) => {
        console.error("Errore Firestore:", error);
        setLoading(false);
      }
    );
    return () => unsubscribe();
  }, [user]);

  // Ricerca AI
  const performAISearch = async (imageContent = null) => {
    setSearchLoading(true);
    try {
      let prompt = `Analizza questo Trollbead. Restituisci JSON con: name, sku, material, price, status, designer, type (uno tra: ${APP_TYPES.join(', ')}).`;
      
      let payload;
      if (imageContent) {
        payload = {
          contents: [{
            parts: [
              { text: prompt },
              { inlineData: { mimeType: "image/jpeg", data: imageContent.split(',')[1] } }
            ]
          }]
        };
      } else {
        payload = {
          contents: [{ parts: [{ text: `Dati per: ${aiQuery}. ${prompt}` }] }],
          tools: [{ "google_search": {} }]
        };
      }

      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      const textResponse = result.candidates?.[0]?.content?.parts?.[0]?.text;
      const jsonMatch = textResponse.match(/\{[\s\S]*\}/);
      
      if (jsonMatch) {
        const beadData = JSON.parse(jsonMatch[0]);
        setSelectedBead({
          ...beadData,
          imageUrl: imageContent || null
        });
        setView('edit');
      }
    } catch (error) {
      console.error("Errore AI:", error);
      setSelectedBead({ name: aiQuery || "Nuovo", type: 'Beads', imageUrl: imageContent });
      setView('edit');
    } finally {
      setSearchLoading(false);
      setAiQuery("");
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => performAISearch(reader.result);
      reader.readAsDataURL(file);
    }
  };

  // Salvataggio
  const saveBead = async (data) => {
    if (!user) return;
    try {
      const colRef = collection(db, 'artifacts', appId, 'users', user.uid, 'beads');
      const payload = { ...data, timestamp: Date.now() };
      if (data.id) {
        await updateDoc(doc(db, 'artifacts', appId, 'users', user.uid, 'beads', data.id), payload);
      } else {
        await addDoc(colRef, payload);
      }
      setView('list');
      setSelectedBead(null);
    } catch (error) {
      console.error("Errore salvataggio:", error);
    }
  };

  const deleteBead = async (id) => {
    if (!confirm("Eliminare l'oggetto dalla tua collezione?")) return;
    try {
      await deleteDoc(doc(db, 'artifacts', appId, 'users', user.uid, 'beads', id));
    } catch (error) {
      console.error("Errore eliminazione:", error);
    }
  };

  const filteredBeads = beads.filter(b => 
    b.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    b.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 pb-20 font-sans">
      {/* Input File posizionato qui per evitare errori di riferimento tra le viste */}
      <input 
        type="file" 
        ref={fileInputRef} 
        hidden 
        accept="image/*" 
        onChange={handleImageUpload} 
      />

      <header className="bg-white border-b px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-purple-700 rounded-lg flex items-center justify-center text-white font-bold">T</div>
          <h1 className="text-xl font-bold text-purple-700">Trollbeads Collector</h1>
        </div>
        <button onClick={() => { setSelectedBead({name: "", type: "Beads"}); setView('edit'); }} className="p-2 bg-purple-100 text-purple-700 rounded-full">
          <Plus size={24} />
        </button>
      </header>

      <main className="max-w-2xl mx-auto p-4">
        {view === 'list' ? (
          <div className="space-y-4">
            {/* Ricerca AI */}
            <div className="bg-purple-600 p-4 rounded-2xl text-white shadow-lg">
              <p className="text-sm mb-2 font-medium opacity-90">Ricerca intelligente (Nome, SKU o Foto)</p>
              <div className="flex gap-2">
                <input 
                  type="text"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && performAISearch()}
                  placeholder="Nome o codice..."
                  className="flex-1 bg-white/20 border-none rounded-xl px-4 py-2 text-white placeholder:text-white/50 focus:ring-2 focus:ring-white outline-none"
                />
                <button onClick={() => performAISearch()} disabled={searchLoading} className="p-2 bg-white text-purple-600 rounded-xl hover:bg-gray-100 transition-colors">
                  {searchLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                </button>
                <button onClick={() => fileInputRef.current?.click()} className="p-2 bg-white/20 text-white rounded-xl hover:bg-white/30 transition-colors">
                  <Camera size={20} />
                </button>
              </div>
            </div>

            {/* Filtro locale */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text"
                placeholder="Filtra la tua collezione..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full border border-gray-200 rounded-xl pl-10 pr-4 py-2 focus:ring-2 focus:ring-purple-500 outline-none shadow-sm"
              />
            </div>

            {/* Griglia Beads */}
            {loading ? (
              <div className="py-20 flex flex-col items-center justify-center text-gray-400 gap-2">
                <Loader2 className="animate-spin" size={32} />
                <p>Sincronizzazione cloud...</p>
              </div>
            ) : filteredBeads.length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {filteredBeads.map(bead => (
                  <div key={bead.id} className="bg-white rounded-xl border border-gray-100 p-2 shadow-sm relative group hover:shadow-md transition-shadow">
                    <div className="aspect-square bg-gray-50 rounded-lg overflow-hidden mb-2">
                      {bead.imageUrl ? (
                        <img src={bead.imageUrl} className="w-full h-full object-cover" alt={bead.name} />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-300"><Info size={32} /></div>
                      )}
                    </div>
                    <div className="px-1">
                      <h3 className="font-bold text-sm truncate text-gray-800">{bead.name}</h3>
                      <p className="text-[10px] text-gray-500 uppercase font-semibold">{bead.type}</p>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-xs font-bold text-purple-600">{bead.price ? `${bead.price}€` : '-'}</span>
                        <div className="flex gap-1">
                          <button onClick={() => { setSelectedBead(bead); setView('edit'); }} className="p-1.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-md transition-colors"><Edit2 size={14} /></button>
                          <button onClick={() => deleteBead(bead.id)} className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"><Trash2 size={14} /></button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20 bg-white rounded-3xl border-2 border-dashed border-gray-100">
                <p className="text-gray-400">Nessun bead trovato.<br/>Usa la ricerca AI per iniziare!</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-5 shadow-xl animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div className="flex items-center gap-2 mb-2">
              <button onClick={() => setView('list')} className="p-1 hover:bg-gray-100 rounded-full transition-colors"><ChevronLeft size={24} /></button>
              <h2 className="text-lg font-bold">Dettagli del Capolavoro</h2>
            </div>

            <div className="flex justify-center">
               <div 
                className="w-40 h-40 bg-gray-50 rounded-2xl overflow-hidden border border-gray-100 relative group cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
               >
                {selectedBead?.imageUrl ? (
                  <img src={selectedBead.imageUrl} className="w-full h-full object-cover" alt="Anteprima" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-gray-300 gap-2">
                    <Camera size={32} />
                    <span className="text-[10px] uppercase font-bold">Aggiungi Foto</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                  <Camera className="text-white" size={24} />
                </div>
               </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Nome</label>
                <input type="text" value={selectedBead?.name || ""} onChange={e => setSelectedBead({...selectedBead, name: e.target.value})} className="w-full border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Inserisci nome..." />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Tipo</label>
                  <select value={selectedBead?.type || "Beads"} onChange={e => setSelectedBead({...selectedBead, type: e.target.value})} className="w-full border-gray-200 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none bg-white">
                    {APP_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Prezzo (€)</label>
                  <input type="text" value={selectedBead?.price || ""} onChange={e => setSelectedBead({...selectedBead, price: e.target.value})} className="w-full border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="0.00" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Materiale</label>
                  <input type="text" value={selectedBead?.material || ""} onChange={e => setSelectedBead({...selectedBead, material: e.target.value})} className="w-full border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Argento, Vetro..." />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">SKU</label>
                  <input type="text" value={selectedBead?.sku || ""} onChange={e => setSelectedBead({...selectedBead, sku: e.target.value})} className="w-full border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Codice..." />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-1">Designer</label>
                <input type="text" value={selectedBead?.designer || ""} onChange={e => setSelectedBead({...selectedBead, designer: e.target.value})} className="w-full border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-purple-500 outline-none" placeholder="Nome designer..." />
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button 
                onClick={() => setView('list')}
                className="flex-1 py-3.5 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200 transition-colors"
              >
                Annulla
              </button>
              <button 
                onClick={() => saveBead(selectedBead)}
                className="flex-[2] py-3.5 bg-purple-600 text-white rounded-xl font-bold shadow-lg shadow-purple-100 flex items-center justify-center gap-2 hover:bg-purple-700 transition-all active:scale-[0.98]"
              >
                <Save size={20} /> Salva nel Cloud
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
