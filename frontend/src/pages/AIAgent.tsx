import React, { useState } from 'react';
import {
  Bot,
  LayoutDashboard,
  Target,
  Sparkles,
  Zap,
  Settings,
  ChevronRight
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AIAgentChat,
  AgentSidebar,
  ResearchPlanPanel,
  ProactiveSuggestions,
  AgentSession
} from '@/components/ai-agent';
import { cn } from '@/lib/utils';

const AIAgentPage: React.FC = () => {
  const [selectedSession, setSelectedSession] = useState<AgentSession | null>(null);
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* 左侧边栏 */}
      <AgentSidebar
        selectedSessionId={selectedSession?.id}
        onSelectSession={setSelectedSession}
        onCreateSession={(session) => {
          setSelectedSession(session);
          setActiveTab('chat');
        }}
        className="w-72 flex-shrink-0"
      />

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {selectedSession ? (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <div className="border-b px-4 py-2 flex items-center justify-between bg-card">
              <TabsList>
                <TabsTrigger value="chat" className="flex items-center gap-1">
                  <Bot className="h-4 w-4" />
                  对话
                </TabsTrigger>
                <TabsTrigger value="plan" className="flex items-center gap-1">
                  <Target className="h-4 w-4" />
                  研究计划
                </TabsTrigger>
              </TabsList>

              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <TabsContent value="chat" className="flex-1 m-0 p-0">
              <AIAgentChat
                sessionId={selectedSession.id}
                className="h-full border-0 rounded-none"
              />
            </TabsContent>

            <TabsContent value="plan" className="flex-1 m-0 p-4 overflow-auto">
              <ResearchPlanPanel className="h-full" />
            </TabsContent>
          </Tabs>
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <Card className="max-w-md w-full">
              <CardHeader className="text-center">
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                  <Sparkles className="h-8 w-8 text-primary" />
                </div>
                <CardTitle className="text-xl">AI科研助手 V2</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground text-center">
                  智能Agent系统，支持自主任务执行、工具调用和多轮对话
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-muted text-center">
                    <Bot className="h-5 w-5 mx-auto mb-1" />
                    <p className="text-sm font-medium">多轮对话</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-center">
                    <Zap className="h-5 w-5 mx-auto mb-1" />
                    <p className="text-sm font-medium">工具调用</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-center">
                    <Target className="h-5 w-5 mx-auto mb-1" />
                    <p className="text-sm font-medium">研究规划</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-center">
                    <Sparkles className="h-5 w-5 mx-auto mb-1" />
                    <p className="text-sm font-medium">主动建议</p>
                  </div>
                </div>

                <div className="text-center text-sm text-muted-foreground">
                  从左侧选择一个会话开始，或创建新会话
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 右侧建议面板 */}
        <div className="w-80 border-l bg-muted/30 p-4 overflow-auto hidden xl:block">
          <ProactiveSuggestions
            className="mb-4"
            onSuggestionAction={(suggestion) => {
              console.log('Suggestion accepted:', suggestion);
            }}
          />

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                快捷入口
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              {[
                { label: '快速文献调研', icon: Bot },
                { label: '一键写作辅助', icon: Sparkles },
                { label: '数据分析助手', icon: Target },
              ].map((item) => (
                <Button
                  key={item.label}
                  variant="ghost"
                  className="w-full justify-start"
                  size="sm"
                >
                  <item.icon className="h-4 w-4 mr-2" />
                  {item.label}
                  <ChevronRight className="h-4 w-4 ml-auto" />
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AIAgentPage;
