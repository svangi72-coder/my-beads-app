import React, { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { 
  getFirestore, 
  collection, 
  addDoc, 
  onSnapshot, 
  updateDoc, 
  deleteDoc, 
  doc 
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
  CheckCircle2,
  AlertCircle,
  X,
  Scale,
  Activity,
  Image as ImageIcon,
  ChevronRight,
  Sparkles,
  Link as LinkIcon,
  ExternalLink,
  Eye,
  Archive,
  Database,
  ImagePlus,
  Cloud,
  Layers,
  SearchCode,
  Smartphone,
  Wand2,
  BookOpen,
  Palette
} from 'lucide-react';

// --- CONFIGURAZIONE FIREBASE ---
const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'trollbeads-collector-v7';
const apiKey = ""; // Gestito dall'ambiente

const APP_TYPES = ['Beads', 'Stop', 'Bracciale', 'Collana', 'Orecchini', 'Anelli', 'Vetro', 'Pietra', 'Chiusura', 'Accessorio', 'Pendenti'];
const APP_STATUSES = ['In Collezione', 'Disponibile', 'Ritirato', 'Edizione Limitata', 'Desiderato', 'Museo'];

const formatPrice = (val) => {
  if (!val) return "0.00";
  const num = parseFloat(String(val).replace(',', '.').replace(/[^0-9.]/g, ''));
  return isNaN(num) ? "0.00" : num.toFixed(2);
};

export default function App() {
  const [user, setUser] = useState(null);
  const [beads, setBeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [aiActionLoading, setAiActionLoading] = useState(false);
  const [view, setView] = useState('list'); 
  const [selectedBead, setSelectedBead] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [aiQuery, setAiQuery] = useState("");
  const [aiResponse, setAiResponse] = useState(null);
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const fileInputRef = useRef(null);

  const showToast = (message, type = 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // 1. Auth Init
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
    const unsubscribe = onAuthStateChanged(auth, setUser);
    return () => unsubscribe();
  }, []);

  // 2. Sincronizzazione Dati
  useEffect(() => {
    if (!user) return;
    setLoading(true);
    const q = collection(db, 'artifacts', appId, 'users', user.uid, 'beads');
    return onSnapshot(q, (snapshot) => {
      const data = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setBeads(data.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0)));
      setLoading(false);
    }, (error) => {
      console.error("Database Error:", error);
      setLoading(false);
    });
  }, [user]);

  // --- LOGICA GEMINI API ---
  const callGemini = async (prompt, systemInstruction = "") => {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;
    
    const payload = {
      contents: [{ parts: [{ text: prompt }] }],
      systemInstruction: systemInstruction ? { parts: [{ text: systemInstruction }] } : undefined
    };

    let delay = 1000;
    for (let i = 0; i < 5; i++) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (response.ok) {
          const result = await response.json();
          return result.candidates?.[0]?.content?.parts?.[0]?.text;
        }
      } catch (e) {
        console.error("Retry...", i);
      }
      await new Promise(r => setTimeout(r, delay));
      delay *= 2;
    }
    throw new Error("Impossibile connettersi a Gemini");
  };

  // ✨ Funzione: Consulente di Stile
  const getStylingAdvice = async (bead) => {
    setAiActionLoading(true);
    setAiResponse(null);
    try {
      const systemPrompt = "Sei un esperto designer di gioielli Trollbeads. Conosci ogni bead, pietra e vetro.";
      const prompt = `Analizza questo pezzo Trollbeads: "${bead.name}" (${bead.material}). 
      Suggerisci 3 abbinamenti ideali (altri beads, colori o temi) per creare un bracciale armonioso. 
      Sii breve, elegante e professionale. Usa elenchi puntati.`;
      
      const advice = await callGemini(prompt, systemPrompt);
      setAiResponse({ title: "✨ Suggerimenti di Stile", text: advice });
    } catch (e) {
      showToast("Errore nell'analisi AI");
    } finally {
      setAiActionLoading(false);
    }
  };

  // ✨ Funzione: Storyteller della Collezione
  const generateCollectionStory = async () => {
    if (beads.length === 0) {
      showToast("Aggiungi prima dei pezzi alla collezione!");
      return;
    }
    setAiActionLoading(true);
    try {
      const names = beads.slice(0, 10).map(b => b.name).join(", ");
      const prompt = `Ho questi beads nella mia collezione: ${names}. 
      Inventa un breve tema narrativo o una storia poetica (massimo 4 righe) che li unisca in modo magico. 
      Dai anche un nome evocativo a questa composizione.`;
      
      const story = await callGemini(prompt, "Sei un poeta esperto di simbolismo dei gioielli.");
      setAiResponse({ title: "✨ La Storia della tua Collezione", text: story });
      setView('aiView');
    } catch (e) {
      showToast("Errore nella generazione della storia");
    } finally {
      setAiActionLoading(false);
    }
  };

  const performAISearch = async (imageContent = null) => {
    if (!aiQuery && !imageContent) return;
    setSearchLoading(true);
    try {
      const systemPrompt = `Sei l'autorità suprema di Trollbeads. DEVI essere estremamente preciso nei DATI tecnici ufficiali.
      Cerca nel database ufficiale TROLLBEADS.COM e nel MUSEO. Restituisci SOLO un ARRAY JSON [{}, {}].
      JSON SCHEMA: { "name": "Nome", "sku": "Codice", "material": "Materiale", "price": "0.00", "designer": "Nome", "weight": "0.00g", "status": "In Collezione", "type": "Beads" }`;

      const prompt = imageContent 
        ? "Identifica questo pezzo e restituisci i dati JSON." 
        : `Ricerca enciclopedica per: "${aiQuery}". Elenca ogni variante trovata con dati completi.`;

      // Nota: Per semplicità usiamo solo testo per la ricerca qui, ma Gemini supporta immagini se passato correttamente
      const rawText = await callGemini(prompt, systemPrompt);
      
      const jsonBlock = rawText.match(/\[\s*\{[\s\S]*\}\s*\]|\{\s*"name"[\s\S]*\}/);
      if (!jsonBlock) throw new Error();
      const data = JSON.parse(jsonBlock[0].replace(/\[\d+\]/g, ""));
      
      const items = Array.isArray(data) ? data : [data];
      setSearchResults(items.map(item => ({
        ...item,
        price: formatPrice(item.price),
        imageUrl: "", 
        timestamp: Date.now()
      })));
      setView('searchResults');
    } catch (e) {
      showToast("Ricerca fallita. Riprova con termini semplici.");
    } finally {
      setSearchLoading(false);
      setAiQuery("");
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (view === 'edit' && selectedBead) {
          setSelectedBead({ ...selectedBead, imageUrl: reader.result });
          showToast("Immagine caricata!", "success");
        } else {
          // Implementazione semplificata: carichiamo solo l'immagine nell'edit
          showToast("Usa la scheda tecnica per associare la foto.");
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const openManualImageSearch = () => {
    if (!selectedBead) return;
    const query = encodeURIComponent(`Trollbeads ${selectedBead.name} ${selectedBead.sku} official`);
    window.open(`https://www.google.com/search?q=${query}&tbm=isch`, '_blank');
  };

  const saveBead = async (data) => {
    if (!user || !data) return;
    try {
      const col = collection(db, 'artifacts', appId, 'users', user.uid, 'beads');
      const payload = { ...data, price: formatPrice(data.price), timestamp: Date.now() };
      if (data.id) await updateDoc(doc(db, 'artifacts', appId, 'users', user.uid, 'beads', data.id), payload);
      else await addDoc(col, payload);
      setView('list'); setSelectedBead(null); setSearchResults([]);
      showToast("Salvato nel Cloud!", "success");
    } catch (e) { showToast("Errore salvataggio Cloud."); }
  };

  const deleteBead = async (id) => {
    try {
      await deleteDoc(doc(db, 'artifacts', appId, 'users', user.uid, 'beads', id));
      setConfirmDelete(null); showToast("Rimosso.");
    } catch (e) { showToast("Errore eliminazione."); }
  };

  const filteredBeads = beads.filter(b => 
    b.name?.toLowerCase().includes(searchTerm.toLowerCase()) || 
    b.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-neutral-50 text-slate-900 pb-24 font-sans tracking-tight antialiased">
      <input type="file" ref={fileInputRef} hidden accept="image/*" onChange={handleImageUpload} />

      {/* Toast */}
      {toast && (
        <div className={`fixed top-6 left-1/2 -translate-x-1/2 z-[100] px-6 py-4 rounded-3xl shadow-2xl flex items-center gap-4 animate-in fade-in slide-in-from-top-8 ${toast.type === 'success' ? 'bg-indigo-600 text-white' : 'bg-rose-600 text-white'}`}>
          <span className="font-black text-xs uppercase tracking-widest">{toast.message}</span>
          <button onClick={() => setToast(null)}><X size={16} /></button>
        </div>
      )}

      {/* Header */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-slate-200 px-6 py-5 flex items-center justify-between sticky top-0 z-20 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center text-white font-black shadow-xl italic text-lg shadow-indigo-100">T</div>
          <h1 className="text-xl font-black uppercase tracking-tighter leading-none">Collector</h1>
        </div>
        <div className="flex gap-3">
          <button onClick={generateCollectionStory} disabled={aiActionLoading} className="p-3 bg-purple-50 text-purple-600 rounded-full hover:bg-purple-100 transition-all flex items-center justify-center">
            {aiActionLoading ? <Loader2 size={22} className="animate-spin" /> : <Sparkles size={22} />}
          </button>
          <button onClick={() => { setSelectedBead({name: "", type: "Beads", status: "In Collezione", price: "0.00", imageUrl: ""}); setView('edit'); }} className="p-3 bg-slate-100 rounded-full hover:bg-slate-200 transition-all"><Plus size={22} /></button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto p-5 md:p-8">
        {/* VISTA LISTA */}
        {view === 'list' && (
          <div className="space-y-8 animate-in fade-in">
            <div className="bg-indigo-600 p-8 rounded-[2.5rem] text-white shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10"><Cloud size={120} /></div>
              <p className="text-[10px] mb-4 font-black tracking-[0.3em] uppercase opacity-80 flex items-center gap-2"><Search size={12}/> Ricerca Enciclopedica</p>
              <div className="flex gap-3 relative z-10">
                <input 
                  type="text"
                  placeholder="Nome bead, anello, museo..."
                  value={aiQuery}
                  onChange={(e) => setAiQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && performAISearch()}
                  className="flex-1 bg-white/20 border-none rounded-2xl px-6 py-4 text-white placeholder:text-white/50 focus:ring-2 focus:ring-white outline-none font-black text-base"
                />
                <button onClick={() => performAISearch()} disabled={searchLoading} className="p-4 bg-white text-indigo-600 rounded-2xl shadow-xl flex items-center justify-center active:scale-95 disabled:opacity-50 transition-all">
                  {searchLoading ? <Loader2 className="animate-spin" size={24} /> : <Search size={24} />}
                </button>
              </div>
            </div>

            <div className="relative group">
              <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500" size={20} />
              <input 
                type="text"
                placeholder="Filtra la tua collezione..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full border-2 border-slate-100 rounded-[1.5rem] pl-16 pr-6 py-4 outline-none bg-white font-black text-base shadow-sm focus:border-indigo-200"
              />
            </div>

            <div className="grid grid-cols-2 gap-5 md:gap-8">
              {filteredBeads.map(bead => (
                <div key={bead.id} onClick={() => { setSelectedBead(bead); setView('edit'); }} className="bg-white rounded-[2rem] border border-slate-100 p-4 shadow-sm hover:shadow-md transition-all group cursor-pointer">
                  <div className="aspect-square bg-slate-50 rounded-[1.5rem] overflow-hidden mb-4 border border-slate-50 relative">
                    {bead.imageUrl ? (
                      <img src={bead.imageUrl} className="w-full h-full object-cover" alt={bead.name} />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-200"><ImageIcon size={48} /></div>
                    )}
                    <div className="absolute top-2 left-2 bg-white/95 px-2 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest text-indigo-600 shadow-sm">
                      {bead.status}
                    </div>
                  </div>
                  <h3 className="font-black text-[11px] truncate text-slate-800 uppercase px-1 leading-tight">{bead.name}</h3>
                  <div className="flex items-center justify-between px-1 mt-1">
                    <span className="text-[8px] text-indigo-700 font-black uppercase tracking-widest bg-indigo-50 px-2 py-1 rounded-md">{bead.type}</span>
                    <span className="text-[10px] font-black text-slate-900">{bead.price}€</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VISTA RISULTATI AI */}
        {view === 'searchResults' && (
          <div className="space-y-6 animate-in slide-in-from-bottom-6">
            <div className="flex items-center gap-4">
              <button onClick={() => setView('list')} className="p-3 hover:bg-slate-100 rounded-full transition-all"><ChevronLeft size={28} /></button>
              <h2 className="text-xl font-black uppercase text-slate-800 tracking-tighter">Risultati Archivio</h2>
            </div>
            <div className="space-y-4">
              {searchResults.map((result, idx) => (
                <button key={idx} onClick={() => { setSelectedBead(result); setView('edit'); }} className="w-full bg-white p-5 rounded-[1.8rem] border border-slate-100 shadow-sm hover:border-indigo-200 transition-all flex items-center justify-between text-left group">
                  <div className="flex items-center gap-5 flex-1 min-w-0">
                    <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center text-indigo-400 border border-slate-100"><Database size={24} /></div>
                    <div className="min-w-0">
                      <h4 className="font-black text-slate-800 uppercase text-[14px] truncate">{result.name}</h4>
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mt-1">
                        {result.type} • {result.sku || 'No SKU'} 
                        {result.status === 'Museo' && " • MUSEO"}
                      </p>
                    </div>
                  </div>
                  <ChevronRight size={20} className="text-slate-200 group-hover:text-indigo-500" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* VISTA AI (STORYTELLER / SUGGERIMENTI) */}
        {view === 'aiView' && (
          <div className="space-y-8 animate-in slide-in-from-bottom-10">
            <div className="flex items-center gap-4">
              <button onClick={() => setView('list')} className="p-3 hover:bg-slate-100 rounded-full transition-all"><ChevronLeft size={28} /></button>
              <h2 className="text-xl font-black uppercase text-slate-800 tracking-tighter">Ispirazione ✨</h2>
            </div>
            <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-[3rem] p-10 text-white shadow-2xl relative overflow-hidden">
               <div className="absolute -top-10 -right-10 opacity-10"><Sparkles size={200} /></div>
               <div className="relative z-10 space-y-6">
                  <h3 className="text-2xl font-black uppercase tracking-tighter">{aiResponse?.title}</h3>
                  <div className="w-12 h-1 bg-white/30 rounded-full"></div>
                  <p className="text-lg font-medium leading-relaxed italic whitespace-pre-wrap">
                    "{aiResponse?.text}"
                  </p>
               </div>
            </div>
            <button onClick={() => setView('list')} className="w-full py-5 bg-white border-2 border-slate-100 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-slate-50 transition-all">Torna alla Collezione</button>
          </div>
        )}

        {/* VISTA EDIT / SCHEDA TECNICA */}
        {view === 'edit' && selectedBead && (
          <div className="bg-white rounded-[3rem] border border-slate-100 p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-10">
            <div className="flex items-center justify-between mb-8">
              <button onClick={() => searchResults.length > 0 ? setView('searchResults') : setView('list')} className="p-3 hover:bg-slate-50 rounded-full transition-all"><ChevronLeft size={32} /></button>
              <h2 className="text-2xl font-black uppercase text-slate-800 tracking-tighter">Scheda Tecnica</h2>
              <button onClick={() => getStylingAdvice(selectedBead)} disabled={aiActionLoading} className="p-3 bg-indigo-50 text-indigo-600 rounded-full hover:bg-indigo-100">
                {aiActionLoading ? <Loader2 size={20} className="animate-spin" /> : <Palette size={20} />}
              </button>
            </div>

            {aiResponse && (
              <div className="mb-8 p-6 bg-indigo-50 rounded-3xl border border-indigo-100 relative group animate-in zoom-in-95">
                <button onClick={() => setAiResponse(null)} className="absolute top-4 right-4 text-indigo-300 hover:text-indigo-600"><X size={16}/></button>
                <h4 className="text-[10px] font-black uppercase text-indigo-400 tracking-widest mb-3 flex items-center gap-2"><Sparkles size={12}/> Suggerimento AI</h4>
                <p className="text-xs font-bold text-indigo-900 leading-relaxed whitespace-pre-wrap">{aiResponse.text}</p>
              </div>
            )}

            <div className="flex flex-col items-center gap-8 mb-10">
               <div className="w-64 h-64 bg-slate-50 rounded-[3rem] overflow-hidden border-2 border-slate-50 relative shadow-2xl shadow-indigo-50 flex items-center justify-center group">
                {selectedBead.imageUrl ? (
                  <img src={selectedBead.imageUrl} className="w-full h-full object-cover" alt="Preview" />
                ) : (
                  <ImageIcon size={64} className="text-slate-200" />
                )}
                <div onClick={() => fileInputRef.current?.click()} className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer">
                  <Camera size={32} className="text-white" />
                </div>
               </div>

               <div className="flex gap-3 w-full">
                 <button onClick={openManualImageSearch} className="flex-1 flex items-center justify-center gap-3 py-5 bg-indigo-50 text-indigo-700 rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-indigo-100 shadow-sm active:scale-95 transition-all">
                   <SearchCode size={20} /> Trova Foto
                 </button>
                 <button onClick={() => fileInputRef.current?.click()} className="flex-1 flex items-center justify-center gap-3 py-5 bg-slate-100 text-slate-700 rounded-2xl font-black text-[11px] uppercase tracking-widest hover:bg-slate-200 shadow-sm active:scale-95 transition-all">
                   <ImagePlus size={20} /> Carica
                 </button>
               </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
              <div className="space-y-2">
                <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.25em] ml-1">Nome Modello</label>
                <input type="text" value={selectedBead?.name || ""} onChange={e => setSelectedBead({...selectedBead, name: e.target.value})} className="w-full bg-slate-50 border-none rounded-2xl px-6 py-5 font-black text-slate-800 text-sm uppercase shadow-inner" />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.25em] ml-1">Prezzo (€)</label>
                  <input type="text" value={selectedBead?.price || "0.00"} onBlur={(e) => setSelectedBead({...selectedBead, price: formatPrice(e.target.value)})} onChange={e => setSelectedBead({...selectedBead, price: e.target.value})} className="w-full bg-slate-50 border-none rounded-2xl px-6 py-5 font-black text-slate-800 text-sm shadow-inner" />
                </div>
                <div className="space-y-2">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.25em] ml-1">Codice SKU</label>
                  <input type="text" value={selectedBead?.sku || ""} onChange={e => setSelectedBead({...selectedBead, sku: e.target.value})} className="w-full bg-slate-50 border-none rounded-2xl px-6 py-5 font-black text-slate-800 text-sm outline-none uppercase shadow-inner" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.25em] ml-1 flex items-center gap-2"><Activity size={12}/> Stato</label>
                  <select value={selectedBead?.status || "In Collezione"} onChange={e => setSelectedBead({...selectedBead, status: e.target.value})} className="w-full bg-slate-50 border-none rounded-2xl px-5 py-5 font-black text-slate-800 bg-white shadow-inner uppercase text-[10px] outline-none tracking-tight">
                    {APP_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.25em] ml-1 flex items-center gap-2"><Scale size={12}/> Peso</label>
                  <input type="text" value={selectedBead?.weight || ""} onChange={e => setSelectedBead({...selectedBead, weight: e.target.value})} className="w-full bg-slate-50 border-none rounded-2xl px-6 py-5 font-black text-slate-800 text-sm shadow-inner" placeholder="2.10g" />
                </div>
              </div>
            </div>

            <div className="flex gap-4 pt-12">
              <button onClick={() => setView('list')} className="flex-1 py-6 bg-slate-100 text-slate-500 rounded-[1.5rem] font-black text-xs active:scale-95 shadow-sm uppercase tracking-widest transition-all">Annulla</button>
              <button onClick={() => saveBead(selectedBead)} className="flex-[2] py-6 bg-indigo-600 text-white rounded-[1.5rem] font-black text-sm shadow-2xl flex items-center justify-center gap-3 active:scale-95 transition-all uppercase tracking-widest"><Save size={24} /> Salva Cloud</button>
            </div>
          </div>
        )}
      </main>

      {/* Footer Nav */}
      <footer className="fixed bottom-0 left-0 w-full bg-white/80 backdrop-blur-lg py-4 border-t border-slate-100 flex justify-center items-center gap-6 z-30">
        <button onClick={() => setView('list')} className={`p-2 flex flex-col items-center gap-1 ${view === 'list' ? 'text-indigo-600' : 'text-slate-400'}`}>
          <Database size={20} />
          <span className="text-[8px] font-black uppercase tracking-widest">Collezione</span>
        </button>
        <div className="h-6 w-px bg-slate-200"></div>
        <button onClick={() => setView('aiView')} className={`p-2 flex flex-col items-center gap-1 ${view === 'aiView' ? 'text-purple-600' : 'text-slate-400'}`}>
          <Wand2 size={20} />
          <span className="text-[8px] font-black uppercase tracking-widest">Ispirazione ✨</span>
        </button>
      </footer>
    </div>
  );
}
