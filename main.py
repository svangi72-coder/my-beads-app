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

  // Inizializzazione Auth - RULE 3
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

  // Fetch dati da Firestore - RULE 1 & 2
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
  }, [user, appId]);

  // Ricerca AI
  const performAISearch = async (imageContent = null) => {
    if (!aiQuery && !imageContent) return;
    setSearchLoading(true);
    
    // Definiamo il modello come stringa per evitare ambiguità di parsing
    const modelId = "gemini-2.5-flash-preview-09-2025";
    const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelId}:generateContent?key=${apiKey}`;

    try {
      const prompt = `Analizza questo Trollbead. Restituisci esclusivamente un JSON con questi campi: name, sku, material, price, status, designer, type (uno tra: ${APP_TYPES.join(', ')}).`;
      
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
          contents: [{ parts: [{ text: `Cerca informazioni su: ${aiQuery}. ${prompt}` }] }],
          tools: [{ "google_search": {} }]
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      const textResponse = result.candidates?.[0]?.content?.parts?.[0]?.text;
      const jsonMatch = textResponse?.match(/\{[\s\S]*\}/);
      
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
      setSelectedBead({ 
        name: aiQuery || "Nuovo Oggetto", 
        type: 'Beads', 
        imageUrl: imageContent,
        material: "",
        price: "" 
      });
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
        const docRef = doc(db, 'artifacts', appId, 'users', user.uid, 'beads', data.id);
        await updateDoc(docRef, payload);
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
      {/* Input File sempre presente per evitare errori di riferimento */}
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
            {/* Sezione Ricerca AI */}
            <div className="bg-purple-600 p-5 rounded-3xl text-white shadow-lg">
              <p className="text-sm mb-3 font-medium opacity-90 text-center">Identifica con AI (Nome, SKU o Foto)</p>
              <div className="flex gap-2">
                <input 
                  type="text"
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && performAISearch()}
                  placeholder="Nome bead o codice..."
                  className="flex-1 bg-white/20 border-none rounded-xl px-4 py-3 text-white placeholder:text-white/60 focus:ring-2 focus:ring-white outline-none"
                />
                <button 
                  onClick={() => performAISearch()} 
                  disabled={searchLoading} 
                  className="p-3 bg-white text-purple-600 rounded-xl hover:bg-gray-100 transition-colors shadow-md"
                >
                  {searchLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                </button>
                <button 
                  onClick={() => fileInputRef.current?.click()} 
                  className="p-3 bg-white/20 text-white rounded-xl hover:bg-white/30 transition-colors"
                >
                  <Camera size={20} />
                </button>
              </div>
            </div>

            {/* Filtro collezione locale */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
              <input 
                type="text"
                placeholder="Cerca nella tua collezione..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full border border-gray-200 rounded-2xl pl-10 pr-4 py-3 focus:ring-2 focus:ring-purple-500 outline-none shadow-sm"
              />
            </div>

            {/* Lista dei Beads */}
            {loading ? (
              <div className="py-20 flex flex-col items-center justify-center text-gray-400 gap-3">
                <Loader2 className="animate-spin" size={32} />
                <p className="text-sm font-medium">Sincronizzazione Cloud...</p>
              </div>
            ) : filteredBeads.length > 0 ? (
              <div className="grid grid-cols-2 gap-4">
                {filteredBeads.map(bead => (
                  <div key={bead.id} className="bg-white rounded-2xl border border-gray-100 p-3 shadow-sm hover:shadow-md transition-shadow group">
                    <div className="aspect-square bg-gray-50 rounded-xl overflow-hidden mb-3 border border-gray-50">
                      {bead.imageUrl ? (
                        <img src={bead.imageUrl} className="w-full h-full object-cover" alt={bead.name} />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-gray-300 bg-gray-50">
                          <Info size={32} />
                        </div>
                      )}
                    </div>
                    <div className="space-y-1">
                      <h3 className="font-bold text-sm truncate text-gray-800">{bead.name}</h3>
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-purple-600 font-bold uppercase tracking-wider bg-purple-50 px-2 py-0.5 rounded-md">
                          {bead.type}
                        </span>
                        <span className="text-xs font-bold text-gray-900">{bead.price ? `${bead.price}€` : '-'}</span>
                      </div>
                      <div className="flex gap-2 pt-2 border-t border-gray-50 mt-2">
                        <button 
                          onClick={() => { setSelectedBead(bead); setView('edit'); }} 
                          className="flex-1 p-1.5 bg-gray-50 text-gray-500 rounded-lg hover:text-blue-600 hover:bg-blue-50 transition-colors"
                        >
                          <Edit2 size={14} className="mx-auto" />
                        </button>
                        <button 
                          onClick={() => deleteBead(bead.id)} 
                          className="flex-1 p-1.5 bg-gray-50 text-gray-500 rounded-lg hover:text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <Trash2 size={14} className="mx-auto" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-24 bg-white rounded-[2rem] border-2 border-dashed border-gray-100">
                <p className="text-gray-400 font-medium">Ancora nessun bead?<br/>Usa la fotocamera per iniziare!</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-gray-100 p-6 space-y-6 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300">
            <div className="flex items-center justify-between">
              <button onClick={() => setView('list')} className="p-2 hover:bg-gray-100 rounded-full transition-colors"><ChevronLeft size={24} /></button>
              <h2 className="text-lg font-black text-gray-800">Scheda Tecnica</h2>
              <div className="w-10"></div>
            </div>

            <div className="flex justify-center">
               <div 
                className="w-48 h-48 bg-gray-50 rounded-[2rem] overflow-hidden border border-gray-100 relative group cursor-pointer shadow-inner"
                onClick={() => fileInputRef.current?.click()}
               >
                {selectedBead?.imageUrl ? (
                  <img src={selectedBead.imageUrl} className="w-full h-full object-cover" alt="Anteprima" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-gray-300 gap-2">
                    <Camera size={40} />
                    <span className="text-[10px] uppercase font-black">Aggiungi Foto</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                  <Camera className="text-white" size={32} />
                </div>
               </div>
            </div>

            <div className="grid grid-cols-1 gap-5">
              <div className="space-y-1">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">Nome Modello</label>
                <input 
                  type="text" 
                  value={selectedBead?.name || ""} 
                  onChange={e => setSelectedBead({...selectedBead, name: e.target.value})} 
                  className="w-full bg-gray-50 border-none rounded-2xl px-5 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold" 
                  placeholder="Nome del bead..." 
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">Categoria</label>
                  <select 
                    value={selectedBead?.type || "Beads"} 
                    onChange={e => setSelectedBead({...selectedBead, type: e.target.value})} 
                    className="w-full bg-gray-50 border-none rounded-2xl px-4 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold"
                  >
                    {APP_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">Prezzo (€)</label>
                  <input 
                    type="text" 
                    value={selectedBead?.price || ""} 
                    onChange={e => setSelectedBead({...selectedBead, price: e.target.value})} 
                    className="w-full bg-gray-50 border-none rounded-2xl px-5 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold" 
                    placeholder="0.00" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">Materiale</label>
                  <input 
                    type="text" 
                    value={selectedBead?.material || ""} 
                    onChange={e => setSelectedBead({...selectedBead, material: e.target.value})} 
                    className="w-full bg-gray-50 border-none rounded-2xl px-5 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold" 
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">SKU / Codice</label>
                  <input 
                    type="text" 
                    value={selectedBead?.sku || ""} 
                    onChange={e => setSelectedBead({...selectedBead, sku: e.target.value})} 
                    className="w-full bg-gray-50 border-none rounded-2xl px-5 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold" 
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest ml-2">Designer</label>
                <input 
                  type="text" 
                  value={selectedBead?.designer || ""} 
                  onChange={e => setSelectedBead({...selectedBead, designer: e.target.value})} 
                  className="w-full bg-gray-50 border-none rounded-2xl px-5 py-3.5 focus:ring-2 focus:ring-purple-500 outline-none font-bold" 
                />
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <button 
                onClick={() => setView('list')}
                className="flex-1 py-4 bg-gray-100 text-gray-600 rounded-2xl font-bold hover:bg-gray-200 transition-colors"
              >
                Annulla
              </button>
              <button 
                onClick={() => saveBead(selectedBead)}
                className="flex-[2] py-4 bg-purple-600 text-white rounded-2xl font-bold shadow-xl shadow-purple-100 flex items-center justify-center gap-2 hover:bg-purple-700 transition-all active:scale-[0.98]"
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
