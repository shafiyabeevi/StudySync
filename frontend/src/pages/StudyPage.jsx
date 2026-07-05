import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ChevronLeft, FileText, Loader2 } from 'lucide-react';
import ExamNotes from '../components/ExamNotes';
import ChatWidget from '../components/ChatWidget';
import FeedbackWidget from '../components/FeedbackWidget';

const StudyPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [documentContent, setDocumentContent] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDocumentData = async () => {
      try {
        const textResponse = await axios.get(`/api/documents/${id}/text`);
        setDocumentContent(textResponse.data);
      } catch (err) {
        console.error("Failed to load document text:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDocumentData();
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  if (!documentContent) {
    return (
      <div className="text-center mt-20">
        <h2 className="text-2xl font-bold text-white mb-4">Document Not Found</h2>
        <button 
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-md text-white transition-colors"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col pt-2 animate-in fade-in duration-300">
      <div className="flex items-center gap-4 mb-6">
        <button 
          onClick={() => navigate('/')}
          className="p-2 hover:bg-white/10 rounded-full transition-colors group"
        >
          <ChevronLeft className="w-5 h-5 text-gray-400 group-hover:text-white" />
        </button>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent/20 rounded-lg text-accent">
            <FileText className="w-5 h-5" />
          </div>
          <h1 className="text-xl font-semibold text-white tracking-tight truncate max-w-lg" title={documentContent.filename}>
            {documentContent.filename}
          </h1>
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-6 min-h-0 relative">
        {/* Left Column: Original Text */}
        <div className="w-full lg:w-1/2 flex flex-col glass-panel flex flex-col overflow-hidden">
          <div className="bg-white/5 border-b border-white/10 p-4">
            <h2 className="font-medium text-[#8c6b5d]">Document Content</h2>
          </div>
          <div className="p-6 overflow-y-auto flex-1 text-[#6a5347] text-sm whitespace-pre-wrap font-mono leading-relaxed">
            {documentContent.text || "No text could be extracted from this document."}
          </div>
        </div>

        {/* Right Column: Exam Notes */}
        <div className="w-full lg:w-1/2 flex flex-col overflow-hidden">
          <div className="glass-panel flex flex-col flex-1 overflow-hidden">
            <ExamNotes documentId={id} />
          </div>
        </div>

        {/* Floating Chat Widget */}
        <ChatWidget documentId={id} />
      </div>

      <div className="mt-4 flex justify-end">
        <FeedbackWidget featureType="general" referenceId={null} />
      </div>
    </div>
  );
};

export default StudyPage;
