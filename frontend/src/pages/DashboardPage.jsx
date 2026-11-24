import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import { FileText, Loader2, ArrowRight, BrainCircuit, Sparkles } from 'lucide-react';

const DashboardPage = () => {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [menuOpenId, setMenuOpenId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const navigate = useNavigate();

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/documents');
      setDocuments(response.data.documents || []);
    } catch (error) {
      console.error('Failed to load documents', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDeleteDocument = useCallback(async (e, docId) => {
    e.stopPropagation();
    e.preventDefault();
    setDeletingId(docId);
    try {
      await api.delete(`/api/documents/${docId}`);
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err) {
      console.error('Failed to delete document', err);
      alert('Failed to delete document. See console for details.');
    } finally {
      setDeletingId(null);
      setConfirmDeleteId(null);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      <section className="flex flex-col md:flex-row items-center gap-8 bg-white/5 rounded-2xl p-8 border border-white/10">
        <div className="flex-1 space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-[#8c6b5d] to-[#4a3b32] bg-clip-text text-transparent drop-shadow-sm">
            Welcome to StudySync!
          </h1>
          <p className="text-[#6a5347] max-w-2xl text-lg leading-relaxed">
            Upload your lecture notes, PDFs, or Word documents. Our AI will extract the most important study points and help you revise with a custom multilingual tutor.
          </p>
        </div>
        <div className="w-48 h-48 md:w-64 md:h-64 flex-shrink-0">
          <img 
            src="/study-image.png" 
            alt="Smiling study books and pencil stand" 
            className="w-full h-full object-contain drop-shadow-xl hover:scale-105 transition-transform duration-300"
          />
        </div>
      </section>

      <section>
        <FileUpload onUploadComplete={fetchDocuments} />
      </section>

      <section className="glass-panel flex flex-col gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-accent/15 p-3 text-accent">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-[#4a3b32]">Upgrade Me</h2>
            <p className="mt-1 text-sm text-[#6a5347]">Explore a topic with a document-grounded flowchart and quiz.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            const selected = localStorage.getItem('studysync:selected-document');
            navigate(selected ? `/upgrade-me?document=${selected}` : '/upgrade-me');
          }}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90"
        >
          Upgrade Me
          <ArrowRight className="h-4 w-4" />
        </button>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <LibraryIcon className="w-5 h-5 text-accent" />
          Your Documents
        </h2>

        {isLoading ? (
          <div className="flex justify-center p-12">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <div className="glass-panel p-12 text-center text-gray-400">
            No documents uploaded yet. Upload your first document above to get started!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <div 
                key={doc.id}
                className="glass-panel p-5 hover:bg-white/[0.03] transition-colors group cursor-pointer relative"
                onClick={() => {
                  // Don't navigate if confirm panel is open for this doc
                  if (confirmDeleteId === doc.id || menuOpenId === doc.id) return;
                  navigate(`/study/${doc.id}`);
                }}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="p-2 bg-accent/20 rounded-lg text-accent">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === 'ready' ? (
                      <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400 border border-green-500/20">
                        Ready
                      </span>
                    ) : doc.status === 'processing' ? (
                      <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/20 flex items-center gap-1">
                        <Loader2 className="w-3 h-3 animate-spin"/> Processing
                      </span>
                    ) : (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-500/20 text-red-400 border border-red-500/20">
                        Error
                      </span>
                    )}

                    {/* Three-dot menu button */}
                    <button
                      onClick={(e) => { e.stopPropagation(); setMenuOpenId(menuOpenId === doc.id ? null : doc.id); setConfirmDeleteId(null); }}
                      className="text-gray-400 hover:text-white p-1 rounded"
                      aria-label="Document menu"
                    >
                      ⋮
                    </button>

                    {menuOpenId === doc.id && (
                      <div className="absolute right-5 top-12 bg-[#1b1918] border border-white/5 rounded shadow-md z-20">
                        <button
                          onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(doc.id); setMenuOpenId(null); }}
                          className="block px-4 py-2 text-sm text-red-400 hover:bg-white/5 w-full text-left"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                
                <h3 className="font-medium text-white truncate mb-1" title={doc.filename}>
                  {doc.filename}
                </h3>
                
                <div className="flex justify-between items-center text-xs text-gray-400 mt-4">
                  <span>{(doc.file_size / (1024 * 1024)).toFixed(1)} MB</span>
                  <span className="block">{new Date(doc.created_at).toLocaleDateString()}</span>
                </div>

                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-sm">
                  <span className="text-gray-300 flex items-center gap-1.5">
                    <BrainCircuit className="w-4 h-4 text-primary" />
                    {doc.has_notes ? 'Notes ready' : 'Generate notes'}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-white transition-colors group-hover:translate-x-1" />
                </div>

                {/* Confirm delete inline panel */}
                {confirmDeleteId === doc.id && (
                  <div
                    className="mt-3 p-3 bg-[#1a1310] border border-white/5 rounded text-sm text-[#f1d9c6]"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="mb-2">Delete &apos;{doc.filename}&apos;? This cannot be undone.</div>
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(null); }}
                        className="px-3 py-1 bg-white/5 rounded"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={(e) => handleDeleteDocument(e, doc.id)}
                        disabled={deletingId === doc.id}
                        className="px-3 py-1 bg-red-600 text-white rounded disabled:opacity-60"
                      >
                        {deletingId === doc.id ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

    </div>
  );
};

// Quick helper
const LibraryIcon = (props) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m16 6 4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/></svg>
);

export default DashboardPage;
