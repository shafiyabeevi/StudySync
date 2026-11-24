import { useEffect, useMemo, useState } from 'react';
import api from '../lib/api';
import { BookOpen, Mic, MicOff, Sparkles, TrendingUp } from 'lucide-react';

const TeachItBack = ({ documentId }) => {
  const [topic, setTopic] = useState('Main Topic');
  const [explanation, setExplanation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = false;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(' ');
      setExplanation(transcript);
    };

    recognitionInstance.onerror = () => {
      setIsListening(false);
    };

    recognitionInstance.onend = () => {
      setIsListening(false);
    };

    setRecognition(recognitionInstance);
  }, []);

  useEffect(() => {
    const fetchAttempts = async () => {
      try {
        const response = await api.get(`/api/teach-it-back/${documentId}`, { params: { topic } });
        setAttempts(response.data.attempts || []);
      } catch (err) {
        console.error(err);
      }
    };

    if (documentId) fetchAttempts();
  }, [documentId, topic]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!explanation.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post('/api/teach-it-back', {
        document_id: documentId,
        topic,
        student_explanation: explanation,
      });
      setResult(response.data);
      const attemptsResponse = await api.get(`/api/teach-it-back/${documentId}`, { params: { topic } });
      setAttempts(attemptsResponse.data.attempts || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'The evaluation service is unavailable right now. Please try again in a moment.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const averageScore = useMemo(() => {
    if (!attempts.length) return null;
    const total = attempts.reduce((sum, attempt) => sum + (attempt.score || 0), 0);
    return Math.round(total / attempts.length);
  }, [attempts]);

  const toggleVoiceInput = () => {
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
      setIsListening(false);
      return;
    }
    recognition.start();
    setIsListening(true);
  };

  return (
    <div className="rounded-2xl border border-[#5f4635] bg-[#2b221d] p-4 text-[#e8d8c8] shadow-inner">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm font-semibold text-[#f7cc9d]">
            <BookOpen className="h-4 w-4" />
            Teach It Back
          </div>
          <p className="mt-1 text-xs text-[#b89c86]">
            Explain the topic in your own words and let the AI coach you gently.
          </p>
        </div>
        {averageScore !== null && (
          <div className="rounded-full bg-[#4d3a2f] px-3 py-1 text-xs text-[#f7cc9d]">
            Avg {averageScore}/10
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          className="w-full rounded-xl border border-[#5f4635] bg-[#1e1815] px-3 py-2 text-sm text-[#f4e5d6]"
          placeholder="Topic name"
        />
        <textarea
          value={explanation}
          onChange={(event) => setExplanation(event.target.value)}
          rows={5}
          className="w-full rounded-xl border border-[#5f4635] bg-[#1e1815] px-3 py-2 text-sm text-[#f4e5d6]"
          placeholder="Explain this topic as if you were teaching a classmate."
        />
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={isLoading || !explanation.trim()}
            className="rounded-xl bg-[#7d5a42] px-3 py-2 text-sm font-medium text-[#f8ebdf] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isLoading ? 'Checking your explanation…' : 'Get feedback'}
          </button>
          {recognition && (
            <button
              type="button"
              onClick={toggleVoiceInput}
              className="rounded-xl border border-[#5f4635] px-3 py-2 text-sm text-[#f7cc9d]"
            >
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>
          )}
        </div>
      </form>

      {error && <p className="mt-3 text-sm text-amber-300">{error}</p>}

      {result && (
        (() => {
          // Normalize result fields to be safe if backend returned strings
          const _rights = Array.isArray(result.rights)
            ? result.rights
            : (result.rights ? [result.rights] : []);
          const _wrongs = Array.isArray(result.wrongs)
            ? result.wrongs
            : (result.wrongs ? [result.wrongs] : []);
          const _missing = Array.isArray(result.missing)
            ? result.missing
            : (result.missing ? [result.missing] : []);
          const _conceptEvaluations = Array.isArray(result.concept_evaluations)
            ? result.concept_evaluations
            : [];

          let _modelAnswer = result.model_answer || '';
          let _result = { ...result, rights: _rights, wrongs: _wrongs, missing: _missing, model_answer: _modelAnswer };

          try {
            if (typeof _modelAnswer === 'string' && _modelAnswer.includes('{')) {
              // try to extract the first JSON object in the string (handles fenced ```json blocks)
              const start = _modelAnswer.indexOf('{');
              let depth = 0;
              let end = -1;
              for (let i = start; i < _modelAnswer.length; i++) {
                if (_modelAnswer[i] === '{') depth += 1;
                else if (_modelAnswer[i] === '}') {
                  depth -= 1;
                  if (depth === 0) { end = i; break; }
                }
              }
              if (start >= 0 && end > start) {
                const candidate = _modelAnswer.slice(start, end + 1);
                const maybe = JSON.parse(candidate);
                if (maybe && typeof maybe === 'object') {
                  if (maybe.model_answer) _modelAnswer = maybe.model_answer;
                  if (Array.isArray(maybe.rights) && maybe.rights.length) _rights.splice(0, _rights.length, ...maybe.rights);
                  if (Array.isArray(maybe.wrongs) && maybe.wrongs.length) _wrongs.splice(0, _wrongs.length, ...maybe.wrongs);
                  if (Array.isArray(maybe.missing) && maybe.missing.length) _missing.splice(0, _missing.length, ...maybe.missing);
                  if (maybe.score !== undefined) _result.score = maybe.score;
                  if (maybe.message) _result.message = maybe.message;
                }
              }
            }
          } catch (e) {
            // leave as-is
          }

          // Prepare a clean display string for model_answer (strip fenced JSON, backticks, and outer quotes)
          let displayModel = _modelAnswer || '';
          try {
            displayModel = displayModel.replace(/```\w*\s*/g, '').replace(/```/g, '').trim();
            if ((displayModel.startsWith('"') && displayModel.endsWith('"')) || (displayModel.startsWith("'") && displayModel.endsWith("'"))) {
              displayModel = displayModel.slice(1, -1).trim();
            }
          } catch (e) {
            /* ignore */
          }

          _result.model_answer = displayModel;


          return (
        <div className="mt-4 space-y-3 rounded-xl border border-[#5f4635] bg-[#211a15] p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#f7cc9d]">
              <Sparkles className="h-4 w-4" />
              Feedback
            </div>
              <div className="rounded-full bg-[#3f2f24] px-2 py-1 text-xs text-[#f7cc9d]">
              {_result.score}/10
            </div>
          </div>
          <p className="text-sm text-[#f4e5d6]">{_result.message}</p>
          <div className="space-y-2 text-sm">
            {_conceptEvaluations.length > 0 && (
              <div>
                <h4 className="font-semibold text-[#f7cc9d]">PDF-grounded concept rubric</h4>
                <div className="mt-2 space-y-2">
                  {_conceptEvaluations.map((item) => (
                    <div key={item.concept} className="rounded-lg border border-[#5f4635] p-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium text-[#f4e5d6]">{item.concept}</span>
                        <span className="text-xs capitalize text-[#f7cc9d]">
                          {item.status?.replaceAll('_', ' ')} · {item.importance} ({item.points_earned}/{item.weight})
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[#d9c5b4]">{item.description}</p>
                      <p className="mt-1 text-xs text-[#b89c86]">From your PDF: “{item.source_evidence}”</p>
                      {item.student_evidence && (
                        <p className="mt-1 text-xs text-[#b89c86]">Your explanation: “{item.student_evidence}”</p>
                      )}
                      {item.feedback && <p className="mt-1 text-xs text-[#d9c5b4]">{item.feedback}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h4 className="font-semibold text-[#f7cc9d]">What you got right</h4>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-[#d9c5b4]">
                {_result.rights.length ? _result.rights.map((item) => <li key={item}>{item}</li>) : <li>Nothing noted yet.</li>}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-[#f7cc9d]">What was missing</h4>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-[#d9c5b4]">
                {_result.missing.length ? _result.missing.map((item) => <li key={item}>{item}</li>) : <li>Nothing missing.</li>}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-[#f7cc9d]">What was inaccurate</h4>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-[#d9c5b4]">
                {_result.wrongs.length ? _result.wrongs.map((item) => <li key={item}>{item}</li>) : <li>Nothing incorrect noted.</li>}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-[#f7cc9d]">Model answer</h4>
              <p className="mt-1 text-[#d9c5b4]">{_result.model_answer}</p>
            </div>
          </div>
        </div>
          );
        })()
      )}

      {attempts.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[#f7cc9d]">
            <TrendingUp className="h-4 w-4" />
            Recent attempts
          </div>
          <div className="space-y-2">
            {attempts.slice(0, 3).map((attempt) => (
              <div key={attempt.id} className="rounded-xl border border-[#5f4635] bg-[#221a15] p-2 text-sm text-[#e4cebf]">
                <div className="mb-1 flex items-center justify-between">
                  <span className="font-medium">{attempt.topic || 'Untitled topic'}</span>
                  <span className="text-xs text-[#f7cc9d]">{attempt.score}/10</span>
                </div>
                <p className="line-clamp-2 text-xs text-[#c8ad95]">{attempt.student_explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TeachItBack;
