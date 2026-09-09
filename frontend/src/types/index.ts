export interface Citation {
  citation_number?: number;
  citation_id?: number;
  source_id?: string;
  doc_id?: string;
  source_title?: string;
  title?: string;
  source_url?: string;
  authoritative_org?: string;
  verbatim_quote?: string;
  snippet?: string;
  is_valid?: boolean;
}

export interface AgentThoughtStep {
  agent_name: string;
  step_type: string;
  description: string;
  duration_ms?: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  category?: string;
  safe_refusal?: boolean;
  is_grounded?: boolean;
  citations?: Citation[];
  thought_steps?: AgentThoughtStep[];
  latency_ms?: number;
  timestamp: string;
}

export interface TelemetryStats {
  total_queries: number;
  avg_latency_ms: number;
  total_cost_usd: number;
  safe_refusal_rate: number;
  total_tokens: number;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  preview?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  category?: string;
  cached_messages?: ChatMessage[];
}
