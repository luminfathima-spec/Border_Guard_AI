import { useState } from 'react';
import { Bot, Send, User as UserIcon, Sparkles } from 'lucide-react';
import { aiApi } from '../services/sentinelApi';

export function AIAssistantPage() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([
    {
      role: 'assistant',
      text: 'Greetings, Commander. I am your SentinelAI Border Intelligence Analyst powered by Google Gemini. I have direct access to live CCTV detections, spatial exclusion zones, incident dossiers, and sensor fleet metrics across all border sectors. How may I assist your mission?',
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || loading) return;

    const userMsg = { role: 'user' as const, text };
    const history = messages.map((m) => ({ role: m.role, content: m.text }));
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await aiApi.chat(text, history);
      setMessages((prev) => [...prev, { role: 'assistant', text: res.response }]);
    } catch (e) {
      console.error('AI chat failed:', e);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: 'Error connecting to Gemini Intelligence API. Please verify network connectivity.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const promptSuggestions = [
    'Analyze Sector 07 breach pattern and assess repeat incursion risk.',
    'List all active alerts and recommend quick containment actions.',
    'Summarize current CCTV camera health and detection rates across all sectors.',
    'Verify if virtual tripwires at Northern Buffer have had line-crossing triggers today.',
  ];

  return (
    <div className="w-full space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[#E5E1EE]">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center space-x-3">
            <span>Sentinel Intelligence AI Analyst</span>
            <span className="text-xs px-3 py-1 rounded-full bg-[#F0EDFD] border border-[#DCD4FB] text-[#7C5CFC] font-bold">
              Gemini 2.5 Flash
            </span>
          </h1>
          <p className="text-sm text-[#625D6D] mt-1 font-medium">
            Natural language perimeter intelligence query, pattern correlation, and containment strategy reasoning
          </p>
        </div>
      </div>

      {/* Main Chat Workspace */}
      <div className="rounded-xl bg-white border border-[#E5E1EE] p-5 sm:p-6 space-y-4 shadow-xs flex flex-col h-[650px] justify-between">
        {/* Messages Feed */}
        <div className="space-y-4 overflow-y-auto pr-2 flex-1">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex items-start space-x-3 ${
                m.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {m.role === 'assistant' && (
                <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] shrink-0">
                  <Bot className="w-5 h-5" />
                </div>
              )}
              <div
                className={`max-w-2xl p-4 rounded-xl text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-[#7C5CFC] text-white font-medium rounded-tr-xs'
                    : 'bg-[#FAF9FD] border border-[#E5E1EE] text-[#211D2B] font-normal rounded-tl-xs shadow-2xs'
                }`}
              >
                {m.text}
              </div>
              {m.role === 'user' && (
                <div className="w-9 h-9 rounded-lg bg-[#FAF9FD] border border-[#E5E1EE] flex items-center justify-center text-[#625D6D] shrink-0">
                  <UserIcon className="w-5 h-5" />
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="p-4 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] text-sm text-[#7C5CFC] font-semibold animate-pulse">
                Analyzing border surveillance telemetry and generating response...
              </div>
            </div>
          )}
        </div>

        {/* Prompt Suggestions */}
        <div className="pt-2 border-t border-[#E5E1EE] space-y-2">
          <div className="flex items-center space-x-1.5 text-xs text-[#8E8899] font-bold uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-[#7C5CFC]" />
            <span>Suggested Surveillance Prompts:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {promptSuggestions.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(s)}
                className="px-3 py-1.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] hover:border-[#DCD4FB] text-xs font-semibold text-[#4328A8] text-left transition"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Input Bar */}
        <div className="flex items-center space-x-3 pt-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about border cameras, incidents, threat heatmaps, or patrol recommendations..."
            className="flex-1 px-4 py-3 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC] font-sans shadow-2xs"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !inputText.trim()}
            className="px-6 py-3 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center space-x-2 transition disabled:opacity-50 shadow-xs"
          >
            <Send className="w-4 h-4" />
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
}
