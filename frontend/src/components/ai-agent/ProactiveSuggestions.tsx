import React, { useState, useEffect } from 'react';
import {
  Lightbulb,
  X,
  Check,
  Clock,
  PenTool,
  BookOpen,
  Calendar,
  AlertCircle,
  ChevronRight,
  Sparkles,
  Bell
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { AgentSuggestion } from './types';
import { aiAgentService } from '@/services/aiAgentService';

interface ProactiveSuggestionsProps {
  className?: string;
  onSuggestionAction?: (suggestion: AgentSuggestion) => void;
}

const actionTypeIcons: Record<string, React.ReactNode> = {
  write: <PenTool className="h-4 w-4" />,
  read: <BookOpen className="h-4 w-4" />,
  analyze: <Sparkles className="h-4 w-4" />,
  remind: <Clock className="h-4 w-4" />,
};

const actionTypeLabels: Record<string, string> = {
  write: '写作',
  read: '阅读',
  analyze: '分析',
  remind: '提醒',
};

export const ProactiveSuggestions: React.FC<ProactiveSuggestionsProps> = ({
  className,
  onSuggestionAction
}) => {
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  // 加载建议
  const loadSuggestions = async () => {
    try {
      setIsLoading(true);
      const data = await aiAgentService.getSuggestions();
      setSuggestions(data.suggestions.filter(s => !s.is_dismissed));
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSuggestions();
    // 每5分钟刷新一次
    const interval = setInterval(loadSuggestions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // 接受建议
  const handleAccept = async (suggestion: AgentSuggestion) => {
    try {
      await aiAgentService.acceptSuggestion(suggestion.id);
      setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
      onSuggestionAction?.(suggestion);
    } catch (error) {
      console.error('Failed to accept suggestion:', error);
    }
  };

  // 忽略建议
  const handleDismiss = async (suggestion: AgentSuggestion) => {
    try {
      setDismissedIds(prev => new Set(prev).add(suggestion.id));
      await aiAgentService.dismissSuggestion(suggestion.id);
      setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
    } catch (error) {
      console.error('Failed to dismiss suggestion:', error);
      setDismissedIds(prev => {
        const next = new Set(prev);
        next.delete(suggestion.id);
        return next;
      });
    }
  };

  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days === 1) return '昨天';
    return `${days}天前`;
  };

  if (suggestions.length === 0 && !isLoading) {
    return null;
  }

  return (
    <Card className={cn("border-primary/20 bg-primary/5", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <div className="p-1.5 rounded-md bg-primary/10">
            <Lightbulb className="h-4 w-4 text-primary" />
          </div>
          AI建议
          {suggestions.length > 0 && (
            <Badge variant="secondary" className="ml-auto">
              {suggestions.length}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="max-h-[300px]">
          <div className="space-y-3">
            {suggestions.map((suggestion) => (
              <div
                key={suggestion.id}
                className={cn(
                  "p-3 rounded-lg bg-card border transition-all",
                  dismissedIds.has(suggestion.id) && "opacity-50"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-md bg-primary/10 text-primary mt-0.5">
                    {actionTypeIcons[suggestion.action_type] || <Sparkles className="h-4 w-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-sm">{suggestion.title}</h4>
                      <Badge variant="outline" className="text-xs">
                        {actionTypeLabels[suggestion.action_type] || suggestion.action_type}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {suggestion.description}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs text-muted-foreground">
                        {formatTime(suggestion.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-3">
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => handleAccept(suggestion)}
                    disabled={dismissedIds.has(suggestion.id)}
                  >
                    <Check className="h-3.5 w-3.5 mr-1" />
                    接受
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDismiss(suggestion)}
                    disabled={dismissedIds.has(suggestion.id)}
                  >
                    <X className="h-3.5 w-3.5 mr-1" />
                    忽略
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// 简化版建议组件（用于侧边栏）
export const CompactSuggestions: React.FC<{
  className?: string;
  onSuggestionClick?: (suggestion: AgentSuggestion) => void;
}> = ({ className, onSuggestionClick }) => {
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await aiAgentService.getSuggestions();
        setSuggestions(data.suggestions.filter(s => !s.is_dismissed).slice(0, 3));
      } catch (error) {
        console.error('Failed to load suggestions:', error);
      }
    };
    load();
  }, []);

  if (suggestions.length === 0) return null;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center gap-2 px-2">
        <Lightbulb className="h-4 w-4 text-primary" />
        <span className="text-sm font-medium">AI建议</span>
      </div>
      <div className="space-y-1">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.id}
            onClick={() => onSuggestionClick?.(suggestion)}
            className="w-full text-left p-2 rounded-md hover:bg-muted transition-colors group"
          >
            <div className="flex items-center gap-2">
              {actionTypeIcons[suggestion.action_type] || <Sparkles className="h-3.5 w-3.5" />}
              <span className="text-sm truncate flex-1">{suggestion.title}</span>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
