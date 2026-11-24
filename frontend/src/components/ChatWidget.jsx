import { useState, useRef, useEffect } from 'react';
import api from '../lib/api';
import ReactMarkdown from 'react-markdown';
import { MessageSquare, X, Send, User, Bot, Sparkles } from 'lucide-react';

const ChatWidget = ({ documentId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I am your study tutor. Ask me anything about this document, and let me know if you need explanations in a specific language (e.g., "explain in Tamil").' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage = { role: 'user', content: input.trim() };
    const chatHistorySnapshot = [...messages];
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await api.post('/api/chat', {
        document_id: documentId,
        message: userMessage.content,
        chat_history: chatHistorySnapshot.filter(m => m.role !== 'system') // send previous messages
      });

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response,
        language: response.data.language
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '*[Error]* Failed to get response. Please try again or check your API limits.' 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="absolute bottom-6 right-6 w-14 h-14 bg-primary hover:bg-primary/90 text-white rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(var(--color-primary),0.4)] transition-transform hover:scale-110 z-50"
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="absolute bottom-6 right-6 w-[380px] h-[600px] max-h-[80vh] bg-[#302c2a] border border-[#52443a] rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden animate-in slide-in-from-bottom-8 duration-300">
      {/* Header */}
      <div className="bg-[#4d3c31] border-b border-[#302c2a] p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-[#7a6150]/30 rounded-md">
            <Sparkles className="w-4 h-4 text-[#d4c4b7]" />
          </div>
          <h3 className="font-medium text-[#d4c4b7]" style={{ fontFamily: 'var(--font-inter)' }}>Study Tutor</h3>
        </div>
        <button 
          onClick={() => setIsOpen(false)}
          className="text-[#d4c4b7] hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-[#7a6150] text-[#d4c4b7]' : 'bg-[#52443a] text-[#d4c4b7]'}`}>
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            
            <div className={`max-w-[80%] rounded-2xl p-3 text-sm flex flex-col ${
              msg.role === 'user' 
                ? 'bg-[#4a3b32] text-[#d4c4b7] rounded-tr-sm border border-[#52443a]' 
                : 'bg-[#24201e] text-[#d4c4b7] rounded-tl-sm border border-[#302c2a]'
            }`}>
              {/* Note: prose-invert automatically makes text inside Markdown white/light gray which overrides our text color. We need to force it. */}
              <div className="prose prose-invert prose-sm max-w-none prose-p:text-[#d4c4b7] prose-headings:text-[#d4c4b7] prose-strong:text-[#d4c4b7] prose-li:text-[#d4c4b7]">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {msg.language && msg.language !== 'en' && msg.role === 'assistant' && (
                <span className="text-[10px] text-[#7a6150] mt-2 flex justify-end opacity-70 font-mono">
                  {msg.language.toUpperCase()} response generated
                </span>
              )}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-[#52443a] text-[#d4c4b7] flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-[#24201e] rounded-2xl rounded-tl-sm p-4 border border-[#302c2a] flex gap-1 items-center">
              <span className="w-1.5 h-1.5 bg-[#8c7a6e] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-[#8c7a6e] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-[#8c7a6e] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="p-3 bg-[#302c2a] border-t border-[#3b322d] flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question or 'explain in Tamil'..."
          className="flex-1 bg-[#3b322d] border border-[#52443a] rounded-xl px-4 py-2.5 text-sm text-[#d4c4b7] placeholder-[#8c7a6e] focus:outline-none focus:border-[#7a6150] transition-colors"
        />
        <button
          type="submit"
          disabled={!input.trim() || isTyping}
          className="w-10 h-10 flex flex-shrink-0 items-center justify-center rounded-xl bg-[#7a6150] hover:bg-[#685244] text-[#d4c4b7] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

export default ChatWidget;
