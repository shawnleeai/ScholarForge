import React, { useState, useEffect } from 'react';
import {
  Calendar,
  CheckCircle2,
  Circle,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  MoreHorizontal,
  Plus,
  ChevronRight,
  Flag,
  ListTodo,
  Sparkles
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
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
import { cn } from '@/lib/utils';
import { ResearchPlan as ResearchPlanType, PlanMilestone, PlanTask } from './types';
import { aiAgentService } from '@/services/aiAgentService';

interface ResearchPlanPanelProps {
  className?: string;
}

export const ResearchPlanPanel: React.FC<ResearchPlanPanelProps> = ({ className }) => {
  const [plans, setPlans] = useState<ResearchPlanType[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<ResearchPlanType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newPlan, setNewPlan] = useState({
    title: '',
    objectives: [''],
    start_date: '',
    end_date: ''
  });

  // 加载研究计划
  const loadPlans = async () => {
    try {
      setIsLoading(true);
      const data = await aiAgentService.listPlans();
      setPlans(data.plans);
      if (data.plans.length > 0 && !selectedPlan) {
        setSelectedPlan(data.plans[0]);
      }
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  // 创建研究计划
  const handleCreatePlan = async () => {
    if (!newPlan.title.trim() || newPlan.objectives.every(o => !o.trim())) return;

    try {
      const data = await aiAgentService.createPlan({
        title: newPlan.title,
        objectives: newPlan.objectives.filter(o => o.trim()),
        start_date: newPlan.start_date || undefined,
        end_date: newPlan.end_date || undefined
      });

      setPlans(prev => [data.plan as ResearchPlanType, ...prev]);
      setSelectedPlan(data.plan as ResearchPlanType);
      setShowCreateDialog(false);
      setNewPlan({ title: '', objectives: [''], start_date: '', end_date: '' });
    } catch (error) {
      console.error('Failed to create plan:', error);
    }
  };

  // 计算进度
  const calculateProgress = (plan: ResearchPlanType) => {
    const totalTasks = plan.tasks?.length || 0;
    if (totalTasks === 0) return 0;
    const completedTasks = plan.tasks?.filter(t => t.status === 'completed').length || 0;
    return Math.round((completedTasks / totalTasks) * 100);
  };

  // 更新任务状态
  const updateTaskStatus = async (taskId: string, status: string) => {
    if (!selectedPlan) return;

    try {
      await aiAgentService.updatePlanProgress(selectedPlan.id, {
        task_id: taskId,
        status
      });

      // 更新本地状态
      setSelectedPlan(prev => {
        if (!prev) return null;
        return {
          ...prev,
          tasks: prev.tasks?.map(t =>
            t.id === taskId ? { ...t, status: status as any } : t
          )
        };
      });
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  // 更新里程碑状态
  const updateMilestoneStatus = async (milestoneId: string, status: string) => {
    if (!selectedPlan) return;

    try {
      await aiAgentService.updatePlanProgress(selectedPlan.id, {
        milestone_id: milestoneId,
        status
      });

      setSelectedPlan(prev => {
        if (!prev) return null;
        return {
          ...prev,
          milestones: prev.milestones?.map(m =>
            m.id === milestoneId ? { ...m, status: status as any } : m
          )
        };
      });
    } catch (error) {
      console.error('Failed to update milestone:', error);
    }
  };

  // 添加目标
  const addObjective = () => {
    setNewPlan(prev => ({
      ...prev,
      objectives: [...prev.objectives, '']
    }));
  };

  // 更新目标
  const updateObjective = (index: number, value: string) => {
    setNewPlan(prev => ({
      ...prev,
      objectives: prev.objectives.map((o, i) => i === index ? value : o)
    }));
  };

  return (
    <Card className={cn("h-full flex flex-col", className)}>
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            研究计划
          </CardTitle>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" />
                新建计划
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>创建研究计划</DialogTitle>
                <DialogDescription>
                  制定您的研究目标和里程碑
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">研究标题</label>
                  <input
                    type="text"
                    value={newPlan.title}
                    onChange={(e) => setNewPlan(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="输入研究标题..."
                    className="w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">研究目标</label>
                  {newPlan.objectives.map((obj, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={obj}
                        onChange={(e) => updateObjective(index, e.target.value)}
                        placeholder={`目标 ${index + 1}`}
                        className="flex-1 px-3 py-2 border rounded-md text-sm"
                      />
                      {index === newPlan.objectives.length - 1 && (
                        <Button type="button" variant="outline" size="icon" onClick={addObjective}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">开始日期</label>
                    <input
                      type="date"
                      value={newPlan.start_date}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, start_date: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">结束日期</label>
                    <input
                      type="date"
                      value={newPlan.end_date}
                      onChange={(e) => setNewPlan(prev => ({ ...prev, end_date: e.target.value }))}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    />
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  取消
                </Button>
                <Button onClick={handleCreatePlan} disabled={!newPlan.title.trim()}>
                  创建
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>

      <div className="flex-1 flex overflow-hidden">
        {/* 计划列表 */}
        <div className="w-64 border-r bg-muted/30">
          <ScrollArea className="h-full">
            <div className="p-2 space-y-1">
              {plans.map((plan) => {
                const progress = calculateProgress(plan);
                return (
                  <button
                    key={plan.id}
                    onClick={() => setSelectedPlan(plan)}
                    className={cn(
                      "w-full text-left p-3 rounded-lg transition-colors",
                      selectedPlan?.id === plan.id
                        ? "bg-primary/10 border-primary/20 border"
                        : "hover:bg-muted"
                    )}
                  >
                    <p className="font-medium truncate text-sm">{plan.title}</p>
                    <div className="mt-2">
                      <div className="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>进度</span>
                        <span>{progress}%</span>
                      </div>
                      <Progress value={progress} className="h-1.5" />
                    </div>
                  </button>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        {/* 计划详情 */}
        <div className="flex-1 overflow-hidden">
          {selectedPlan ? (
            <ScrollArea className="h-full">
              <div className="p-6 space-y-6">
                {/* 标题和概览 */}
                <div>
                  <h2 className="text-xl font-semibold">{selectedPlan.title}</h2>
                  <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                    {selectedPlan.start_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {new Date(selectedPlan.start_date).toLocaleDateString()}
                        {selectedPlan.end_date && ` - ${new Date(selectedPlan.end_date).toLocaleDateString()}`}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <ListTodo className="h-4 w-4" />
                      {selectedPlan.tasks?.length || 0} 个任务
                    </span>
                  </div>
                </div>

                <Separator />

                {/* 研究目标 */}
                <div>
                  <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
                    <Target className="h-4 w-4 text-primary" />
                    研究目标
                  </h3>
                  <ul className="space-y-2">
                    {selectedPlan.objectives?.map((obj, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-medium">
                          {index + 1}
                        </span>
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 里程碑 */}
                {selectedPlan.milestones && selectedPlan.milestones.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
                      <Flag className="h-4 w-4 text-primary" />
                      里程碑
                    </h3>
                    <div className="space-y-2">
                      {selectedPlan.milestones.map((milestone, index) => (
                        <div
                          key={milestone.id}
                          className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                        >
                          <button
                            onClick={() => updateMilestoneStatus(
                              milestone.id,
                              milestone.status === 'completed' ? 'todo' : 'completed'
                            )}
                            className="flex-shrink-0"
                          >
                            {milestone.status === 'completed' ? (
                              <CheckCircle2 className="h-5 w-5 text-green-500" />
                            ) : (
                              <Circle className="h-5 w-5 text-muted-foreground" />
                            )}
                          </button>
                          <div className="flex-1">
                            <p className={cn(
                              "text-sm font-medium",
                              milestone.status === 'completed' && "line-through text-muted-foreground"
                            )}>
                              {milestone.title}
                            </p>
                            {milestone.due_date && (
                              <p className="text-xs text-muted-foreground mt-0.5">
                                截止: {new Date(milestone.due_date).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                          <Badge variant="outline" className="text-xs">
                            阶段 {index + 1}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 任务列表 */}
                {selectedPlan.tasks && selectedPlan.tasks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
                      <ListTodo className="h-4 w-4 text-primary" />
                      任务列表
                    </h3>
                    <div className="space-y-1">
                      {selectedPlan.tasks.map((task) => (
                        <div
                          key={task.id}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted transition-colors"
                        >
                          <button
                            onClick={() => updateTaskStatus(
                              task.id,
                              task.status === 'completed' ? 'todo' : 'completed'
                            )}
                          >
                            {task.status === 'completed' ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500" />
                            ) : task.status === 'in_progress' ? (
                              <div className="h-4 w-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
                            ) : (
                              <Circle className="h-4 w-4 text-muted-foreground" />
                            )}
                          </button>
                          <span className={cn(
                            "text-sm flex-1",
                            task.status === 'completed' && "line-through text-muted-foreground"
                          )}>
                            {task.title}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 进度统计 */}
                <div className="p-4 rounded-lg bg-muted">
                  <h3 className="text-sm font-medium flex items-center gap-2 mb-3">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    进度概览
                  </h3>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold">{calculateProgress(selectedPlan)}%</p>
                      <p className="text-xs text-muted-foreground">总进度</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {selectedPlan.tasks?.filter(t => t.status === 'completed').length || 0}
                      </p>
                      <p className="text-xs text-muted-foreground">已完成</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">
                        {selectedPlan.milestones?.filter(m => m.status === 'completed').length || 0}
                      </p>
                      <p className="text-xs text-muted-foreground">里程碑</p>
                    </div>
                  </div>
                </div>
              </div>
            </ScrollArea>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-6">
              <Target className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">还没有研究计划</h3>
              <p className="text-muted-foreground text-sm mb-4">
                创建研究计划来管理您的研究进度
              </p>
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                创建计划
              </Button>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
