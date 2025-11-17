# 模块交互协议规范 v1.0

## 1. 核心数据结构定义

### 1.1 InterviewContext (全局上下文对象)
```python
@dataclass
class InterviewContext:
    """面试会话的全局上下文,在所有模块间传递"""
    
    # 基础信息
    session_id: str                          # 会话唯一ID
    problem_text: str                        # 题目原文
    problem_metadata: Dict[str, Any]         # 题目元数据(难度、标签等)
    
    # 状态管理
    current_stage: Stage                     # 当前所处阶段(枚举)
    stage_history: List[Stage]               # 阶段历史记录
    
    # 对话记录
    conversation_history: List[Message]      # 完整对话历史
    current_user_input: str                  # 当前用户输入
    
    # 各模块的输出缓存
    identified_pattern: Optional[str] = None         # 题型识别结果
    complexity_expectation: Optional[str] = None     # 复杂度期望
    user_approach: Optional[str] = None              # 用户思路总结
    pseudocode: Optional[str] = None                 # 用户伪代码
    detected_issues: List[str] = field(default_factory=list)  # 发现的问题列表
    
    # 用户画像(后期实现)
    user_profile: Optional[Dict] = None
```

### 1.2 Message (对话消息)
```python
@dataclass
class Message:
    role: str           # "user" 或 "assistant"
    content: str        # 消息内容
    timestamp: float    # 时间戳
    stage: Stage        # 发送时的阶段
```

### 1.3 Stage (阶段枚举)
```python
from enum import Enum

class Stage(Enum):
    PROBLEM_CLARIFICATION = 0    # 题意确认
    THOUGHT_ARTICULATION = 1     # 思路口述
    COMPLEXITY_ANALYSIS = 2      # 复杂度分析
    PSEUDOCODE_DESIGN = 3        # 伪代码/框架实现
    EDGE_CASE_CHECK = 4          # 边界条件检查
    FOLLOW_UP = 5                # follow-up追问
    PATTERN_SUMMARY = 6          # 题型套路总结
```

### 1.4 ModuleResponse (模块返回结构)
```python
@dataclass
class ModuleResponse:
    """所有模块的统一返回格式"""
    
    success: bool                    # 是否成功执行
    assistant_message: str           # 给用户的回复内容
    next_stage: Optional[Stage]      # 建议的下一阶段(None表示保持当前阶段)
    context_updates: Dict[str, Any]  # 需要更新到context的字段
    metadata: Dict[str, Any]         # 模块内部元数据(用于调试/日志)
    
    # 错误处理
    error_message: Optional[str] = None
```

## 2. 模块接口定义

### 2.1 抽象基类
```python
from abc import ABC, abstractmethod

class ModuleInterface(ABC):
    """所有子模块必须实现的接口"""
    
    @abstractmethod
    def process(self, context: InterviewContext) -> ModuleResponse:
        """
        处理当前上下文,生成回复
        
        Args:
            context: 当前会话上下文
            
        Returns:
            ModuleResponse: 包含回复内容和状态更新
        """
        pass
    
    @abstractmethod
    def should_activate(self, context: InterviewContext) -> bool:
        """
        判断该模块是否应该在当前状态下激活
        
        Args:
            context: 当前会话上下文
            
        Returns:
            bool: True表示应该激活该模块
        """
        pass
    
    def validate_context(self, context: InterviewContext) -> bool:
        """
        验证上下文是否满足该模块的前置条件
        可选实现,默认返回True
        """
        return True
```

### 2.2 四大核心模块接口

#### ProblemTypeRecognizer (题型识别模块)
```python
class ProblemTypeRecognizer(ModuleInterface):
    """
    职责: 识别题目类型、生成解题线索、判断复杂度期望
    激活时机: Stage.PROBLEM_CLARIFICATION
    前置条件: problem_text不为空
    输出: 更新context.identified_pattern, context.complexity_expectation
    """
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        # 实现逻辑:
        # 1. 分析problem_text,提取关键词
        # 2. 匹配题型模式(DP/图/滑窗等)
        # 3. 生成引导线索(不直接给答案)
        # 4. 判断合理的复杂度范围
        pass
```

#### GuidedThoughtGenerator (引导式思路教练模块)
```python
class GuidedThoughtGenerator(ModuleInterface):
    """
    职责: 生成分层提示,引导用户从暴力到优化
    激活时机: Stage.THOUGHT_ARTICULATION, Stage.COMPLEXITY_ANALYSIS
    前置条件: identified_pattern已设置
    输出: 更新context.user_approach
    """
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        # 实现逻辑:
        # 1. 根据用户当前回答判断理解程度
        # 2. 生成下一层提示(由浅入深)
        # 3. 如果用户思路偏离,温和纠正
        pass
```

#### CodeEdgeCaseReviewer (代码与边界检查模块)
```python
class CodeEdgeCaseReviewer(ModuleInterface):
    """
    职责: 检查伪代码逻辑,生成边界测试用例
    激活时机: Stage.PSEUDOCODE_DESIGN, Stage.EDGE_CASE_CHECK
    前置条件: context.pseudocode不为空
    输出: 更新context.detected_issues
    """
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        # 实现逻辑:
        # 1. 模拟执行伪代码(干跑法)
        # 2. 检测逻辑漏洞(空指针/越界/死循环等)
        # 3. 生成边界case(空输入/极值/特殊情况)
        # 4. 用问题而非直接指出错误的方式引导
        pass
```

#### FollowUpGenerator (面试官追问模块)
```python
class FollowUpGenerator(ModuleInterface):
    """
    职责: 生成进阶问题、变体题目、压力测试
    激活时机: Stage.FOLLOW_UP
    前置条件: 用户已完成基础解答
    输出: 生成追问内容
    """
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        # 实现逻辑:
        # 1. 基于题型生成相关follow-up
        # 2. 根据难度递进式追问
        # 3. 提出优化方向或变体
        pass
```

## 3. 模块调用流程

### 3.1 主编排器调用模式
```python
def orchestrator_main_loop(context: InterviewContext, modules: Dict[str, ModuleInterface]):
    """
    主控制循环
    """
    # 1. 根据current_stage确定应激活的模块
    active_module = select_module_by_stage(context.current_stage, modules)
    
    # 2. 验证前置条件
    if not active_module.validate_context(context):
        return handle_missing_prerequisites(context)
    
    # 3. 调用模块处理
    response = active_module.process(context)
    
    # 4. 更新context
    if response.success:
        update_context(context, response.context_updates)
        if response.next_stage:
            context.current_stage = response.next_stage
            context.stage_history.append(response.next_stage)
    
    # 5. 返回给用户的消息
    return response.assistant_message
```

### 3.2 状态转换触发条件
```python
STAGE_TRANSITION_RULES = {
    Stage.PROBLEM_CLARIFICATION: {
        "next": Stage.THOUGHT_ARTICULATION,
        "condition": lambda ctx: ctx.identified_pattern is not None
    },
    Stage.THOUGHT_ARTICULATION: {
        "next": Stage.COMPLEXITY_ANALYSIS,
        "condition": lambda ctx: ctx.user_approach is not None
    },
    Stage.COMPLEXITY_ANALYSIS: {
        "next": Stage.PSEUDOCODE_DESIGN,
        "condition": lambda ctx: "complexity" in ctx.current_user_input.lower()
    },
    # ... 其他阶段的转换规则
}
```

## 4. Mock数据示例

### 4.1 示例题目context
```python
MOCK_CONTEXT_TWO_SUM = InterviewContext(
    session_id="session_123",
    problem_text="Given an array of integers nums and an integer target, return indices of the two numbers that add up to target.",
    problem_metadata={"difficulty": "Easy", "tags": ["Array", "Hash Table"]},
    current_stage=Stage.PROBLEM_CLARIFICATION,
    stage_history=[],
    conversation_history=[],
    current_user_input="I understand the problem, we need to find two numbers.",
    identified_pattern=None,
    complexity_expectation=None,
    user_approach=None,
    pseudocode=None,
    detected_issues=[]
)
```

### 4.2 示例模块返回
```python
MOCK_RESPONSE_PATTERN_IDENTIFIED = ModuleResponse(
    success=True,
    assistant_message="Great! I notice this is a classic **search problem**. What approach would you take if you had to solve it the simplest way possible, without worrying about efficiency?",
    next_stage=Stage.THOUGHT_ARTICULATION,
    context_updates={
        "identified_pattern": "Hash Table / Two Pointer",
        "complexity_expectation": "O(n) time, O(n) space"
    },
    metadata={"confidence": 0.95, "alternative_patterns": ["Sorting + Two Pointer"]}
)
```

## 5. 接口使用示例

### 5.1 开发者A使用示例(状态机部分)
```python
# 开发者A在状态机中这样调用开发者B的模块
from modules import CodeEdgeCaseReviewer

reviewer = CodeEdgeCaseReviewer()
context = load_current_context()

# 检查是否应该激活
if reviewer.should_activate(context):
    response = reviewer.process(context)
    
    if response.success:
        # 更新context
        for key, value in response.context_updates.items():
            setattr(context, key, value)
        
        # 发送回复给用户
        send_to_user(response.assistant_message)
```

### 5.2 开发者B使用示例(模块内部)
```python
# 开发者B在实现模块时可以这样访问context
def process(self, context: InterviewContext) -> ModuleResponse:
    # 读取需要的信息
    problem = context.problem_text
    user_code = context.pseudocode
    pattern = context.identified_pattern
    
    # 处理逻辑...
    issues = self._detect_issues(user_code)
    
    # 返回标准格式
    return ModuleResponse(
        success=True,
        assistant_message=f"I found {len(issues)} potential issues...",
        next_stage=Stage.EDGE_CASE_CHECK if issues else Stage.FOLLOW_UP,
        context_updates={"detected_issues": issues},
        metadata={"checked_patterns": ["null_check", "boundary"]}
    )
```

## 6. 注意事项

### 6.1 不要做的事
- ❌ 不要在模块内部直接修改传入的context对象
- ❌ 不要在模块间传递除context外的其他状态
- ❌ 不要在一个模块内调用另一个模块
- ❌ 不要假设用户输入的格式,总是做防御性检查

### 6.2 必须做的事
- ✅ 所有模块返回必须使用ModuleResponse格式
- ✅ 所有context修改必须通过context_updates字典
- ✅ 所有错误必须在success=False时设置error_message
- ✅ 所有模块必须实现should_activate方法

## 7. 接口版本控制
- 当前版本: v1.0
- 修改此文档必须通知另一位开发者
- 重大修改需要双方同意后才能实施
