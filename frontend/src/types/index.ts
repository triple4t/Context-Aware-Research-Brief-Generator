export interface BriefRequest {
  topic: string;
  depth: 'shallow' | 'moderate' | 'deep';
  user_id: string;
  follow_up?: boolean;
  additional_context?: string;
}

export interface BriefResponse {
  brief: {
    executive_summary: string;
    key_insights: string[];
    synthesis: string;
    references: Reference[];
  };
  execution_time: number;
  token_usage?: {
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
  };
  trace_id?: string;
}

export interface Reference {
  title: string;
  url: string;
  relevance_score: number;
  source_type: string;
  publication_date?: string;
  summary: string;
  key_points: string[];
}



export interface UserHistory {
  briefs: Array<{
    id: number;
    topic: string;
    generated_at: string;
    executive_summary: string;
    synthesis: string;
    key_insights: string[];
    references: Reference[];
    context_used?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
  }>;
}

export interface UserStats {
  stats: {
    total_briefs: number;
    average_execution_time: number;
    total_sources: number;
    total_cost_estimate: number;
  };
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  environment: string;
  llm_provider: string;
  storage: string;
  langsmith: {
    enabled: boolean;
    tracing: boolean;
    api_key_configured: boolean;
    project: string;
  };
}

export interface AvailableModels {
  primary_model: {
    name: string;
    provider: string;
  };
  secondary_model: {
    name: string;
    provider: string;
  };
}

export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  current: boolean;
} 