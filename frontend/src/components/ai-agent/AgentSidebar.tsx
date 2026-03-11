import React, { useState, useEffect } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  MoreHorizontal,
  Bot,
  Clock,
  Sparkles,
  ChevronRight,
  BookOpen,
  PenTool,
  BarChart3,
  Code,
  Calendar,
  FileSearch,
  Lightbulb
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { AgentSession, TASK_TYPES } from './types';
import { aiAgentService } from '@/services/aiAgentService';

interface AgentSidebarProps {
  selectedSessionId?: string;
  onSelectSession?: (session: AgentSession) => void;
  onCreateSession?: (session: AgentSession) => void;
  className?: string;
}

const taskTypeIcons: Record<string, React.ReactNode> = {
  research: <BookOpen className="h-4 w-4" />,
  writing: <PenTool className="h-4 w-4" />,
  analysis: <BarChart3 className="h-4 w-4" />,
  coding: <Code className="h-4 w-4" />,
  planning: <Calendar className="h-4 w-4" />,
  review: <FileSearch className="h-4 w-4" />,
  brainstorming: <Lightbulb className="h-4 w-4" />,
};

export const AgentSidebar: React.FC<AgentSidebarProps> = ({
  selectedSessionId,
  onSelectSession,
  onCreateSession,
  className
}) => {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const [selectedTaskType, setSelectedTaskType] = useState('research');

  // 加载会话列表
  const loadSessions = async () => {
    try {
      setIsLoading(true);
      const data = await aiAgentService.listSessions();
      setSessions(data.sessions.map(s => ({
        ...s,
        created_at: (s as any).created_at || new Date().toISOString(),
      })) as AgentSession[]);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  // 创建新会话
  const handleCreateSession = async () => {
    if (!newSessionTitle.trim()) return;

    try {
      const data = await aiAgentService.createSession({
        title: newSessionTitle,
        task_type: selectedTaskType,
        context: {}
      });

      const newSession: AgentSession = {
        id: data.session.id,
        title: data.session.title,
        task_type: data.session.task_type as AgentSession['task_type'],
        status: 'idle',
        message_count: 0,
        created_at: data.session.created_at,
        updated_at: data.session.created_at,
      };
      setSessions(prev => [newSession, ...prev]);
      setShowNewDialog(false);
      setNewSessionTitle('');
      onCreateSession?.(newSession as any);
      onSelectSession?.(newSession as any);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  // 删除会话
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await aiAgentService.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
  };

  // 按日期分组
  const groupedSessions = sessions.reduce((groups, session) => {
    const date = new Date(session.updated_at);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    let group = '更早';
    if (days === 0) group = '今天';
    else if (days === 1) group = '昨天';
    else if (days < 7) group = '本周';
    else if (days < 30) group = '本月';

    if (!groups[group]) groups[group] = [];
    groups[group].push(session);
    return groups;
  }, {} as Record<string, AgentSession[]>);

  const groupOrder = ['今天', '昨天', '本周', '本月', '更早'];

  return (
    <div className={cn("flex flex-col h-full bg-card border-r", className)}>
      {/* 头部 */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-primary/10">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="font-semibold">AI科研助手</h2>
            <p className="text-xs text-muted-foreground">智能Agent系统</p>
          </div>
        </div>

        <Dialog open={showNewDialog} onOpenChange={setShowNewDialog}>
          <DialogTrigger asChild>
            <Button className="w-full" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新会话
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>创建新会话</DialogTitle>
              <DialogDescription>
                选择AI助手类型并开始对话
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">会话名称</label>
                <input
                  type="text"
                  value={newSessionTitle}
                  onChange={(e) => setNewSessionTitle(e.target.value)}
                  placeholder="输入会话名称..."
                  className="w-full px-3 py-2 border rounded-md text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">助手类型</label>
                <div className="grid grid-cols-2 gap-2">
                  {TASK_TYPES.map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setSelectedTaskType(type.id)}
                      className={cn(
                        "flex items-center gap-2 p-3 rounded-md border text-left transition-colors",
                        selectedTaskType === type.id
                          ? "border-primary bg-primary/5"
                          : "hover:bg-muted"
                      )}
                    >
                      <div className={cn(
                        "p-1.5 rounded",
                        selectedTaskType === type.id ? "bg-primary/10 text-primary" : "bg-muted"
                      )}>
                        {taskTypeIcons[type.id]}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{type.name}</p>
                        <p className="text-xs text-muted-foreground line-clamp-1">
                          {type.description}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewDialog(false)}>
                取消
              </Button>
              <Button onClick={handleCreateSession} disabled={!newSessionTitle.trim()}>
                创建
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* 会话列表 */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">
              加载中...
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8">
              <Sparkles className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">还没有会话</p>
              <p className="text-xs text-muted-foreground mt-1">
                点击上方按钮创建新会话
              </p>
            </div>
          ) : (
            groupOrder.map((group) => {
              const groupSessions = groupedSessions[group];
              if (!groupSessions || groupSessions.length === 0) return null;

              return (
                <div key={group} className="mb-4">
                  <h3 className="text-xs font-medium text-muted-foreground px-2 mb-2">
                    {group}
                  </h3>
                  <div className="space-y-1">
                    {groupSessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => onSelectSession?.(session)}
                        className={cn(
                          "w-full flex items-start gap-3 p-2 rounded-md text-left transition-colors group",
                          selectedSessionId === session.id
                            ? "bg-primary/10 text-primary"
                            : "hover:bg-muted"
                        )}
                      >
                        <div className={cn(
                          "p-1.5 rounded mt-0.5",
                          selectedSessionId === session.id
                            ? "bg-primary/20"
                            : "bg-muted group-hover:bg-background"
                        )}>
                          {taskTypeIcons[session.task_type]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={cn(
                            "text-sm font-medium truncate",
                            selectedSessionId === session.id && "text-primary"
                          )}>
                            {session.title}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                            <span>{formatTime(session.updated_at)}</span>
                            <span>•</span>
                            <span>{session.message_count} 条消息</span>
                          </div>
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6 opacity-0 group-hover:opacity-100"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreHorizontal className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={(e) => handleDeleteSession(session.id, e)}
                              className="text-destructive"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              删除
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </ScrollArea>

      {/* 底部信息 */}
      <div className="p-3 border-t">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span>AI Agent V2</span>
          <Separator orientation="vertical" className="h-3" />
          <span>{sessions.length} 个会话</span>
        </div>
      </div>
    </div>
  );
};
