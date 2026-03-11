import api from './api';

export interface CreateSessionRequest {
  title: string;
  task_type: string;
  context?: Record<string, any>;
}

export interface CreateSessionResponse {
  message: string;
  session: {
    id: string;
    title: string;
    task_type: string;
    status: string;
    created_at: string;
  };
}

export interface ListSessionsResponse {
  sessions: Array<{
    id: string;
    title: string;
    task_type: string;
    status: string;
    message_count: number;
    updated_at: string;
  }>;
}

export interface GetSessionResponse {
  id: string;
  title: string;
  task_type: string;
  status: string;
  context: Record<string, any>;
  messages: Array<{
    id: string;
    role: string;
    content: string;
    created_at: string;
    metadata?: Record<string, any>;
  }>;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  stream?: boolean;
}

export interface ChatChunk {
  type: 'chunk' | 'complete' | 'error';
  content?: string;
  error?: string;
}

export interface CreatePlanRequest {
  title: string;
  objectives: string[];
  start_date?: string;
  end_date?: string;
}

export interface CreatePlanResponse {
  message: string;
  plan: {
    id: string;
    title: string;
    objectives: string[];
    milestones: Array<{
      id: string;
      title: string;
      order: number;
      due_date?: string;
    }>;
    tasks: Array<{
      id: string;
      title: string;
      status: string;
    }>;
    created_at: string;
  };
}

export interface GetSuggestionsResponse {
  suggestions: Array<{
    id: string;
    title: string;
    description: string;
    action_type: string;
    is_accepted?: boolean;
    is_dismissed: boolean;
    created_at: string;
  }>;
}

export interface GetCapabilitiesResponse {
  task_types: Array<{
    id: string;
    name: string;
    description: string;
  }>;
  features: string[];
  supported_tools: string[];
}

class AIAgentService {
  private baseUrl = '/ai-agent';

  // 会话管理
  async createSession(data: CreateSessionRequest): Promise<CreateSessionResponse> {
    const response = await api.post(`${this.baseUrl}/sessions`, data);
    return response.data;
  }

  async listSessions(taskType?: string): Promise<ListSessionsResponse> {
    const params = taskType ? { task_type: taskType } : {};
    const response = await api.get(`${this.baseUrl}/sessions`, { params });
    return response.data;
  }

  async getSession(sessionId: string): Promise<GetSessionResponse> {
    const response = await api.get(`${this.baseUrl}/sessions/${sessionId}`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`${this.baseUrl}/sessions/${sessionId}`);
  }

  // 对话
  async chat(
    sessionId: string,
    data: ChatRequest,
    onChunk?: (chunk: ChatChunk) => void
  ): Promise<void> {
    if (data.stream) {
      // 流式响应
      const response = await fetch(
        `${api.defaults.baseURL}${this.baseUrl}/sessions/${sessionId}/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...api.defaults.headers.common,
          },
          body: JSON.stringify(data),
        }
      );

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (dataStr === '[DONE]') {
              return;
            }
            try {
              const chunk: ChatChunk = JSON.parse(dataStr);
              onChunk?.(chunk);
            } catch (e) {
              console.error('Failed to parse chunk:', e);
            }
          }
        }
      }
    } else {
      // 非流式响应
      const response = await api.post(
        `${this.baseUrl}/sessions/${sessionId}/chat/sync`,
        data
      );
      onChunk?.({
        type: 'complete',
        content: response.data.response
      });
    }
  }

  // 研究计划
  async createPlan(data: CreatePlanRequest): Promise<CreatePlanResponse> {
    const response = await api.post(`${this.baseUrl}/plans`, data);
    return response.data;
  }

  async listPlans(): Promise<{ plans: CreatePlanResponse['plan'][] }> {
    const response = await api.get(`${this.baseUrl}/plans`);
    return response.data;
  }

  async getPlan(planId: string): Promise<CreatePlanResponse['plan']> {
    const response = await api.get(`${this.baseUrl}/plans/${planId}`);
    return response.data;
  }

  async updatePlanProgress(
    planId: string,
    data: { milestone_id?: string; task_id?: string; status: string }
  ): Promise<void> {
    await api.post(`${this.baseUrl}/plans/${planId}/progress`, data);
  }

  // 主动建议
  async getSuggestions(includeDismissed?: boolean): Promise<GetSuggestionsResponse> {
    const params = includeDismissed ? { include_dismissed: true } : {};
    const response = await api.get(`${this.baseUrl}/suggestions`, { params });
    return response.data;
  }

  async acceptSuggestion(suggestionId: string): Promise<void> {
    await api.post(`${this.baseUrl}/suggestions/${suggestionId}/accept`);
  }

  async dismissSuggestion(suggestionId: string): Promise<void> {
    await api.post(`${this.baseUrl}/suggestions/${suggestionId}/dismiss`);
  }

  // 快捷入口
  async quickResearch(topic: string): Promise<{
    message: string;
    session_id: string;
    plan_id: string;
    suggested_actions: string[];
  }> {
    const response = await api.post(
      `${this.baseUrl}/quick/research?topic=${encodeURIComponent(topic)}`
    );
    return response.data;
  }

  async quickWriting(
    title: string,
    section?: string
  ): Promise<{
    message: string;
    session_id: string;
    suggested_outline: string[];
  }> {
    const response = await api.post(
      `${this.baseUrl}/quick/writing?title=${encodeURIComponent(title)}&section=${section}`
    );
    return response.data;
  }

  // 能力列表
  async getCapabilities(): Promise<GetCapabilitiesResponse> {
    const response = await api.get(`${this.baseUrl}/capabilities`);
    return response.data;
  }
}

export const aiAgentService = new AIAgentService();
export default aiAgentService;
