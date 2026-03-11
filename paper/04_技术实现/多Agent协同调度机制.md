# 4.3 多Agent协同调度机制

多Agent协同调度是ScholarForge系统的核心机制，负责任务的分配、执行和协调。本节详细介绍调度算法的设计、冲突解决策略以及性能优化方法。

## 4.3.1 调度算法

### （1）任务队列管理

系统采用**多级优先级队列**管理待执行任务：

```python
class TaskQueue:
    """多级优先级任务队列"""

    def __init__(self):
        # 四级优先级队列
        self.queues = {
            Priority.CRITICAL: asyncio.Queue(),  # 关键任务
            Priority.HIGH: asyncio.Queue(),      # 高优先级
            Priority.NORMAL: asyncio.Queue(),    # 普通优先级
            Priority.LOW: asyncio.Queue(),       # 低优先级
        }

    async def enqueue(self, task: AgentTask):
        """将任务加入队列"""
        queue = self.queues.get(task.priority, self.queues[Priority.NORMAL])
        await queue.put(task)

    async def dequeue(self) -> Optional[AgentTask]:
        """按优先级取出任务"""
        # 按优先级顺序检查队列
        for priority in [Priority.CRITICAL, Priority.HIGH,
                        Priority.NORMAL, Priority.LOW]:
            queue = self.queues[priority]
            if not queue.empty():
                return await queue.get()
        return None
```

**优先级定义**：

| 优先级 | 数值 | 适用场景 | 处理策略 |
|--------|------|----------|----------|
| CRITICAL | 1 | 用户直接操作、系统关键任务 | 立即执行，抢占资源 |
| HIGH | 2 | 用户请求响应、重要生成任务 | 优先执行，等待不超过5秒 |
| NORMAL | 3 | 后台任务、批量处理 | 按序执行，合理等待 |
| LOW | 4 | 预加载、缓存更新 | 空闲时执行，可延迟 |

### （2）动态调度算法

系统采用**基于能力和负载的动态调度算法**：

```python
class DynamicScheduler:
    """动态任务调度器"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.task_queue = TaskQueue()
        self.running_tasks: Dict[str, AgentTask] = {}

    async def schedule(self, task: AgentTask) -> Optional[str]:
        """
        调度任务到合适的Agent
        返回分配的Agent ID，如果无法调度则返回None
        """
        # 1. 筛选有能力的Agent
        capable_agents = self._find_capable_agents(task)

        if not capable_agents:
            logger.warning(f"No capable agent for task {task.id}")
            return None

        # 2. 计算每个Agent的调度分数
        agent_scores = {}
        for agent in capable_agents:
            score = self._calculate_score(agent, task)
            agent_scores[agent.id] = score

        # 3. 选择最优Agent
        best_agent_id = max(agent_scores, key=agent_scores.get)

        # 4. 分配任务
        await self._assign_task(task, best_agent_id)

        return best_agent_id

    def _calculate_score(self, agent: Agent, task: AgentTask) -> float:
        """计算Agent的调度分数"""
        # 能力匹配度 (40%)
        capability_score = self._match_capability(agent, task)

        # 负载因子 (40%)
        load_score = 1.0 - (agent.current_load / agent.max_capacity)

        # 响应时间估计 (20%)
        response_score = self._estimate_response(agent, task)

        # 加权综合
        final_score = (
            capability_score * 0.4 +
            load_score * 0.4 +
            response_score * 0.2
        )

        return final_score
```

**能力匹配计算**：

```python
def _match_capability(self, agent: Agent, task: AgentTask) -> float:
    """
    计算Agent能力与任务需求的匹配度
    返回0-1之间的分数
    """
    task_requirements = task.required_capabilities
    agent_capabilities = agent.capabilities

    if not task_requirements:
        return 1.0

    match_count = 0
    for req in task_requirements:
        # 检查Agent是否有该能力
        if any(self._capability_matches(req, cap)
               for cap in agent_capabilities):
            match_count += 1

    return match_count / len(task_requirements)
```

### （3）负载均衡策略

**负载计算**：

```python
class LoadBalancer:
    def calculate_load(self, agent: Agent) -> float:
        """计算Agent当前负载"""
        # 任务数量权重
        task_weight = agent.running_tasks / agent.max_concurrent_tasks

        # CPU使用率权重
        cpu_weight = agent.cpu_usage / 100.0

        # 内存使用率权重
        memory_weight = agent.memory_usage / 100.0

        # 加权平均
        load = (
            task_weight * 0.5 +
            cpu_weight * 0.3 +
            memory_weight * 0.2
        )

        return min(load, 1.0)  # 最大为1.0
```

**动态扩容**：

当所有Agent负载过高时，触发自动扩容：

```python
async def check_and_scale(self):
    """检查负载并动态扩容"""
    avg_load = self._get_average_load()

    if avg_load > 0.8:  # 平均负载超过80%
        # 启动新的Agent实例
        new_agent = await self._spawn_agent()
        logger.info(f"Scaled up: new agent {new_agent.id}")

    elif avg_load < 0.3 and len(self.agents) > self.min_agents:
        # 负载过低，回收Agent
        agent_to_remove = self._find_idle_agent()
        await self._remove_agent(agent_to_remove)
```

### （4）超时处理机制

**任务超时管理**：

```python
class TimeoutManager:
    def __init__(self):
        self.timeouts: Dict[str, asyncio.Task] = {}

    async def start_timeout_watch(self, task: AgentTask):
        """启动任务超时监控"""
        timeout_seconds = self._get_timeout(task)

        async def timeout_callback():
            await asyncio.sleep(timeout_seconds)
            await self._handle_timeout(task)

        watch_task = asyncio.create_task(timeout_callback())
        self.timeouts[task.id] = watch_task

    async def cancel_timeout(self, task_id: str):
        """取消超时监控（任务完成时）"""
        if task_id in self.timeouts:
            self.timeouts[task_id].cancel()
            del self.timeouts[task_id]

    async def _handle_timeout(self, task: AgentTask):
        """处理任务超时"""
        logger.warning(f"Task {task.id} timed out")

        # 1. 标记任务失败
        task.status = TaskStatus.TIMEOUT

        # 2. 通知用户
        await self._notify_user(task, "任务执行超时")

        # 3. 尝试重新调度
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            await scheduler.reschedule(task)
```

## 4.3.2 冲突解决

### （1）冲突类型与检测

**资源冲突检测**：

```python
class ConflictDetector:
    def detect_resource_conflict(
        self,
        task1: AgentTask,
        task2: AgentTask
    ) -> Optional[ResourceConflict]:
        """检测两个任务是否存在资源冲突"""
        # 检查资源需求交集
        common_resources = set(task1.required_resources) & \
                          set(task2.required_resources)

        if not common_resources:
            return None

        # 检查时间重叠
        if self._time_overlap(task1, task2):
            return ResourceConflict(
                task1_id=task1.id,
                task2_id=task2.id,
                resources=list(common_resources)
            )

        return None
```

**数据冲突检测**：

使用版本向量检测数据修改冲突：

```python
@dataclass
class VersionVector:
    """版本向量，用于分布式冲突检测"""
    agent_id: str
    timestamp: datetime
    version: int

class DataConflictDetector:
    def detect_write_conflict(
        self,
        local_version: VersionVector,
        remote_version: VersionVector
    ) -> bool:
        """
        检测写冲突
        如果版本向量不兼容，则存在冲突
        """
        # 如果远程版本更新，且不是基于本地版本，则冲突
        if remote_version.version > local_version.version:
            # 检查是否有因果关系
            if not self._is_descendant(local_version, remote_version):
                return True

        return False
```

### （2）冲突解决策略

**策略1：优先级策略**

```python
class PriorityStrategy:
    def resolve(self, conflict: Conflict) -> Resolution:
        """基于优先级解决冲突"""
        task1 = self.get_task(conflict.task1_id)
        task2 = self.get_task(conflict.task2_id)

        # 高优先级任务获胜
        if task1.priority > task2.priority:
            return Resolution(winner=task1.id, loser=task2.id)
        elif task2.priority > task1.priority:
            return Resolution(winner=task2.id, loser=task1.id)
        else:
            # 优先级相同，使用其他策略
            return self._fallback_resolve(conflict)
```

**策略2：时间戳策略**

```python
class TimestampStrategy:
    def resolve(self, conflict: Conflict) -> Resolution:
        """基于时间戳解决冲突（先到先服务）"""
        task1 = self.get_task(conflict.task1_id)
        task2 = self.get_task(conflict.task2_id)

        # 先创建的任务获胜
        if task1.created_at < task2.created_at:
            return Resolution(winner=task1.id, loser=task2.id)
        else:
            return Resolution(winner=task2.id, loser=task1.id)
```

**策略3：协商策略**

```python
class NegotiationStrategy:
    async def resolve(self, conflict: Conflict) -> Resolution:
        """
        通过Agent协商解决冲突
        让涉及冲突的Agent提出解决方案
        """
        # 获取相关Agent
        agents = self._get_involved_agents(conflict)

        # 收集各Agent的解决方案
        proposals = []
        for agent in agents:
            proposal = await agent.propose_solution(conflict)
            proposals.append(proposal)

        # 评估各方案
        best_proposal = self._evaluate_proposals(proposals)

        return Resolution(
            winner=best_proposal.winner,
            loser=best_proposal.loser,
            solution=best_proposal.solution
        )
```

**策略4：合并策略**

对于数据冲突，尝试自动合并：

```python
class MergeStrategy:
    def resolve_data_conflict(
        self,
        local_data: Dict,
        remote_data: Dict,
        base_data: Dict
    ) -> MergeResult:
        """
        三路合并算法
        """
        merged = {}
        conflicts = []

        all_keys = set(local_data.keys()) | set(remote_data.keys())

        for key in all_keys:
            local_val = local_data.get(key)
            remote_val = remote_data.get(key)
            base_val = base_data.get(key)

            if local_val == remote_val:
                # 双方一致
                merged[key] = local_val
            elif local_val == base_val:
                # 只有远程修改
                merged[key] = remote_val
            elif remote_val == base_val:
                # 只有本地修改
                merged[key] = local_val
            else:
                # 双方都修改，且不同
                conflicts.append(key)
                # 使用更详细的合并策略
                merged[key] = self._smart_merge(
                    local_val, remote_val, base_val
                )

        return MergeResult(data=merged, conflicts=conflicts)
```

### （3）死锁预防

**死锁检测**：

```python
class DeadlockDetector:
    def detect_deadlock(self) -> Optional[List[str]]:
        """
        使用资源分配图检测死锁
        返回死锁涉及的Agent ID列表
        """
        # 构建等待图
        wait_graph = defaultdict(list)

        for agent in self.agents.values():
            if agent.status == AgentStatus.WAITING:
                # Agent等待的资源持有者
                holders = self._get_resource_holders(
                    agent.waiting_for_resources
                )
                wait_graph[agent.id] = holders

        # 检测环
        cycle = self._find_cycle(wait_graph)
        return cycle
```

**死锁解除**：

```python
async def resolve_deadlock(self, deadlock_agents: List[str]):
    """解除死锁"""
    # 策略：选择优先级最低的任务终止
    victim_task = min(
        (self.running_tasks[agent_id] for agent_id in deadlock_agents),
        key=lambda t: t.priority
    )

    # 终止受害者任务
    await self._abort_task(victim_task)

    logger.info(f"Resolved deadlock by aborting task {victim_task.id}")
```

## 4.3.3 性能优化

### （1）请求合并

合并相似请求，减少LLM调用：

```python
class RequestBatcher:
    def __init__(self, batch_interval: float = 0.1):
        self.batch_interval = batch_interval
        self.pending_requests: List[Request] = []

    async def add_request(self, request: Request) -> Response:
        """添加请求到批次"""
        future = asyncio.Future()
        self.pending_requests.append((request, future))

        # 等待批次处理
        return await future

    async def process_batch(self):
        """批量处理请求"""
        while True:
            await asyncio.sleep(self.batch_interval)

            if not self.pending_requests:
                continue

            # 取出批次
            batch = self.pending_requests[:]
            self.pending_requests = []

            # 合并相似请求
            merged = self._merge_similar_requests(batch)

            # 批量执行
            results = await self._execute_batch(merged)

            # 分发结果
            self._dispatch_results(batch, results)
```

### （2）结果缓存

缓存常见查询的结果：

```python
class ResultCache:
    def __init__(self, ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.ttl = ttl

    async def get_or_compute(
        self,
        key: str,
        compute_func: Callable,
    ) -> Any:
        """获取缓存结果，如果不存在则计算"""
        # 检查缓存
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                return entry.value

        # 计算结果
        result = await compute_func()

        # 存入缓存
        self.cache[key] = CacheEntry(
            value=result,
            timestamp=datetime.now()
        )

        return result
```

### （3）异步任务队列

使用消息队列处理后台任务：

```python
class AsyncTaskQueue:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.processors: Dict[str, Callable] = {}

    async def enqueue(self, task_type: str, task_data: Dict):
        """将任务加入队列"""
        await self.redis.xadd(
            f"queue:{task_type}",
            {"data": json.dumps(task_data)}
        )

    async def start_worker(self, task_type: str):
        """启动任务处理工作线程"""
        processor = self.processors.get(task_type)
        if not processor:
            raise ValueError(f"No processor for {task_type}")

        while True:
            # 读取任务
            messages = await self.redis.xreadgroup(
                group_name="workers",
                consumer_name=f"worker_{os.getpid()}",
                streams={f"queue:{task_type}": ">"},
                block=5000
            )

            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    task_data = json.loads(fields["data"])

                    try:
                        # 处理任务
                        await processor(task_data)

                        # 确认完成
                        await self.redis.xack(
                            stream, "workers", msg_id
                        )
                    except Exception as e:
                        logger.error(f"Task failed: {e}")
                        # 重试逻辑...
```

### （4）降级策略

系统负载过高时的降级处理：

```python
class DegradationStrategy:
    def __init__(self):
        self.levels = [
            DegradationLevel.NORMAL,      # 正常
            DegradationLevel.LIGHT,       # 轻度：禁用非关键功能
            DegradationLevel.MODERATE,    # 中度：简化AI响应
            DegradationLevel.SEVERE,      # 重度：仅保留核心功能
        ]
        self.current_level = 0

    async def check_and_degrade(self):
        """检查系统负载并执行降级"""
        load = await self._get_system_load()

        if load > 0.9 and self.current_level < 3:
            # 升级到更严重的降级级别
            self.current_level += 1
            await self._apply_degradation(self.levels[self.current_level])

        elif load < 0.5 and self.current_level > 0:
            # 恢复降级
            self.current_level -= 1
            await self._apply_degradation(self.levels[self.current_level])

    async def _apply_degradation(self, level: DegradationLevel):
        """应用降级策略"""
        if level == DegradationLevel.LIGHT:
            # 禁用非关键功能：推荐、分析等
            await self._disable_non_critical_features()

        elif level == DegradationLevel.MODERATE:
            # 简化AI响应，缩短生成长度
            await self._simplify_ai_responses()

        elif level == DegradationLevel.SEVERE:
            # 仅保留核心写作功能
            await self._keep_only_core_features()
```

---

**本节小结**：

本节详细介绍了多Agent协同调度机制的实现。首先，在调度算法方面，设计了多级优先级队列管理任务，实现了基于能力和负载的动态调度算法，通过能力匹配度、负载因子和响应时间综合评估选择最优Agent，并实现了负载均衡和自动扩容机制。其次，在冲突解决方面，实现了资源冲突和数据冲突的检测机制，提供了优先级、时间戳、协商和合并四种冲突解决策略，以及死锁检测和解除机制。最后，在性能优化方面，通过请求合并、结果缓存、异步任务队列和降级策略，确保系统在高负载下仍能稳定运行。这些机制共同构成了多Agent协同调度的核心能力，为系统的高效运行提供了保障。
