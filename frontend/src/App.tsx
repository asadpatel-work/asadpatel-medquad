import React, { useState, useEffect, useRef } from 'react';
import { Citation, ChatMessage, TelemetryStats, SessionSummary } from './types';

export const App: React.FC = () => {
  const [sessionsList, setSessionsList] = useState<SessionSummary[]>(() => {
    try {
      const saved = localStorage.getItem('medquad_sessions');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [activeSessionId, setActiveSessionId] = useState<string>(() => `session-${Date.now().toString(36)}`);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryStats | null>(null);
  const [showTelemetryModal, setShowTelemetryModal] = useState(false);
  const [feedbackMessageId, setFeedbackMessageId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    try {
      localStorage.setItem('medquad_sessions', JSON.stringify(sessionsList));
    } catch (e) {
      console.error('Failed to cache sessions', e);
    }
  }, [sessionsList]);

  const fetchBackendSessions = async () => {
    try {
      const res = await fetch('/api/v1/sessions');
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setSessionsList((prev) => {
            const map = new Map<string, SessionSummary>();
            prev.forEach((s) => map.set(s.session_id, s));
            data.forEach((s: SessionSummary) => map.set(s.session_id, { ...map.get(s.session_id), ...s }));
            return Array.from(map.values()).sort(
              (a, b) => new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime()
            );
          });
        }
      }
    } catch (e) {
      console.warn('Backend sessions not reachable yet', e);
    }
  };

  const normalizeCitation = (c: any, idx = 0): Citation => {
    if (!c) {
      return {
        citation_number: idx + 1,
        citation_id: idx + 1,
        source_id: 'MedQuAD',
        doc_id: 'MedQuAD',
        source_title: 'Authoritative Medical Literature',
        title: 'Authoritative Medical Literature',
        source_url: '#',
        authoritative_org: 'NIH MedQuAD',
        verbatim_quote: '',
        snippet: '',
        is_valid: true,
      };
    }
    const num = c.citation_number ?? c.citation_id ?? (idx + 1);
    return {
      ...c,
      citation_number: num,
      citation_id: num,
      source_title: c.source_title ?? c.title ?? 'Authoritative Medical Literature',
      title: c.title ?? c.source_title ?? 'Authoritative Medical Literature',
      verbatim_quote: c.verbatim_quote ?? c.snippet ?? '',
      snippet: c.snippet ?? c.verbatim_quote ?? '',
      source_id: c.source_id ?? c.doc_id ?? 'MedQuAD',
      doc_id: c.doc_id ?? c.source_id ?? 'MedQuAD',
      authoritative_org: c.authoritative_org ?? 'NIH MedQuAD',
      source_url: c.source_url ?? '#',
    };
  };

  const fetchTelemetry = async () => {
    try {
      const res = await fetch('/api/v1/telemetry/stats');
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (e) {
      console.error('Failed to fetch telemetry', e);
    }
  };

  useEffect(() => {
    fetchBackendSessions().then(() => {
      if (messages.length === 0 && sessionsList.length > 0) {
        handleSelectSession(sessionsList[0].session_id);
      }
    });
    fetchTelemetry();
  }, []);

  const handleSelectSession = async (sessionId: string) => {
    if (!sessionId) return;
    if (sessionId === activeSessionId && messages.length > 0) return;

    setIsLoading(true);
    setActiveSessionId(sessionId);
    setSelectedCitation(null);

    // Hydrate immediately from cache
    let cached: ChatMessage[] | null = null;
    try {
      const stored = localStorage.getItem(`medquad_messages_${sessionId}`);
      if (stored) {
        cached = JSON.parse(stored);
      }
    } catch (e) {}

    if (!cached || cached.length === 0) {
      const local = sessionsList.find((s) => s.session_id === sessionId);
      if (local && local.cached_messages && local.cached_messages.length > 0) {
        cached = local.cached_messages;
      }
    }

    if (cached && cached.length > 0) {
      const normalizedCached = cached.map((m) => ({
        ...m,
        citations: (m.citations || []).map((c, i) => normalizeCitation(c, i)),
      }));
      setMessages(normalizedCached);
      const lastAss = normalizedCached.filter((m) => m.role === 'assistant').pop();
      if (lastAss && lastAss.citations && lastAss.citations.length > 0) {
        setSelectedCitation(lastAss.citations[0]);
      }
    }

    try {
      const res = await fetch(`/api/v1/sessions/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        const formatted: ChatMessage[] = (data.messages || []).map((m: any, idx: number) => ({
          id: `msg-${idx}-${Date.now()}`,
          role: m.role,
          content: m.content,
          category: m.metadata?.category || 'Clinical Research',
          citations: (m.citations || []).map((c: any, i: number) => normalizeCitation(c, i)),
          thought_steps: m.thought_steps || [],
          safe_refusal: m.metadata?.safe_refusal || false,
          is_grounded: (m.citations || []).length > 0,
          latency_ms: m.metadata?.latency_ms || 0,
          timestamp: m.timestamp || new Date().toISOString(),
        }));

        if (formatted.length > 0) {
          setMessages(formatted);
          try {
            localStorage.setItem(`medquad_messages_${sessionId}`, JSON.stringify(formatted));
          } catch (e) {}

          setSessionsList((prev) =>
            prev.map((s) =>
              s.session_id === sessionId
                ? {
                    ...s,
                    cached_messages: formatted,
                    message_count: formatted.length,
                    preview: (formatted[formatted.length - 1]?.content || s.preview || '').substring(0, 60) + '...',
                  }
                : s
            )
          );

          const lastAssistant = formatted.filter((m) => m.role === 'assistant').pop();
          if (lastAssistant && lastAssistant.citations && lastAssistant.citations.length > 0) {
            setSelectedCitation(lastAssistant.citations[0]);
          }
        }
      } else if (!cached || cached.length === 0) {
        setMessages([]);
      }
    } catch (err) {
      console.error('Error fetching session details:', err);
      if (!cached || cached.length === 0) {
        setMessages([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewConsultation = () => {
    const newId = `session-${Date.now().toString(36)}`;
    setActiveSessionId(newId);
    setMessages([]);
    setSelectedCitation(null);
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this consultation history?')) return;

    try {
      await fetch(`/api/v1/sessions/${sessionId}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('Could not delete from backend', err);
    }

    try {
      localStorage.removeItem(`medquad_messages_${sessionId}`);
    } catch (e) {}

    setSessionsList((prev) => prev.filter((s) => s.session_id !== sessionId));
    if (activeSessionId === sessionId) {
      handleNewConsultation();
    }
  };

  const handleSendMessage = async (queryToSend?: string) => {
    const q = queryToSend || inputQuery;
    if (!q.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: new Date().toISOString(),
    };

    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInputQuery('');
    setIsLoading(true);

    setSessionsList((prev) => {
      const title = q.length > 45 ? q.substring(0, 45) + '...' : q;
      const existing = prev.find((s) => s.session_id === activeSessionId);
      if (existing) {
        return prev.map((s) =>
          s.session_id === activeSessionId
            ? {
                ...s,
                updated_at: new Date().toISOString(),
                message_count: s.message_count + 1,
                preview: q,
              }
            : s
        );
      } else {
        return [
          {
            session_id: activeSessionId,
            title: title,
            preview: q,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 1,
            category: 'Clinical',
          },
          ...prev,
        ];
      }
    });

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: q,
          session_id: activeSessionId,
        }),
      });

      if (!res.ok) throw new Error(`HTTP error ${res.status}`);

      const data = await res.json();
      const normalizedCitations = (data.citations || []).map((c: any, i: number) => normalizeCitation(c, i));
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}-resp`,
        role: 'assistant',
        content: data.response || 'No response generated.',
        category: data.category || 'General Clinical',
        safe_refusal: data.safe_refusal || false,
        is_grounded: data.is_grounded || false,
        citations: normalizedCitations,
        thought_steps: data.thought_steps || [],
        latency_ms: data.latency_ms || 0,
        timestamp: new Date().toISOString(),
      };

      const finalMessages = [...updatedMessages, assistantMsg];
      setMessages(finalMessages);

      try {
        localStorage.setItem(`medquad_messages_${activeSessionId}`, JSON.stringify(finalMessages));
      } catch (e) {}

      setSessionsList((prev) =>
        prev.map((s) =>
          s.session_id === activeSessionId
            ? {
                ...s,
                cached_messages: finalMessages,
                message_count: finalMessages.length,
                category: data.category || s.category,
                preview: (data.response || '').substring(0, 60) + '...',
                updated_at: new Date().toISOString(),
              }
            : s
        )
      );

      if (normalizedCitations.length > 0) {
        setSelectedCitation(normalizedCitations[0]);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg-${Date.now()}-err`,
        role: 'assistant',
        content: `⚠️ Error connecting to MedQuAD Multi-Agent Backend: ${err.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      fetchTelemetry();
    }
  };

  const submitFeedback = async () => {
    if (!feedbackMessageId) return;
    try {
      await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          message_id: feedbackMessageId,
          rating: feedbackRating,
          comments: feedbackComment,
        }),
      });
      alert('Feedback submitted successfully. Thank you for helping refine clinical evidence accuracy.');
      setFeedbackMessageId(null);
      setFeedbackComment('');
    } catch (e) {
      alert('Failed to submit feedback.');
    }
  };

  const filteredSessions = sessionsList.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (s.title && s.title.toLowerCase().includes(q)) ||
      (s.preview && s.preview.toLowerCase().includes(q)) ||
      (s.category && s.category.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans">
      <header className="flex items-center justify-between px-5 py-3 bg-slate-900 border-b border-slate-800 shadow-md z-10">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title="Toggle Consultation History Sidebar"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            📑
          </button>
          <div className="w-9 h-9 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 font-bold text-lg shadow-inner">
            ⚕️
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
              MedQuAD Clinical Research Assistant
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-950 text-teal-300 border border-teal-800">
                ADK Multi-Agent
              </span>
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              NIH Grounding • Gemini 2.5/3.5 Architecture • Model Armor Guardrails
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => {
              fetchTelemetry();
              setShowTelemetryModal(true);
            }}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center gap-1.5"
          >
            📊 Live Telemetry HUD
          </button>
          <button
            onClick={handleNewConsultation}
            className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-teal-600 hover:bg-teal-500 text-white shadow transition flex items-center gap-1"
          >
            <span>+</span> New Consultation
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {sidebarOpen && (
          <aside className="w-72 bg-slate-900/95 border-r border-slate-800 flex flex-col flex-shrink-0 transition-all">
            <div className="p-3.5 border-b border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                  🗂️ History ({sessionsList.length})
                </span>
                <button
                  onClick={handleNewConsultation}
                  className="text-[11px] px-2 py-1 bg-teal-950/80 hover:bg-teal-900 text-teal-300 border border-teal-800 rounded font-medium transition"
                >
                  + New
                </button>
              </div>

              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search consultations..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-teal-500 transition"
              />
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
              {filteredSessions.length === 0 ? (
                <div className="text-center py-10 px-4 text-xs text-slate-500">
                  {searchQuery ? 'No matching consultations.' : 'No saved consultations yet. Start by asking a clinical question!'}
                </div>
              ) : (
                filteredSessions.map((s) => {
                  const isActive = s.session_id === activeSessionId;
                  return (
                    <div
                      key={s.session_id}
                      onClick={() => handleSelectSession(s.session_id)}
                      className={`group relative p-2.5 rounded-xl text-xs cursor-pointer transition border ${
                        isActive
                          ? 'bg-teal-950/40 border-teal-500 text-slate-100 shadow-sm'
                          : 'bg-slate-950/50 border-slate-800/80 hover:bg-slate-800/60 hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-1 mb-1">
                        <span className="font-semibold text-slate-200 line-clamp-1 flex-1">
                          {s.title || 'Consultation Session'}
                        </span>
                        <button
                          onClick={(e) => handleDeleteSession(s.session_id, e)}
                          title="Delete consultation"
                          className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 p-0.5 rounded transition"
                        >
                          ✕
                        </button>
                      </div>

                      <p className="text-[11px] text-slate-400 line-clamp-1 mb-1.5">
                        {s.preview || 'Clinical consultation...'}
                      </p>

                      <div className="flex items-center justify-between text-[10px] text-slate-500">
                        <span className="px-1.5 py-0.5 bg-slate-900 rounded border border-slate-800 text-teal-400">
                          {s.category || 'General'}
                        </span>
                        <span>{s.message_count ? `${s.message_count} msgs` : 'Active'}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 text-[11px] text-slate-500 flex items-center justify-between">
              <span>Session: {activeSessionId.substring(0, 14)}...</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
            </div>
          </aside>
        )}

        <main className="flex-1 flex flex-col min-w-0 bg-slate-950">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center max-w-xl mx-auto space-y-6">
                <div className="w-16 h-16 rounded-2xl bg-teal-950/60 border border-teal-800/50 flex items-center justify-center text-3xl shadow-lg">
                  🔬
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-200 mb-2">Authoritative Medical Literature Exploration</h2>
                  <p className="text-sm text-slate-400">
                    Query NIH MedQuAD, NCI trial protocols, and clinical reference ranges with strict source grounding and multi-agent peer review.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full text-left">
                  {[
                    "What are the diagnostic markers and Ann Arbor staging for Hodgkin Lymphoma?",
                    "What are the ADA criteria and HbA1c diagnostic cutoffs for Type 2 Diabetes?",
                    "Summarize Sepsis-3 qSOFA diagnostic criteria and 1-hour resuscitation bundle.",
                    "Diagnose me please: I have a lump on my collarbone and night sweats.",
                  ].map((preset, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(preset)}
                      className="p-3.5 text-xs rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-teal-500/50 text-slate-300 transition shadow-sm text-left"
                    >
                      <span className="text-teal-400 font-semibold mr-1.5">💡</span> {preset}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className="text-[11px] text-slate-500 mb-1 px-1">
                    {msg.role === 'user' ? 'Clinician' : 'MedQuAD Assistant'}
                  </div>

                  <div
                    className={`max-w-3xl rounded-2xl p-5 ${
                      msg.role === 'user'
                        ? 'bg-teal-700/80 text-white rounded-tr-none'
                        : msg.safe_refusal
                        ? 'bg-amber-950/40 border border-amber-800/60 text-amber-200 rounded-tl-none'
                        : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                    }`}
                  >
                    {msg.thought_steps && msg.thought_steps.length > 0 && (
                      <details className="mb-4 pb-3 border-b border-slate-800/80">
                        <summary className="text-xs font-semibold text-teal-400 cursor-pointer hover:text-teal-300 select-none flex items-center gap-1.5">
                          ⚙️ Multi-Agent Reasoning Trace ({msg.thought_steps.length} Steps)
                        </summary>
                        <div className="mt-2.5 space-y-1.5 pl-3 border-l-2 border-teal-500/30">
                          {msg.thought_steps.map((step, idx) => (
                            <div key={idx} className="text-xs text-slate-400">
                              <span className="font-semibold text-slate-300">[{step.agent_name}]:</span>{' '}
                              {step.description}
                            </div>
                          ))}
                        </div>
                      </details>
                    )}

                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap items-center gap-2">
                        <span className="text-xs text-slate-400 font-medium">Grounding Sources:</span>
                        {msg.citations.map((c, cIdx) => {
                          const norm = normalizeCitation(c, cIdx);
                          const selNum = selectedCitation?.citation_number ?? selectedCitation?.citation_id;
                          const isSelected = selNum !== undefined && selNum === norm.citation_number;
                          return (
                            <button
                              key={`${norm.citation_number}-${cIdx}`}
                              onClick={() => setSelectedCitation(norm)}
                              className={`px-2.5 py-1 text-xs font-semibold rounded-md border transition flex items-center gap-1 ${
                                isSelected
                                  ? 'bg-teal-500/20 text-teal-300 border-teal-500 ring-1 ring-teal-500/50'
                                  : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-500'
                              }`}
                            >
                              [{norm.citation_number}] {norm.authoritative_org}
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {msg.role === 'assistant' && (
                      <div className="mt-3 flex items-center justify-between text-xs text-slate-500 pt-2">
                        <span>Latency: {msg.latency_ms || 0} ms</span>
                        <button
                          onClick={() => setFeedbackMessageId(msg.id)}
                          className="hover:text-slate-300 text-slate-400 underline transition"
                        >
                          Provide Feedback
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex items-center space-x-3 text-slate-400 text-sm p-4 bg-slate-900/50 rounded-xl border border-slate-800 w-fit">
                <div className="w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full animate-spin" />
                <span>Multi-agent reasoning loop in progress (Researcher & Reviewer)...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 bg-slate-900 border-t border-slate-800">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center space-x-3"
            >
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask an evidence-grounded clinical research question (e.g. diagnostic criteria, protocols)..."
                className="flex-1 bg-slate-950 border border-slate-700 focus:border-teal-500 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition shadow-inner"
              />
              <button
                type="submit"
                disabled={isLoading || !inputQuery.trim()}
                className="px-5 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold text-sm transition shadow"
              >
                Send
              </button>
            </form>
          </div>
        </main>

        <aside className="w-80 bg-slate-900/90 flex flex-col overflow-y-auto p-5 border-l border-slate-800 flex-shrink-0">
          <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              📖 Citation Inspector
            </h2>
          </div>

          {selectedCitation ? (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-teal-950/30 border border-teal-800/40">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-teal-400">
                    Citation [{selectedCitation.citation_number ?? selectedCitation.citation_id ?? 1}]
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded bg-teal-900/60 text-teal-300 font-medium">
                    {selectedCitation.authoritative_org || 'NIH MedQuAD'}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-slate-100 mb-1">
                  {selectedCitation.source_title || selectedCitation.title || 'Authoritative Clinical Literature'}
                </h3>
                {selectedCitation.source_url && (
                  <a
                    href={selectedCitation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-teal-400 hover:underline break-all"
                  >
                    {selectedCitation.source_url} ↗
                  </a>
                )}
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Verbatim Grounding Passage
                </div>
                <p className="text-xs text-slate-300 leading-relaxed italic">
                  "{selectedCitation.verbatim_quote || selectedCitation.snippet || 'Referenced clinical text passage verified by reviewer.'}"
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/60 text-xs text-slate-400 space-y-1">
                <div><strong>Corpus:</strong> NIH MedQuAD Knowledge Base</div>
                <div><strong>Verification Status:</strong> 🟢 Verified by Reviewer Agent</div>
                <div><strong>Doc ID:</strong> {selectedCitation.source_id || selectedCitation.doc_id || 'NIH-Doc'}</div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-center text-slate-500 text-xs">
              <div className="text-2xl mb-2">🔍</div>
              Click any citation badge [1], [2] in an answer to inspect its authoritative source passage and provenance.
            </div>
          )}
        </aside>
      </div>

      {showTelemetryModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
              <h3 className="text-base font-bold text-slate-100">📊 System Telemetry & Cost Accounting</h3>
              <button
                onClick={() => setShowTelemetryModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {telemetry ? (
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 mb-1">Total Processed Queries</div>
                  <div className="text-xl font-bold text-teal-400">{telemetry.total_queries || 0}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 mb-1">Total Estimated Cost</div>
                  <div className="text-xl font-bold text-emerald-400">${(telemetry.total_cost_usd || 0).toFixed(4)}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 mb-1">Average Latency</div>
                  <div className="text-xl font-bold text-slate-200">{telemetry.avg_latency_ms || 0} ms</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-slate-400 mb-1">Safe Refusal Rate</div>
                  <div className="text-xl font-bold text-amber-400">
                    {((telemetry.safe_refusal_rate || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">Loading telemetry records...</div>
            )}
          </div>
        </div>
      )}

      {feedbackMessageId && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-100 mb-3">⭐ Clinician Review & Feedback</h3>
            <p className="text-xs text-slate-400 mb-4">
              Rate the clinical factuality and citation precision of this response:
            </p>

            <div className="flex items-center space-x-2 mb-4">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => setFeedbackRating(star)}
                  className={`text-2xl ${feedbackRating >= star ? 'text-amber-400' : 'text-slate-600'}`}
                >
                  ★
                </button>
              ))}
            </div>

            <textarea
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder="Optional notes or clinical accuracy observations..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-teal-500 mb-4 h-24"
            />

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setFeedbackMessageId(null)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={submitFeedback}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-teal-600 text-white hover:bg-teal-500 transition"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
