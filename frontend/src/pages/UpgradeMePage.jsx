import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  ArrowDown,
  CheckCircle2,
  Loader2,
  RotateCcw,
  Sparkles,
  XCircle,
} from 'lucide-react';
import api from '../lib/api';

const requestError = (error) =>
  error.response?.data?.detail ||
  'We could not complete this request. Please try again.';

const UpgradeMePage = () => {
  const [topic, setTopic] = useState('');
  const [documents, setDocuments] = useState([]);
  const [documentId, setDocumentId] = useState('');
  const [flowchart, setFlowchart] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api.get('/api/documents')
      .then(({ data }) => {
        if (!active) return;
        const ready = (data.documents || []).filter(
          (document) => document.status === 'ready' &&
            String(document.file_type || '').toLowerCase() === 'pdf'
        );
        setDocuments(ready);
        setDocumentId('');
      })
      .catch((err) => setError(requestError(err)));
    return () => { active = false; };
  }, []);

  const selectedDocument = useMemo(
    () => documents.find((document) => document.id === documentId),
    [documents, documentId]
  );

  const generateFlowchart = async (event) => {
    event.preventDefault();
    if (!documentId) {
      setError('Please select a PDF document.');
      return;
    }
    if (!topic.trim()) {
      setError('Please enter a topic or question to improve.');
      return;
    }
    setError('');
    setFlowchart(null);
    setQuiz(null);
    setResults(null);
    setAnswers({});
    setLoading('flowchart');
    try {
      const { data } = await api.post('/api/upgrade-me/flowchart', {
        document_id: documentId,
        topic: topic.trim(),
      });
      setFlowchart(data);
    } catch (err) {
      setError(requestError(err));
    } finally {
      setLoading('');
    }
  };

  const takeQuiz = async () => {
    setError('');
    setResults(null);
    setAnswers({});
    setLoading('quiz');
    try {
      const { data } = await api.post('/api/upgrade-me/quiz', {
        document_id: documentId,
        topic: topic.trim(),
      });
      setQuiz(data);
    } catch (err) {
      setError(requestError(err));
    } finally {
      setLoading('');
    }
  };

  const submitQuiz = async (event) => {
    event.preventEvent?.();
    event.preventDefault();
    if (!quiz) return;
    const unanswered = quiz.questions.filter((question) => !String(answers[question.id] || '').trim());
    if (unanswered.length) {
      setError('Please answer every question before submitting.');
      return;
    }
    setError('');
    setLoading('results');
    try {
      const answerPayload = quiz.questions.map((question) => ({
        question_id: question.id,
        answer: answers[question.id],
        question: question.question,
        type: question.type,
        correct_answer: question.correct_answer,
        explanation: question.explanation,
      }));
      const { data } = await api.post('/api/upgrade-me/quiz/evaluate', {
        document_id: documentId,
        topic: topic.trim(),
        answers: answerPayload,
      });
      setResults(data);
    } catch (err) {
      setError(requestError(err));
    } finally {
      setLoading('');
    }
  };

  const retryQuiz = () => {
    setResults(null);
    setAnswers({});
    setError('');
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 animate-in fade-in duration-300">
      <form onSubmit={generateFlowchart} className="glass-panel mx-auto max-w-3xl space-y-5 p-5 sm:p-6">
        <section>
          <label htmlFor="upgrade-pdf" className="mb-2 block text-sm font-semibold text-[#4a3b32]">
            Select a PDF document
          </label>
          <select
            id="upgrade-pdf"
            value={documentId}
            onChange={(event) => {
              setDocumentId(event.target.value);
              setError('');
            }}
            className="w-full rounded-xl border border-[#d9c8b9] bg-white px-4 py-3 text-sm text-[#4a3b32] outline-none focus:border-accent"
          >
            <option value="">Choose a PDF...</option>
            {documents.map((document) => (
              <option key={document.id} value={document.id}>{document.filename}</option>
            ))}
          </select>
          {selectedDocument && (
            <p className="mt-2 text-xs font-medium text-[#8c6b5d]">
              Selected PDF: {selectedDocument.filename}
            </p>
          )}
          {documents.length === 0 && (
            <p className="mt-2 text-xs text-[#8c6b5d]">No ready PDF documents are available. Upload a PDF first.</p>
          )}
        </section>

        <section>
          <h1 className="mb-2 text-xl font-bold text-[#4a3b32]">What do you want to improve?</h1>
          <textarea
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Enter a topic or ask a question about your document..."
            rows={3}
            className="w-full rounded-xl border border-[#d9c8b9] bg-white px-4 py-3 text-sm text-[#4a3b32] outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/10"
            maxLength={200}
          />
        </section>

        <div className="flex justify-center">
          <button
            type="submit"
            disabled={loading === 'flowchart' || !documentId}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
          >
            {loading === 'flowchart' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Start Improving
          </button>
        </div>
      </form>

      {error && (
        <div role="alert" className="mx-auto flex max-w-3xl items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {flowchart && (
        <section className="glass-panel overflow-hidden p-5 sm:p-7">
          <h2 className="text-2xl font-bold text-[#4a3b32]">{flowchart.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-[#6a5347]">{flowchart.summary}</p>
          <div className="mt-6 flex flex-col items-center">
            {flowchart.nodes.map((node, index) => (
              <FlowNode key={node.id} node={node} isLast={index === flowchart.nodes.length - 1} edge={flowchart.edges.find((edge) => edge.from === node.id)} />
            ))}
          </div>
          {!quiz && (
            <div className="mt-7 flex justify-center">
              <button
                type="button"
                onClick={takeQuiz}
                disabled={loading === 'quiz'}
                className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3 text-sm font-semibold text-white disabled:opacity-60"
              >
                {loading === 'quiz' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                Take Quiz
              </button>
            </div>
          )}
        </section>
      )}

      {quiz && !results && (
        <section className="glass-panel p-5 sm:p-7">
          <h2 className="text-2xl font-bold text-[#4a3b32]">Quiz: {quiz.topic}</h2>
          <form onSubmit={submitQuiz} className="mt-5 space-y-5">
            {quiz.questions.map((question, index) => (
              <article key={question.id} className="rounded-xl border border-[#e4d8cd] bg-white/60 p-4 sm:p-5">
                <p className="text-sm font-semibold text-[#4a3b32]">{index + 1}. {question.question}</p>
                {question.type === 'multiple_choice' ? (
                  <div className="mt-3 space-y-2">
                    {question.options.map((option) => (
                      <label key={option} className="flex cursor-pointer items-start gap-3 rounded-lg px-2 py-2 text-sm text-[#6a5347] hover:bg-accent/5">
                        <input
                          type="radio"
                          name={question.id}
                          value={option}
                          checked={answers[question.id] === option}
                          onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                          className="mt-0.5 accent-[#8c6b5d]"
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={answers[question.id] || ''}
                    onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                    rows={3}
                    placeholder="Explain the concept in your own words..."
                    className="mt-3 w-full rounded-lg border border-[#d9c8b9] bg-white px-3 py-2 text-sm text-[#4a3b32] outline-none focus:border-accent"
                  />
                )}
              </article>
            ))}
            <button
              type="submit"
              disabled={loading === 'results'}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white disabled:opacity-60 sm:w-auto"
            >
              {loading === 'results' && <Loader2 className="h-4 w-4 animate-spin" />}
              Submit Quiz
            </button>
          </form>
        </section>
      )}

      {results && quiz && (
        <section className="glass-panel p-5 sm:p-7">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-wide text-[#8c6b5d]">Final Score</p>
            <p className="mt-1 text-4xl font-bold text-[#4a3b32]">{results.score}/{results.total}</p>
            <p className="mt-2 text-sm text-[#6a5347]">{results.feedback}</p>
          </div>
          <div className="mt-6 space-y-3">
            {results.results.map((result, index) => (
              <article key={result.question_id} className="rounded-xl border border-[#e4d8cd] bg-white/60 p-4">
                <div className="flex items-start gap-3">
                  {result.correct
                    ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
                    : <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />}
                  <div>
                    <p className="font-semibold text-[#4a3b32]">Question {index + 1}: {result.correct ? 'Correct' : 'Not quite'}</p>
                    <p className="mt-1 text-sm text-[#6a5347]">{result.feedback}</p>
                    <p className="mt-2 text-sm text-[#4a3b32]"><strong>Correct answer:</strong> {result.correct_answer}</p>
                    {result.explanation && <p className="mt-1 text-sm text-[#6a5347]">{result.explanation}</p>}
                  </div>
                </div>
              </article>
            ))}
          </div>
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={retryQuiz}
              className="inline-flex items-center gap-2 rounded-xl border border-[#b08d7a] px-5 py-3 text-sm font-semibold text-[#6a5347]"
            >
              <RotateCcw className="h-4 w-4" />
              Retry Quiz
            </button>
          </div>
        </section>
      )}
    </div>
  );
};

const FlowNode = ({ node, isLast, edge }) => {
  const shape = node.kind === 'decision'
    ? 'border-dashed bg-amber-50'
    : node.kind === 'start'
      ? 'border-emerald-300 bg-emerald-50'
      : node.kind === 'end'
        ? 'border-accent bg-[#f1e9e1]'
        : 'border-[#d9c8b9] bg-white';

  return (
    <>
      <article className={`w-full max-w-xl rounded-xl border p-4 text-center shadow-sm ${shape}`}>
        <p className="text-xs font-semibold uppercase tracking-wide text-[#9b7862]">{node.kind}</p>
        <h3 className="mt-1 font-bold text-[#4a3b32]">{node.label}</h3>
        <p className="mt-1 text-sm leading-relaxed text-[#6a5347]">{node.explanation}</p>
      </article>
      {!isLast && (
        <div className="flex h-14 flex-col items-center justify-center text-[#8c6b5d]">
          {edge?.label && <span className="mb-0.5 rounded-full bg-[#f1e9e1] px-2 text-xs">{edge.label}</span>}
          <ArrowDown className="h-5 w-5" />
        </div>
      )}
    </>
  );
};

export default UpgradeMePage;
