import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  Wrench,
  BookOpen,
  PenTool,
  BarChart3,
  Code,
  Calendar,
  FileSearch,
  Lightbulb,
  MoreHorizontal,
  Plus,
  Trash2,
  History,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import { AgentSession, AgentMessage, TASK_TYPES, TaskTypeInfo } from './types';
import { aiAgentService } from '@/services/aiAgentService';

interface AIAgentChatProps {
  sessionId?: string;
  onSessionCreated?: (session: AgentSession) => void;
  onSessionSelect?: (session: AgentSession) => void;
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

const getTaskTypeInfo = (typeId: string): TaskTypeInfo => {
  return TASK_TYPES.find(t => t.id === typeId) || TASK_TYPES[0];
};

export const AIAgentChat: React.FC<AIAgentChatProps> = ({
  sessionId: initialSessionId,
  onSessionCreated,
  onSessionSelect,
  className
}) => {
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [session, setSession] = useState<AgentSession | null>(null);
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(!initialSessionId);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 加载会话列表
  const loadSessions = useCallback(async () => {
    try {
      const data = await aiAgentService.listSessions();
      setSessions(data.sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }, []);

  // 加载会话详情
  const loadSession = useCallback(async (id: string) => {
    try {
      const data = await aiAgentService.getSession(id);
      setSession(data);
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId, loadSession]);

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // 创建新会话
  const createSession = async (title: string, taskType: string) => {
    try {
      const data = await aiAgentService.createSession({
        title,
        task_type: taskType,
        context: {}
      });

      const newSession = data.session;
      setSessions(prev => [newSession, ...prev]);
      setSessionId(newSession.id);
      setSession(newSession);
      setMessages([]);
      setShowNewSessionDialog(false);

      onSessionCreated?.(newSession);

      // 聚焦输入框
      setTimeout(() => inputRef.current?.focus(), 100);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  // 发送消息
  const sendMessage = async () => {
    if (!input.trim() || !sessionId || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // 添加用户消息到界面
    const tempUserMsg: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, tempUserMsg]);

    try {
      let assistantContent = '';

      await aiAgentService.chat(
        sessionId,
        { message: userMessage, stream: true },
        (chunk) => {
          if (chunk.type === 'chunk') {
            assistantContent += chunk.content;
            // 更新最后一条消息
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMsg = newMessages[newMessages.length - 1];
              if (lastMsg && lastMsg.role === 'assistant') {
                lastMsg.content = assistantContent;
              } else {
                newMessages.push({
                  id: Date.now().toString(),
                  role: 'assistant',
                  content: assistantContent,
                  created_at: new Date().toISOString()
                });
              }
              return newMessages;
            });
          }
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: '抱歉，我遇到了一些问题。请稍后再试。',
        created_at: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // 删除会话
  const deleteSession = async (id: string) => {
    try {
      await aiAgentService.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (sessionId === id) {
        setSessionId(undefined);
        setSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  // 处理按键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (showNewSessionDialog) {
    return (
      <Card className={cn("h-full flex flex-col", className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            选择AI助手类型
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-auto">
          <div className="grid grid-cols-2 gap-4">
            {TASK_TYPES.map((taskType) => (
              <button
                key={taskType.id}
                onClick={() => createSession(`新的${taskType.name}会话`, taskType.id)}
                className="flex flex-col items-start p-4 rounded-lg border hover:border-primary hover:bg-primary/5 transition-colors text-left"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-2 rounded-md bg-primary/10 text-primary">
                    {taskTypeIcons[taskType.id]}
                  </div>
                  <span className="font-medium">{taskType.name}</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {taskType.description}
                </p>
              </button>
            ))}
          </div>

          {sessions.length > 0 && (
            <>
              <Separator className="my-6" />
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <History className="h-4 w-4" />
                最近会话
              </h3>
              <div className="space-y-2">
                {sessions.slice(0, 5).map((s) => (
                  <button
                    key={s.id}
                    onClick={() => {
                      setSessionId(s.id);
                      setShowNewSessionDialog(false);
                      onSessionSelect?.(s);
                    }}
                    className="w-full flex items-center gap-3 p-3 rounded-lg border hover:bg-muted transition-colors text-left"
                  >
                    <div className="p-1.5 rounded bg-muted">
                      {taskTypeIcons[s.task_type]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{s.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(s.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      {/* 头部 */}
      <CardHeader className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">
                {session?.title || 'AI科研助手'}
              </CardTitle>
              {session && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary" className="text-xs">
                    {getTaskTypeInfo(session.task_type).name}
                  </Badge>
                  <span>•</span>
                  <span>{session.message_count} 条消息</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowNewSessionDialog(true)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>新会话</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => sessionId && deleteSession(sessionId)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  删除会话
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>

      {/* 消息区域 */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                <Sparkles className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-lg font-medium mb-2">开始对话</h3>
              <p className="text-muted-foreground max-w-sm mx-auto">
                我是您的AI科研助手，可以帮您进行文献调研、论文写作、数据分析等工作。
                请告诉我您需要什么帮助？
              </p>

              {/* 快捷提示 */}
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {['帮我搜索相关文献', '帮我写引言部分', '分析这个数据', '制定研究计划'].map((prompt) => (
                  <Button
                    key={prompt}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInput(prompt);
                      inputRef.current?.focus();
                    }}
                  >
                    {prompt}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={message.id || index}
              className={cn(
                "flex gap-3",
                message.role === 'user' ? "flex-row-reverse" : ""
              )}
            >
              <Avatar className={cn(
                "h-8 w-8",
                message.role === 'user' ? "bg-primary" : "bg-primary/10"
              )}>
                <AvatarFallback>
                  {message.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </AvatarFallback>
              </Avatar>

              <div className={cn(
                "max-w-[80%] rounded-lg px-4 py-2",
                message.role === 'user'
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}>
                {message.role === 'tool' && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                    <Wrench className="h-3 w-3" />
                    <span>工具调用: {message.metadata?.tool_type}</span>
                  </div>
                )}
                <div className="whitespace-pre-wrap text-sm">
                  {message.content}
                </div>
                <div className={cn(
                  "text-xs mt-1",
                  message.role === 'user' ? "text-primary-foreground/60" : "text-muted-foreground"
                )}>
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <Avatar className="h-8 w-8 bg-primary/10">
                <AvatarFallback><Bot className="h-4 w-4" /></AvatarFallback>
              </Avatar>
              <div className="bg-muted rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">思考中...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* 输入区域 */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          AI助手可能会产生不准确的信息，请核实重要信息。
        </p>
      </div>
    </Card>
  );
};
