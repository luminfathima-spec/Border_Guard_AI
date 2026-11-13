import { useState, useEffect, useRef } from 'react';
import {
  Bot, Send, AlertTriangle, RefreshCw,
  Terminal, ShieldCheck
} from 'lucide-react';
import { copilotApi, cameraApi, incidentApi } from '../services/sentinelApi';
import { useAuth } from '../contexts/AuthContext';
import type {
  CopilotChatResponse, CopilotToolCall, CopilotPendingConfirmation,
  Camera, Incident
} from '../types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolCalls?: CopilotToolCall[];
  pendingConfirmation?: CopilotPendingConfirmation;
  suggestedQueries?: string[];
  modelUsed?: string;
}

export function CopilotPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<number | undefined>();
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | undefined>();
  const [confirmationModal, setConfirmationModal] = useState<CopilotPendingConfirmation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // Initial welcome message
    const welcomeMsg: ChatMessage = {
      id: 'welcome-1',
      role: 'assistant',
      content: `### Welcome to Surveillance Copilot
I am your authorized AI border operations analyst powered by **Gemini 2.5 Flash** and deterministic verification tools.

I can assist you with:
- **Camera Telemetry:** Summarizing recent events and detection density across specific sensors.
- **Unresolved Evidence:** Highlighting incidents with missing observation links or sensor conflicts.
- **Zone Spatial Queries:** Locating events in specific zones across customizable time windows.
- **Report Provenance:** Explaining the exact database evidence and citations supporting stored dossiers.
- **Provenance Graph Synthesis:** Summarizing multi-sensor linked observations and conflict ledgers.
- **Tactical Escalation:** Escalating critical perimeter breaches with two-step operator confirmation.

Click any prompt chip below or type your inquiry in natural language.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestedQueries: [
        'Summarize recorded events from camera 1',
        'Show incidents with unresolved evidence',
        'Find events associated with Sector 4 in the last 24 hours',
        'Explain which evidence supports Report #1',
        'Summarize what happened across linked observations in Incident #1',
      ],
    };
    setMessages([welcomeMsg]);

    // Load available cameras and incidents for contextual filtering
    const loadContext = async () => {
      try {
        const [cams, incs] = await Promise.all([cameraApi.list(), incidentApi.list()]);
        setCameras(cams);
        setIncidents(incs);
        if (cams.length > 0) setSelectedCameraId(cams[0].id);
        if (incs.length > 0) setSelectedIncidentId(incs[0].id);
      } catch (err) {
        console.error('Failed to load contextual data for Copilot:', err);
      }
    };
    loadContext();
  }, []);

  const handleSendMessage = async (textToSend?: string, confirmedAction?: CopilotPendingConfirmation) => {
    const query = (textToSend || inputValue).trim();
    if (!query && !confirmedAction) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: confirmedAction ? `[CONFIRMED ACTION] ${confirmedAction.prompt}` : query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend && !confirmedAction) setInputValue('');
    setLoading(true);

    try {
      // Build conversation history format
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res: CopilotChatResponse = await copilotApi.chat({
        message: query || (confirmedAction ? `Execute ${confirmedAction.action_type}` : ''),
        conversation_history: history,
        camera_id: selectedCameraId,
        incident_id: selectedIncidentId,
        confirmed_action: confirmedAction,
      });

      const assistantMsg: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        toolCalls: res.tool_calls,
        pendingConfirmation: res.pending_confirmation,
        suggestedQueries: res.suggested_queries,
        modelUsed: res.model_used,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // If response requires confirmation, show confirmation dialog
      if (res.pending_confirmation) {
        setConfirmationModal(res.pending_confirmation);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `**Copilot Service Error**: ${err?.response?.data?.detail || err.message || 'Failed to communicate with AI Copilot backend.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAction = async (pending: CopilotPendingConfirmation) => {
    setConfirmationModal(null);
    await handleSendMessage(undefined, pending);
  };

  return (
    <div className="w-full flex flex-col h-[calc(100vh-140px)] min-h-[600px] space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E5E1EE] shrink-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#211D2B] tracking-tight flex items-center gap-2.5">
            <Bot className="w-7 h-7 text-[#7C5CFC]" />
            Surveillance Copilot
          </h1>
          <p className="text-xs sm:text-sm text-[#625D6D] mt-1 font-medium">
            Natural-language surveillance assistant with authorized tool execution, evidence verification, and two-step action confirmation
          </p>
        </div>

        {/* User Role & Authorization Indicator */}
        <div className="flex items-center gap-2.5 shrink-0 bg-white p-2 rounded-xl border border-[#E5E1EE] shadow-2xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#F0EDFD] text-[#4328A8] text-xs font-bold">
            <ShieldCheck className="w-4 h-4 text-[#7C5CFC]" />
            <span>Role: {user?.role || 'OPERATOR'}</span>
          </div>
          {user?.role === 'VIEWER' ? (
            <span className="text-[11px] font-semibold text-[#DC2626] bg-[#FEE2E2] px-2 py-0.5 rounded-md">
              Read-Only
            </span>
          ) : (
            <span className="text-[11px] font-semibold text-[#16A34A] bg-[#DCFCE7] px-2 py-0.5 rounded-md">
              Action Authorized
            </span>
          )}
        </div>
      </div>

      {/* Main Chat Workstation */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl border border-[#E5E1EE] shadow-2xs overflow-hidden">
        {/* Context Controls */}
        <div className="px-5 py-2.5 bg-[#FAF9FD] border-b border-[#E5E1EE] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[#625D6D]">Active Camera Context:</span>
              <select
                value={selectedCameraId || ''}
                onChange={(e) => setSelectedCameraId(Number(e.target.value))}
                className="px-2 py-1 rounded-md border border-[#E5E1EE] bg-white text-[#211D2B] font-medium"
              >
                {cameras.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.camera_identifier} — {c.name} ({c.zone})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="font-bold text-[#625D6D]">Active Incident Context:</span>
              <select
                value={selectedIncidentId || ''}
                onChange={(e) => setSelectedIncidentId(Number(e.target.value))}
                className="px-2 py-1 rounded-md border border-[#E5E1EE] bg-white text-[#211D2B] font-medium"
              >
                {incidents.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.incident_number} — {i.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="text-[11px] text-[#8E8899] font-mono flex items-center gap-1">
            <Terminal className="w-3.5 h-3.5 text-[#7C5CFC]" />
            Strict Tool Gating Active (Zero SQL/Shell)
          </div>
        </div>

        {/* Message Log */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-2`}
            >
              {/* Message Bubble */}
              <div
                className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-xs sm:text-sm leading-relaxed shadow-xs ${
                  msg.role === 'user'
                    ? 'bg-[#7C5CFC] text-white rounded-br-xs font-medium'
                    : 'bg-[#FAF9FD] text-[#211D2B] rounded-bl-xs border border-[#E5E1EE]'
                }`}
              >
                {/* Markdown-style rendering for assistant */}
                <div className="space-y-2 whitespace-pre-wrap">
                  {msg.content}
                </div>

                {/* Tool Executions Cards */}
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-[#E5E1EE] space-y-2">
                    <div className="text-[11px] uppercase tracking-wider font-extrabold text-[#7C5CFC] flex items-center gap-1">
                      <Terminal className="w-3.5 h-3.5" />
                      Authorized Tool Invocations ({msg.toolCalls.length})
                    </div>

                    {msg.toolCalls.map((tc, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-white border border-[#E5E1EE] text-xs space-y-1.5 font-mono"
                      >
                        <div className="flex items-center justify-between font-bold text-[#211D2B]">
                          <span className="text-[#4328A8]">tool: {tc.tool_name}()</span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] uppercase ${
                              tc.status === 'SUCCESS'
                                ? 'bg-[#DCFCE7] text-[#166534]'
                                : tc.status === 'CONFIRMATION_REQUIRED'
                                ? 'bg-[#FEF3C7] text-[#B45309]'
                                : 'bg-[#FEE2E2] text-[#B91C1C]'
                            }`}
                          >
                            {tc.status} ({tc.execution_time_ms}ms)
                          </span>
                        </div>
                        <div className="text-[11px] text-[#625D6D] truncate">
                          args: {JSON.stringify(tc.arguments)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Inline Pending Confirmation Prompt */}
                {msg.pendingConfirmation && (
                  <div className="mt-4 p-4 rounded-xl bg-[#FEF3C7] border border-[#FCD34D] text-[#92400E] space-y-2.5">
                    <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wide">
                      <AlertTriangle className="w-4 h-4 text-[#D97706]" />
                      Operator Confirmation Required
                    </div>
                    <p className="text-xs font-medium text-[#78350F]">
                      {msg.pendingConfirmation.prompt}
                    </p>
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => handleConfirmAction(msg.pendingConfirmation!)}
                        className="px-3.5 py-1.5 rounded-lg bg-[#D97706] hover:bg-[#B45309] text-white text-xs font-bold transition shadow-xs"
                      >
                        Confirm & Execute Action
                      </button>
                    </div>
                  </div>
                )}

                {/* Timestamp & Model Metadata */}
                <div
                  className={`flex items-center justify-between mt-2 pt-1 text-[10px] ${
                    msg.role === 'user' ? 'text-white/70' : 'text-[#8E8899]'
                  }`}
                >
                  <span>{msg.timestamp}</span>
                  {msg.modelUsed && (
                    <span className="font-mono">{msg.modelUsed}</span>
                  )}
                </div>
              </div>

              {/* Suggested Follow-up Queries */}
              {msg.suggestedQueries && msg.suggestedQueries.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1 max-w-[85%]">
                  {msg.suggestedQueries.map((sq, sIdx) => (
                    <button
                      key={sIdx}
                      onClick={() => handleSendMessage(sq)}
                      className="px-3 py-1 rounded-full bg-[#F0EDFD] hover:bg-[#E5DFFD] text-[#4328A8] text-xs font-medium border border-[#DCD4FB] transition text-left"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-2 text-xs font-bold text-[#7C5CFC] bg-[#F0EDFD] px-4 py-2.5 rounded-xl w-fit">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Copilot evaluating evidentiary records & tools...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-[#FAF9FD] border-t border-[#E5E1EE] space-y-3 shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              placeholder="Ask Copilot (e.g., 'Summarize recorded events from camera 1' or 'Show incidents with unresolved evidence')..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading}
              className="flex-1 px-4 py-3 text-xs sm:text-sm rounded-xl border border-[#E5E1EE] bg-white text-[#211D2B] placeholder-[#8E8899] focus:border-[#7C5CFC] focus:outline-hidden shadow-2xs"
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="px-5 py-3 rounded-xl bg-[#7C5CFC] hover:bg-[#6846EB] text-white text-xs sm:text-sm font-bold shadow-xs transition disabled:opacity-50 flex items-center gap-1.5 shrink-0"
            >
              <span>Transmit</span>
              <Send className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Archetype Suggestion Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            <span className="text-[#8E8899] font-bold shrink-0">Operator Archetypes:</span>
            <button
              onClick={() => handleSendMessage(`Summarize recorded events from camera ${selectedCameraId || 1}`)}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#4328A8] shrink-0 font-medium transition"
            >
              Camera Summary
            </button>
            <button
              onClick={() => handleSendMessage('Show incidents with unresolved evidence')}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#4328A8] shrink-0 font-medium transition"
            >
              Unresolved Evidence
            </button>
            <button
              onClick={() => handleSendMessage('Find events associated with Sector 4 in the last 24 hours')}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#4328A8] shrink-0 font-medium transition"
            >
              Zone Query
            </button>
            <button
              onClick={() => handleSendMessage('Explain which evidence supports Report #1')}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#4328A8] shrink-0 font-medium transition"
            >
              Report Evidence
            </button>
            <button
              onClick={() => handleSendMessage(`Summarize what happened across linked observations in Incident #${selectedIncidentId || 1}`)}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#F0EDFD] border border-[#E5E1EE] text-[#625D6D] hover:text-[#4328A8] shrink-0 font-medium transition"
            >
              Linked Observations
            </button>
            <button
              onClick={() => handleSendMessage(`Escalate Incident #${selectedIncidentId || 1} to Tactical QRT`)}
              className="px-2.5 py-1 rounded-lg bg-white hover:bg-[#FEE2E2] border border-[#E5E1EE] text-[#DC2626] hover:text-[#B91C1C] shrink-0 font-bold transition"
            >
              Escalate Incident (Consequential)
            </button>
          </div>
        </div>
      </div>

      {/* Two-step Consequential Action Modal */}
      {confirmationModal && (
        <div className="fixed inset-0 z-50 bg-[#211D2B]/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-[#E5E1EE] space-y-4 animate-scale-in">
            <div className="flex items-center space-x-2.5 pb-3 border-b border-[#E5E1EE]">
              <div className="p-2 rounded-xl bg-[#FEF3C7] text-[#D97706]">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-[#211D2B]">Consequential Action Confirmation</h3>
                <span className="text-[11px] font-mono text-[#8E8899]">ID: {confirmationModal.action_id}</span>
              </div>
            </div>

            <div className="space-y-3 text-xs sm:text-sm text-[#211D2B]">
              <p className="font-semibold text-[#78350F] bg-[#FEF3C7] p-3 rounded-xl border border-[#FCD34D]">
                {confirmationModal.prompt}
              </p>
              <div className="space-y-1.5 p-3 rounded-xl bg-[#FAF9FD] border border-[#E5E1EE] text-xs">
                <div className="flex justify-between">
                  <span className="text-[#8E8899]">Action Type:</span>
                  <span className="font-bold text-[#DC2626]">{confirmationModal.action_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8E8899]">Target Entity ID:</span>
                  <span className="font-mono font-bold text-[#211D2B]">#{confirmationModal.target_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8E8899]">Description:</span>
                  <span className="text-[#625D6D]">{confirmationModal.description}</span>
                </div>
              </div>
              <p className="text-[11px] text-[#8E8899]">
                Executing this action modifies critical perimeter threat levels and records an immutable audit log entry.
              </p>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-[#E5E1EE]">
              <button
                onClick={() => setConfirmationModal(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-[#625D6D] hover:bg-[#FAF9FD] transition"
              >
                Cancel
              </button>
              <button
                onClick={() => handleConfirmAction(confirmationModal)}
                className="px-5 py-2.5 rounded-xl bg-[#DC2626] hover:bg-[#B91C1C] text-white text-xs sm:text-sm font-bold shadow-xs transition"
              >
                Confirm & Execute
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
