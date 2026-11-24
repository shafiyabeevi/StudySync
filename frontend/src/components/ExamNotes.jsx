import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Loader2, BrainCircuit, Sparkles, BookOpen, KeyRound, Lightbulb } from 'lucide-react';

const ExamNotes = ({ documentId }) => {
  const [notes, setNotes] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const response = await api.get(`/api/documents/${documentId}/notes`);
        if (response.data.notes) {
          setNotes(response.data.notes);
        } else if (response.data.status !== 'ready') {
          setError('Document is still processing. Please wait...');
        }
      } catch (err) {
        setError('Failed to load or generate exam notes.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchNotes();
  }, [documentId]);

  if (isLoading) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center p-8 bg-black/20">
        <BrainCircuit className="w-12 h-12 text-primary animate-pulse mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">Generating Exam Notes</h3>
        <p className="text-sm text-gray-400 text-center max-w-sm">
          Our AI is reading your document and extracting the most important study points...
        </p>
        <div className="mt-6 flex gap-2">
          <div className="w-2 h-2 rounded-full bg-primary/40 animate-ping" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 rounded-full bg-primary/60 animate-ping" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-ping" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    );
  }

  if (error || !notes) {
    return (
      <div className="flex-1 p-6 flex items-center justify-center text-center">
        <p className="text-gray-400">{error || "Notes are currently unavailable."}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="bg-primary/10 border-b border-primary/20 p-4 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-primary" />
        <h2 className="font-medium text-primary">AI Exam Notes</h2>
      </div>
      
      <div className="p-6 overflow-y-auto flex-1 custom-scrollbar space-y-8">
        {notes.title && (
          <h3 className="text-2xl font-bold text-white mb-6 border-b border-white/10 pb-4">
            {notes.title}
          </h3>
        )}

        {/* Sub Topics */}
        {notes.sub_topics && notes.sub_topics.length > 0 && (
          <div className="space-y-6">
            {notes.sub_topics.map((topic, idx) => (
              <div key={idx} className="space-y-3">
                <h4 className="text-lg font-semibold text-accent flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  {topic.heading}
                </h4>
                <ul className="space-y-2">
                  {topic.points.map((point, pIdx) => (
                    <li key={pIdx} className="text-gray-300 text-sm flex items-start gap-3">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary/60 mt-1.5 flex-shrink-0" />
                      <span className="leading-relaxed">{point}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}

        {/* Key Definitions */}
        {notes.key_definitions && notes.key_definitions.length > 0 && (
          <div className="mt-8 bg-white/5 rounded-xl p-5 border border-white/10">
            <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-primary" />
              Key Definitions
            </h4>
            <div className="space-y-4">
              {notes.key_definitions.map((def, idx) => (
                <div key={idx} className="text-sm">
                  <span className="font-semibold text-accent">{def.term}: </span>
                  <span className="text-gray-300">{def.definition}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Formulas */}
        {notes.important_formulas && notes.important_formulas.length > 0 && (
          <div className="mt-8 bg-primary/5 rounded-xl p-5 border border-primary/20">
            <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
              <span className="font-serif italic text-primary font-bold">f(x)</span>
              Important Formulas
            </h4>
            <ul className="space-y-3">
              {notes.important_formulas.map((formula, idx) => (
                <li key={idx} className="text-sm font-mono bg-black/40 p-3 rounded border border-white/5 text-gray-300">
                  {formula}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Likely Exam Questions */}
        {notes.likely_exam_questions && notes.likely_exam_questions.length > 0 && (
          <div className="mt-8 bg-accent/5 rounded-xl p-5 border border-accent/20">
            <h4 className="text-md font-semibold text-white mb-4 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-accent" />
              Likely Exam Questions
            </h4>
            <ul className="space-y-2 list-decimal list-inside text-sm text-gray-300">
              {notes.likely_exam_questions.map((q, idx) => (
                <li key={idx} className="leading-relaxed mb-2 pb-2 border-b border-white/5 last:border-0 last:pb-0">{q}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExamNotes;
