# 异常处理策略规范 v1.0

## 1. 异常分类体系

### 1.1 异常级别定义
```python
from enum import Enum

class ExceptionLevel(Enum):
    CRITICAL = 1    # 致命错误,必须中止会话
    ERROR = 2       # 严重错误,需要降级服务
    WARNING = 3     # 警告,可以继续但需记录
    INFO = 4        # 信息性异常,正常处理流程
```

### 1.2 异常类型分类

#### A. 用户行为异常
- **跳过流程请求**: 用户想跳过某个阶段
- **重复阶段请求**: 用户想回到之前的阶段
- **无效输入**: 用户输入空白、乱码或不相关内容
- **态度消极**: 用户表现出沮丧、放弃倾向
- **过度依赖**: 用户反复要求直接答案

#### B. 系统技术异常
- **LLM调用失败**: API超时、限流、返回错误
- **状态不一致**: context数据缺失或损坏
- **模块执行失败**: 某个模块抛出异常
- **资源不足**: 内存、token超限

#### C. 逻辑流程异常
- **前置条件不满足**: 进入某阶段但缺少必要数据
- **死循环检测**: 用户在同一阶段停滞过久
- **状态转换失败**: 无法确定下一阶段

## 2. 异常处理策略

### 2.1 用户行为异常处理

#### 策略1: 跳过流程请求
```python
class SkipStageException:
    """
    触发条件: 用户输入包含"跳过"、"skip"、"下一个"等关键词
    """
    
    def handle(context: InterviewContext, requested_stage: Optional[Stage]) -> ModuleResponse:
        """
        处理逻辑:
        1. 判断当前阶段是否允许跳过
        2. 记录用户跳过行为(用于画像分析)
        3. 给予温和提醒,说明该阶段的重要性
        4. 如果用户坚持,允许跳过但设置标记
        """
        
        # 允许跳过的阶段
        SKIPPABLE_STAGES = {
            Stage.COMPLEXITY_ANALYSIS,  # 复杂度分析可以后补
            Stage.PATTERN_SUMMARY       # 总结可以跳过
        }
        
        # 绝不能跳过的核心阶段
        CRITICAL_STAGES = {
            Stage.THOUGHT_ARTICULATION,   # 必须说思路
            Stage.PSEUDOCODE_DESIGN,      # 必须写代码
            Stage.EDGE_CASE_CHECK         # 必须检查边界
        }
        
        if context.current_stage in CRITICAL_STAGES:
            return ModuleResponse(
                success=True,
                assistant_message=(
                    "I understand you want to move forward, but this stage is crucial for interview success. "
                    "In real interviews, skipping **思路讲解/代码实现** would be a red flag. "
                    "How about we spend just 2-3 minutes on this? It'll make a big difference."
                ),
                next_stage=None,  # 保持当前阶段
                context_updates={"skip_requested": True},
                metadata={"warning": "User attempted to skip critical stage"}
            )
        
        elif context.current_stage in SKIPPABLE_STAGES:
            return ModuleResponse(
                success=True,
                assistant_message=(
                    f"Okay, we can move on for now. But remember, in a real interview, "
                    f"{'discussing complexity shows analytical maturity' if context.current_stage == Stage.COMPLEXITY_ANALYSIS else 'summarizing patterns helps you in future problems'}. "
                    f"Let's continue to the next part."
                ),
                next_stage=get_next_stage(context.current_stage),
                context_updates={"skipped_stages": context.skipped_stages + [context.current_stage]},
                metadata={"info": "User skipped optional stage"}
            )
```

#### 策略2: 无效输入处理
```python
class InvalidInputException:
    """
    触发条件: 
    - 空白输入
    - 单字符或过短输入(<5字符)
    - 完全不相关的内容(用LLM判断)
    """
    
    RESPONSE_TEMPLATES = {
        "empty": "I didn't catch that. Could you share your thoughts on {current_question}?",
        "too_short": "That's a bit brief! Could you elaborate a bit more?",
        "off_topic": "Hmm, that seems unrelated. Let me rephrase: {current_question}",
        "repeated": "I notice you've said something similar before. Want to try a different angle?"
    }
    
    def handle(context: InterviewContext, input_type: str) -> ModuleResponse:
        """
        处理逻辑:
        1. 识别无效输入类型
        2. 使用温和的提示模板
        3. 如果连续3次无效,触发降级策略
        """
        
        invalid_count = context.metadata.get("consecutive_invalid_inputs", 0) + 1
        
        if invalid_count >= 3:
            # 连续3次无效,可能用户遇到困难
            return trigger_help_mode(context)
        
        return ModuleResponse(
            success=True,
            assistant_message=RESPONSE_TEMPLATES[input_type].format(
                current_question=context.metadata.get("last_question", "the current problem")
            ),
            next_stage=None,
            context_updates={"consecutive_invalid_inputs": invalid_count},
            metadata={"warning": f"Invalid input detected: {input_type}"}
        )
```

#### 策略3: 用户情绪低落处理
```python
class UserFrustrationException:
    """
    触发条件:
    - 输入包含"太难了"、"不会"、"放弃"等关键词
    - 连续多次要求提示
    - 停留在同一阶段超过10分钟
    """
    
    def handle(context: InterviewContext) -> ModuleResponse:
        """
        处理逻辑:
        1. 立即给予情感支持
        2. 降低当前问题难度
        3. 提供更多引导
        4. 建议暂时跳过,改天再战
        """
        
        encouragement = [
            "I can tell this is challenging, and that's completely normal! Even experienced engineers struggle with these problems at first.",
            "Let me help you break this down into smaller steps. We'll tackle it together.",
            "How about we approach this differently? Sometimes a fresh angle makes all the difference."
        ]
        
        # 根据用户历史表现选择鼓励语
        user_level = context.user_profile.get("estimated_level", "beginner") if context.user_profile else "beginner"
        
        if user_level == "beginner":
            hint_level = "very_detailed"  # 给新手更多帮助
        else:
            hint_level = "moderate"
        
        return ModuleResponse(
            success=True,
            assistant_message=random.choice(encouragement) + "\n\n" + generate_adaptive_hint(context, hint_level),
            next_stage=None,
            context_updates={
                "frustration_detected": True,
                "hint_level": hint_level
            },
            metadata={"support_triggered": True}
        )
```

#### 策略4: 过度依赖直接答案
```python
class OverRelianceException:
    """
    触发条件:
    - 用户多次直接要求答案
    - 不愿自己思考,总是要提示
    """
    
    def handle(context: InterviewContext) -> ModuleResponse:
        """
        处理逻辑:
        1. 温和但坚定地拒绝直接给答案
        2. 解释为什么思考过程比答案重要
        3. 提供思考框架而非答案
        """
        
        return ModuleResponse(
            success=True,
            assistant_message=(
                "I totally get wanting to see the answer! But here's the thing: "
                "in a real interview, the interviewer wants to see **how you think**, not just the final solution. "
                "\n\nInstead of giving you the answer, let me ask you this: "
                "{guiding_question}"
                "\n\nTrust me, working through this yourself will help you WAY more than seeing my solution."
            ).format(
                guiding_question=generate_socratic_question(context)
            ),
            next_stage=None,
            context_updates={"answer_requests": context.metadata.get("answer_requests", 0) + 1},
            metadata={"teaching_moment": True}
        )
```

### 2.2 系统技术异常处理

#### 策略5: LLM调用失败
```python
class LLMCallException:
    """
    触发条件: API调用超时、限流、返回错误
    """
    
    def handle(error: Exception, context: InterviewContext, retry_count: int = 0) -> ModuleResponse:
        """
        处理逻辑:
        1. 自动重试(最多3次,指数退避)
        2. 如果持续失败,使用预设模板回复
        3. 记录错误日志供后续分析
        """
        
        MAX_RETRIES = 3
        
        if retry_count < MAX_RETRIES:
            # 指数退避重试
            time.sleep(2 ** retry_count)
            return retry_llm_call(context, retry_count + 1)
        
        else:
            # 降级为模板回复
            return ModuleResponse(
                success=True,  # 虽然LLM失败,但我们有降级方案
                assistant_message=get_fallback_template(context.current_stage),
                next_stage=None,
                context_updates={},
                metadata={
                    "error": str(error),
                    "fallback_used": True,
                    "level": ExceptionLevel.ERROR
                }
            )
    
    FALLBACK_TEMPLATES = {
        Stage.THOUGHT_ARTICULATION: (
            "Let's think about this step by step. What would be the simplest "
            "approach to solve this problem, even if it's not the most efficient?"
        ),
        Stage.COMPLEXITY_ANALYSIS: (
            "Can you analyze the time and space complexity of your approach? "
            "Consider: how many times do we iterate through the data?"
        ),
        # ... 其他阶段的兜底模板
    }
```

#### 策略6: 状态不一致异常
```python
class StateInconsistencyException:
    """
    触发条件: context缺少必要字段,或字段值不合法
    """
    
    def handle(context: InterviewContext, missing_field: str) -> ModuleResponse:
        """
        处理逻辑:
        1. 尝试从历史记录重建缺失字段
        2. 如果无法重建,回退到安全状态
        3. 通知用户并优雅恢复
        """
        
        # 尝试从对话历史重建
        if missing_field == "identified_pattern":
            # 快速重新分析题目
            pattern = quick_pattern_detection(context.problem_text)
            context.identified_pattern = pattern
            return continue_normally(context)
        
        elif missing_field in ["user_approach", "pseudocode"]:
            # 这些字段缺失说明用户没有提供,需要主动询问
            return ModuleResponse(
                success=True,
                assistant_message=f"Before we continue, could you share your {missing_field.replace('_', ' ')}?",
                next_stage=None,
                context_updates={},
                metadata={"recovered_from": "missing_field"}
            )
        
        else:
            # 严重错误,回退到题目确认阶段
            return ModuleResponse(
                success=False,
                assistant_message="Oops, something went wrong. Let's start fresh from understanding the problem.",
                next_stage=Stage.PROBLEM_CLARIFICATION,
                context_updates={"reset_triggered": True},
                error_message=f"Critical state inconsistency: missing {missing_field}",
                metadata={"level": ExceptionLevel.CRITICAL}
            )
```

### 2.3 逻辑流程异常处理

#### 策略7: 死循环检测
```python
class StagnationException:
    """
    触发条件: 
    - 用户在同一阶段超过15分钟
    - 同一问题被重复问3次以上
    """
    
    def handle(context: InterviewContext) -> ModuleResponse:
        """
        处理逻辑:
        1. 识别卡点原因(概念不清/题目太难/引导不够)
        2. 提供更强的引导或直接给出框架
        3. 建议降低难度或换题
        """
        
        time_in_stage = time.time() - context.metadata.get("stage_start_time", time.time())
        
        if time_in_stage > 900:  # 15分钟
            return ModuleResponse(
                success=True,
                assistant_message=(
                    "I notice we've been on this for a while. That's okay! "
                    "Let me give you a stronger hint:\n\n"
                    f"{generate_strong_hint(context)}\n\n"
                    "Does this help? Or would you like to try a different problem first?"
                ),
                next_stage=None,
                context_updates={"strong_hint_given": True},
                metadata={"intervention": "stagnation_detected"}
            )
```

## 3. 异常处理通用原则

### 3.1 用户体验原则
```python
UX_PRINCIPLES = {
    "温和优先": "永远不要让用户感到被批评或责备",
    "教育性": "把异常转化为学习机会",
    "透明度": "如果系统出错,诚实告知但提供解决方案",
    "鼓励性": "即使用户犯错,也要保持积极态度",
    "灵活性": "允许用户以不同方式使用系统"
}
```

### 3.2 技术实现原则
```python
TECHNICAL_PRINCIPLES = {
    "防御性编程": "所有用户输入都可能是异常的",
    "优雅降级": "核心功能失败时有备用方案",
    "日志完整": "所有异常必须被记录以便调试",
    "快速恢复": "异常处理不应让用户等待过久",
    "幂等性": "异常恢复操作可重复执行"
}
```

## 4. 异常处理工具函数

### 4.1 统一异常包装器
```python
def safe_module_call(module: ModuleInterface, context: InterviewContext) -> ModuleResponse:
    """
    包装所有模块调用,统一处理异常
    """
    try:
        # 前置验证
        if not module.validate_context(context):
            raise StateInconsistencyException("Context validation failed")
        
        # 执行模块
        response = module.process(context)
        
        # 后置验证
        if not validate_response(response):
            raise ValueError("Invalid module response format")
        
        return response
    
    except LLMCallException as e:
        return LLMCallException.handle(e, context)
    
    except StateInconsistencyException as e:
        return StateInconsistencyException.handle(context, str(e))
    
    except Exception as e:
        # 未预期的异常,记录并返回通用错误响应
        log_error(f"Unexpected exception in {module.__class__.__name__}: {e}")
        return ModuleResponse(
            success=False,
            assistant_message="I encountered an unexpected issue. Let's continue from where we left off.",
            next_stage=None,
            context_updates={},
            error_message=str(e),
            metadata={"level": ExceptionLevel.CRITICAL}
        )
```

### 4.2 用户输入验证器
```python
def validate_user_input(user_input: str, context: InterviewContext) -> Tuple[bool, Optional[str]]:
    """
    验证用户输入,返回(是否有效, 异常类型)
    """
    # 空输入
    if not user_input or user_input.strip() == "":
        return False, "empty"
    
    # 过短输入
    if len(user_input.strip()) < 5:
        return False, "too_short"
    
    # 检测重复输入
    recent_inputs = [msg.content for msg in context.conversation_history[-3:] if msg.role == "user"]
    if user_input in recent_inputs:
        return False, "repeated"
    
    # 使用简单关键词检测是否相关(避免调用LLM节省成本)
    problem_keywords = extract_keywords(context.problem_text)
    input_keywords = extract_keywords(user_input)
    
    if len(set(problem_keywords) & set(input_keywords)) == 0 and len(user_input) > 50:
        # 长输入但完全不相关
        return False, "off_topic"
    
    return True, None
```

### 4.3 异常日志记录
```python
import logging
from datetime import datetime

class ExceptionLogger:
    """统一的异常日志系统"""
    
    def __init__(self):
        self.logger = logging.getLogger("InterviewCoach")
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        fh = logging.FileHandler(f"logs/exceptions_{datetime.now().strftime('%Y%m%d')}.log")
        fh.setLevel(logging.WARNING)
        
        # 格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    
    def log_exception(self, 
                     exception_type: str, 
                     context: InterviewContext, 
                     error_message: str,
                     level: ExceptionLevel):
        """
        记录异常
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": context.session_id,
            "current_stage": context.current_stage.name,
            "exception_type": exception_type,
            "error_message": error_message,
            "level": level.name,
            "user_input": context.current_user_input,
            "context_snapshot": self._snapshot_context(context)
        }
        
        if level == ExceptionLevel.CRITICAL:
            self.logger.critical(log_entry)
        elif level == ExceptionLevel.ERROR:
            self.logger.error(log_entry)
        elif level == ExceptionLevel.WARNING:
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)
    
    def _snapshot_context(self, context: InterviewContext) -> dict:
        """创建上下文快照用于调试"""
        return {
            "identified_pattern": context.identified_pattern,
            "current_stage": context.current_stage.name,
            "conversation_length": len(context.conversation_history),
            "has_pseudocode": context.pseudocode is not None
        }
```

## 5. 异常恢复测试用例

### 5.1 必须通过的测试场景
```python
TEST_CASES = [
    {
        "name": "用户要求跳过核心阶段",
        "input": "Can we skip this part?",
        "current_stage": Stage.THOUGHT_ARTICULATION,
        "expected_behavior": "温和拒绝,解释重要性,保持当前阶段"
    },
    {
        "name": "连续3次无效输入",
        "input": [".", "?", "idk"],
        "expected_behavior": "触发帮助模式,提供更多引导"
    },
    {
        "name": "LLM API失败",
        "mock_error": "TimeoutError",
        "expected_behavior": "自动重试3次,失败后使用模板回复"
    },
    {
        "name": "用户表示沮丧",
        "input": "This is too hard, I give up",
        "expected_behavior": "情感支持 + 降低难度 + 更多提示"
    },
    {
        "name": "状态数据缺失",
        "missing_field": "identified_pattern",
        "expected_behavior": "尝试重建 或 回退到安全状态"
    }
]
```

## 6. 实施检查清单

### 第1天必须完成
- [ ] 定义所有异常类型的枚举/类
- [ ] 实现safe_module_call包装器
- [ ] 实现validate_user_input函数
- [ ] 编写5个核心异常处理策略的伪代码

### 第5-6天集成
- [ ] 在主编排器中使用safe_module_call
- [ ] 在每个模块的process方法中抛出明确的异常
- [ ] 添加ExceptionLogger到所有模块
- [ ] 测试至少10个异常场景

### 第7天验证
- [ ] 运行所有异常恢复测试用例
- [ ] 验证日志文件正确记录异常
- [ ] 用户测试时故意触发异常,检查体验
