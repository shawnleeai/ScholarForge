export interface AgentSession {
  id: string;
  title: string;
  task_type: string;
  status: string;
  message_count?: number;
  created_at: string;
  updated_at?: string;
}

export interface AgentMessage {
  id: string;
  role: string;
  content: string;
  created_at: string;
  metadata?: {
    tool_type?: string;
    [key: string]: any;
  };
}

export interface ResearchPlan {
  id: string;
  title: string;
  objectives: string[];
  milestones: PlanMilestone[];
  tasks: PlanTask[];
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at?: string;
}

export interface PlanMilestone {
  id: string;
  title: string;
  order: number;
  due_date?: string;
  status?: string;
  completed_at?: string;
}

export interface PlanTask {
  id: string;
  title: string;
  status: 'todo' | 'in_progress' | 'completed';
  completed_at?: string;
}

export interface AgentSuggestion {
  id: string;
  title: string;
  description: string;
  action_type: string;
  is_accepted?: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface TaskTypeInfo {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

export const TASK_TYPES: TaskTypeInfo[] = [
  { id: 'research', name: '文献调研', description: '帮助搜索和分析学术文献' },
  { id: 'writing', name: '写作辅助', description: '协助撰写和润色论文' },
  { id: 'analysis', name: '数据分析', description: '分析实验数据并提供建议' },
  { id: 'coding', name: '代码辅助', description: '编写和调试研究代码' },
  { id: 'planning', name: '研究规划', description: '制定研究计划和时间安排' },
  { id: 'review', name: '论文审阅', description: '审阅论文并提供改进建议' },
  { id: 'brainstorming', name: '头脑风暴', description: '激发研究灵感和创意' },
];
