import { useEffect, useMemo, useState } from 'react';
import api from '../lib/api';
import { BookOpen, FileText, Sparkles, X } from 'lucide-react';
import TeachItBack from './TeachItBack';

const TeachItBackModal = ({ isOpen, onClose, documentId }) => {
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(documentId || '');
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setSelectedDocumentId(documentId || '');
  }, [documentId, isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const loadDocuments = async () => {
      try {
        setIsLoadingDocuments(true);
        const response = await api.get('/api/documents');
        setDocuments(response.data.documents || []);
      } catch (err) {
        console.error('Failed to load documents for Teach It Back', err);
      } finally {
        setIsLoadingDocuments(false);
      }
    };

    loadDocuments();
  }, [isOpen]);

  const activeDocument = useMemo(() => {
    return documents.find((item) => item.id === selectedDocumentId) || null;
  }, [documents, selectedDocumentId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 px-4 py-6 backdrop-blur-sm">
      <div className="relative w-full max-w-3xl max-h-[85vh] overflow-hidden rounded-2xl border border-white/10 bg-[#1e1815] shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 bg-[#2b221d] px-4 py-3">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-[#f7cc9d]">
              <BookOpen className="h-4 w-4" />
              Teach It Back
            </div>
            <p className="mt-1 text-xs text-[#b89c86]">
              Practice explaining a topic in your own words and get supportive feedback.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[#5f4635] p-2 text-[#f7cc9d] transition hover:bg-white/10"
            aria-label="Close Teach It Back"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[calc(85vh-64px)] overflow-y-auto p-4">
          {!selectedDocumentId ? (
            <div className="rounded-2xl border border-[#5f4635] bg-[#2b221d] p-4 text-[#e8d8c8]">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#f7cc9d]">
                <FileText className="h-4 w-4" />
                Choose a document to practice explaining
              </div>
              {isLoadingDocuments ? (
                <p className="text-sm text-[#b89c86]">Loading documents…</p>
              ) : documents.length === 0 ? (
                <p className="text-sm text-[#b89c86]">No documents are available yet.</p>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <button
                      key={doc.id}
                      type="button"
                      onClick={() => setSelectedDocumentId(doc.id)}
                      className="flex w-full items-center justify-between rounded-xl border border-[#5f4635] bg-[#1e1815] px-3 py-2 text-left text-sm text-[#f4e5d6] transition hover:border-[#7d5a42]"
                    >
                      <span>{doc.filename}</span>
                      <span className="text-xs text-[#b89c86]">{doc.status}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-2xl border border-[#5f4635] bg-[#2b221d] p-3 text-sm text-[#f4e5d6]">
                <div className="mb-1 flex items-center gap-2 text-[#f7cc9d]">
                  <Sparkles className="h-4 w-4" />
                  Practice mode for {activeDocument?.filename || 'selected document'}
                </div>
                <p className="text-xs text-[#b89c86]">
                  Use the prompts below to explain the topic in your own words and receive supportive feedback.
                </p>
              </div>
              <TeachItBack documentId={selectedDocumentId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeachItBackModal;
