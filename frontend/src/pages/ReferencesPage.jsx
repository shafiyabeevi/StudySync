import { useState } from 'react';
import api from '../lib/api';
import { Search, Loader2, BookOpen, ExternalLink, GraduationCap, Video, Globe } from 'lucide-react';

const ReferencesPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setHasSearched(true);
    setResults([]);

    try {
      const response = await api.post('/api/search-references', { topic: query.trim() });
      setResults(response.data.results || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search for references. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getSourceIcon = (type) => {
    switch(type) {
      case 'book': return <BookOpen className="w-4 h-4 text-primary" />;
      case 'academic': return <GraduationCap className="w-4 h-4 text-accent" />;
      case 'video': return <Video className="w-4 h-4 text-red-400" />;
      default: return <Globe className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-in fade-in duration-500 space-y-8">
      <div className="text-center space-y-4 mb-8">
        <h1 className="text-3xl font-bold text-white">Find Reference Books</h1>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Search for textbooks, academic papers, and highly-rated tutorials. We filter out the noise so you get links you can actually study from.
        </p>
      </div>

      <form onSubmit={handleSearch} className="relative z-10 max-w-2xl mx-auto">
        <div className="relative glass-panel rounded-full overflow-hidden flex shadow-lg hover:shadow-primary/5 transition-shadow">
          <div className="pl-6 flex items-center justify-center text-gray-400">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search topic (e.g., Computer Networks, Thermodynamics)..."
            className="flex-1 bg-transparent border-none py-4 px-4 text-white focus:outline-none focus:ring-0 placeholder-gray-500"
          />
          <button 
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-8 bg-primary hover:bg-primary/90 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Search'}
          </button>
        </div>
      </form>

      {/* Results Area */}
      <div className="mt-12 space-y-4">
        {isLoading && (
          <div className="flex flex-col items-center justify-center p-12 text-gray-400 gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="animate-pulse">Scouring the web for the best reference materials...</p>
          </div>
        )}

        {error && (
          <div className="glass-panel p-6 text-center text-red-400 border-red-500/20 bg-red-500/5">
            {error}
          </div>
        )}

        {!isLoading && !error && hasSearched && results.length === 0 && (
          <div className="glass-panel p-12 text-center text-gray-400">
            No academic references found for this topic. Try broader keywords.
          </div>
        )}

        {!isLoading && results.length > 0 && (
          <div className="space-y-4 animate-in slide-in-from-bottom-4 duration-500">
            {results.map((result, idx) => (
              <a 
                key={idx} 
                href={result.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="block glass-panel p-6 hover:bg-white/[0.03] hover:border-white/20 transition-all group"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white/5 rounded-lg border border-white/10 group-hover:bg-white/10 transition-colors">
                      {getSourceIcon(result.source_type)}
                    </div>
                    <h3 className="text-lg font-medium text-white group-hover:text-primary transition-colors">
                      {result.title}
                    </h3>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-white transition-colors flex-shrink-0 mt-2" />
                </div>
                
                <p className="text-sm text-gray-400 line-clamp-2 md:line-clamp-3 ml-12 leading-relaxed">
                  {result.description}
                </p>
                
                <div className="mt-4 ml-12 flex items-center gap-2">
                  <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-1 bg-white/5 rounded text-gray-400 border border-white/5">
                    {result.source_type}
                  </span>
                  <span className="text-xs text-gray-500 truncate max-w-[200px] md:max-w-md">
                    {new URL(result.url).hostname}
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReferencesPage;
