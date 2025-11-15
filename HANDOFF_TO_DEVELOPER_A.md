# 🤝 给开发者A的交接指南

## 📋 交接检查清单

### 开发者B需要做的事
- [ ] 将所有文件发给开发者A (zip压缩或Git推送)
- [ ] 确认开发者A能成功运行 `python3 examples.py`
- [ ] 一起过一遍 `MODULE_INTERFACE_SPEC.md` (15分钟)
- [ ] 解答开发者A的任何疑问
- [ ] 确认第2天的接口约定

### 开发者A需要做的事
- [ ] 接收文件并解压到工作目录
- [ ] 运行 `python3 examples.py` 验证环境
- [ ] 阅读本文档 (20分钟)
- [ ] 阅读 `MODULE_INTERFACE_SPEC.md` 核心部分
- [ ] 开始实现主编排器

---

## 🚀 开发者A快速上手指南

### 第一步: 验证环境 (5分钟)

```bash
# 1. 进入项目目录
cd interview-coach-agent

# 2. 运行示例代码
python3 examples.py

# 3. 应该看到成功输出,没有错误
```

如果运行成功,说明基础环境OK! ✅

---

### 第二步: 理解核心概念 (10分钟)

#### 核心数据结构 (必读!)

**InterviewContext** - 这是系统的"记忆"
```python
from core_models import InterviewContext

# 包含了整个面试会话的所有信息:
context = InterviewContext(
    session_id="123",           # 会话ID
    problem_text="题目内容",     # 当前题目
    current_stage=Stage.XXX,    # 当前在哪个阶段
    conversation_history=[],     # 对话历史
    identified_pattern="DP",     # 识别出的题型
    # ... 还有很多其他字段
)
```

**ModuleResponse** - 这是模块的"回复"
```python
from core_models import ModuleResponse

# 所有模块都返回这个格式:
response = ModuleResponse(
    success=True,                      # 是否成功
    assistant_message="给用户的话",    # 回复内容
    next_stage=Stage.COMPLEXITY,       # 建议下一阶段
    context_updates={                  # 要更新的字段
        "identified_pattern": "DP"
    }
)
```

**重要规则**: 模块不能直接修改context,只能通过context_updates返回修改!

---

### 第三步: 实现主编排器 (你的核心任务!)

#### 主编排器的职责
```
┌─────────────────┐
│   用户输入      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   主编排器 (Orchestrator)   │  ← 你要实现这个!
│                             │
│  职责:                      │
│  1. 接收用户输入            │
│  2. 判断当前在哪个阶段      │
│  3. 选择对应的模块          │
│  4. 调用模块处理            │
│  5. 更新Context             │
│  6. 返回回复给用户          │
└─────────────────────────────┘
```

#### 实现模板 (复制这个开始!)

创建新文件 `orchestrator.py`:

```python
"""
主编排器 - 控制整个面试流程
作者: 开发者A
日期: Day 1-2
"""

from core_models import (
    InterviewContext, 
    ModuleResponse, 
    Stage,
    create_mock_context
)
from module_interface import ModuleInterface
from exception_handler import (
    ExceptionHandler,
    InputValidator,
    safe_module_call
)


class Orchestrator:
    """主编排器 - 系统的大脑"""
    
    def __init__(self):
        self.exception_handler = ExceptionHandler()
        self.input_validator = InputValidator()
        self.modules = {}  # 第2天会添加实际模块
    
    def register_module(self, name: str, module: ModuleInterface):
        """注册一个模块"""
        self.modules[name] = module
    
    def process_user_input(self, context: InterviewContext, user_input: str) -> str:
        """
        处理用户输入的主函数
        
        这是整个系统的核心循环!
        
        Args:
            context: 当前会话上下文
            user_input: 用户输入的内容
            
        Returns:
            str: 要返回给用户的消息
        """
        
        # ===== 步骤1: 验证输入 =====
        is_valid, error_type = self.input_validator.validate(user_input, context)
        
        if not is_valid:
            response = self.exception_handler.handle_invalid_input(context, error_type)
            return response.assistant_message
        
        # ===== 步骤2: 检测特殊请求 =====
        # 跳过请求
        if self.input_validator.detect_skip_request(user_input):
            response = self.exception_handler.handle_skip_request(context)
            return response.assistant_message
        
        # 沮丧情绪
        if self.input_validator.detect_frustration(user_input):
            response = self.exception_handler.handle_frustration(context)
            return response.assistant_message
        
        # ===== 步骤3: 更新用户输入到context =====
        context.current_user_input = user_input
        context.add_message("user", user_input)
        
        # ===== 步骤4: 选择要激活的模块 =====
        active_module = self._select_module(context)
        
        if not active_module:
            # 没有模块匹配,给个默认回复
            return "I'm not sure how to help with that. Could you clarify?"
        
        # ===== 步骤5: 调用模块 =====
        response = safe_module_call(active_module, context, self.exception_handler)
        
        if not response.success:
            # 模块执行失败,已经由safe_module_call处理过了
            return response.assistant_message
        
        # ===== 步骤6: 更新context =====
        self._update_context(context, response)
        
        # ===== 步骤7: 记录助手回复 =====
        context.add_message("assistant", response.assistant_message)
        
        # ===== 步骤8: 返回回复 =====
        return response.assistant_message
    
    def _select_module(self, context: InterviewContext) -> ModuleInterface:
        """
        根据当前阶段选择要激活的模块
        
        这里是你需要实现的核心逻辑!
        """
        for module in self.modules.values():
            if module.should_activate(context):
                return module
        
        return None
    
    def _update_context(self, context: InterviewContext, response: ModuleResponse):
        """
        根据模块返回的response更新context
        
        重要: 这是唯一应该修改context的地方!
        """
        # 更新所有字段
        for key, value in response.context_updates.items():
            setattr(context, key, value)
        
        # 如果需要转换阶段
        if response.next_stage and response.next_stage != context.current_stage:
            context.transition_to(response.next_stage)


# ===== 测试代码 =====
def test_orchestrator():
    """测试主编排器是否工作"""
    
    print("=== 测试主编排器 ===\n")
    
    # 1. 创建编排器
    orchestrator = Orchestrator()
    
    # 2. 创建测试上下文
    context = create_mock_context(
        problem_text="Given an array, find two sum."
    )
    
    # 3. 测试各种输入
    test_inputs = [
        "",  # 空输入
        "skip",  # 跳过请求
        "I understand the problem",  # 正常输入
    ]
    
    for user_input in test_inputs:
        print(f"用户输入: '{user_input}'")
        reply = orchestrator.process_user_input(context, user_input)
        print(f"助手回复: {reply}\n")


if __name__ == "__main__":
    test_orchestrator()
```

---

### 第四步: 运行你的编排器 (5分钟)

```bash
# 创建orchestrator.py后运行
python3 orchestrator.py

# 应该能看到测试输出
```

---

### 第五步: 集成你的第一个模块 (第2天)

当你实现了题型识别模块后,这样集成:

```python
# 在你的recognizer.py中
from module_interface import ProblemTypeRecognizer
from core_models import ModuleResponse, Stage

class MyRecognizer(ProblemTypeRecognizer):
    
    def process(self, context):
        # 你的识别逻辑
        problem = context.problem_text
        
        # 简单示例
        if "array" in problem.lower():
            pattern = "Array问题"
        else:
            pattern = "一般问题"
        
        return ModuleResponse(
            success=True,
            assistant_message=f"这是一个{pattern}!",
            next_stage=Stage.THOUGHT_ARTICULATION,
            context_updates={"identified_pattern": pattern},
            metadata={}
        )
    
    def should_activate(self, context):
        return context.current_stage == Stage.PROBLEM_CLARIFICATION

# 在orchestrator.py中注册
from recognizer import MyRecognizer

orchestrator = Orchestrator()
orchestrator.register_module("recognizer", MyRecognizer())
```

---

## 📖 重要文档阅读清单

### 必读 (第1天晚上读完)
1. **本文档** - 快速上手
2. **MODULE_INTERFACE_SPEC.md** 的第1-3节 - 理解数据结构和接口
3. **examples.py** 的`example_for_developer_a()`函数 - 看使用示例

### 可选 (遇到问题时查阅)
4. **EXCEPTION_HANDLING_STRATEGY.md** - 了解异常处理
5. **DAY1_DEVELOPER_B_SUMMARY.md** - 查看B的工作总结

---

## 🔧 常见问题 FAQ

### Q1: 我在哪里实现状态转换逻辑?
**A**: 在`orchestrator.py`的`_update_context`方法中。模块会通过`response.next_stage`建议下一阶段,你决定是否接受。

### Q2: 如何调试模块调用?
**A**: 
```python
# 在orchestrator.py中添加日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看context状态
print(f"当前阶段: {context.current_stage}")
print(f"识别的模式: {context.identified_pattern}")
```

### Q3: 模块返回的response里有什么?
**A**: 
```python
response.success           # 是否成功
response.assistant_message # 给用户的回复
response.next_stage       # 建议的下一阶段
response.context_updates  # 要更新的字段
response.metadata         # 调试信息
response.error_message    # 如果失败,错误信息
```

### Q4: 如何测试我的代码?
**A**: 
```python
# 使用create_mock_context创建测试数据
from core_models import create_mock_context

context = create_mock_context(
    problem_text="测试题目",
    current_stage=Stage.PROBLEM_CLARIFICATION
)

# 然后测试你的逻辑
```

### Q5: 开发者B的代码我需要改吗?
**A**: **不需要!** 开发者B已经完成的文件你只需要**使用**,不要修改:
- ✅ 使用: `core_models.py`, `module_interface.py`, `exception_handler.py`
- ❌ 不要改动这些文件
- ✅ 你专注实现: `orchestrator.py`, `state_machine.py`, `recognizer.py`, `thought_coach.py`

---

## 🎯 你的第1-2天任务清单

### Day 1下午 (今天剩余时间)
- [ ] 收到所有文件
- [ ] 运行 `examples.py` 验证环境
- [ ] 创建 `orchestrator.py` 文件
- [ ] 复制上面的模板代码
- [ ] 运行测试,确保能工作

### Day 2全天
- [ ] 实现完整的主控制循环
- [ ] 实现状态转换逻辑
- [ ] 定义7个阶段的转换规则
- [ ] 创建 `state_machine.py` (可选,也可以写在orchestrator里)
- [ ] 与开发者B晚上同步

---

## 💡 设计建议

### 建议1: 先简单后复杂
```python
# 第1天: 先实现最简单的线性流程
def _select_module(self, context):
    # 简单映射
    stage_to_module = {
        Stage.PROBLEM_CLARIFICATION: self.modules.get("recognizer"),
        Stage.THOUGHT_ARTICULATION: self.modules.get("thought_coach"),
        # ...
    }
    return stage_to_module.get(context.current_stage)

# 第3天: 再优化成智能选择
def _select_module(self, context):
    # 复杂的条件判断...
    pass
```

### 建议2: 用日志追踪状态
```python
def process_user_input(self, context, user_input):
    logger.info(f"[{context.session_id}] Stage={context.current_stage}, Input={user_input[:50]}")
    # ... 处理逻辑
    logger.info(f"[{context.session_id}] Next Stage={response.next_stage}")
```

### 建议3: 写小的辅助函数
```python
def _should_transition(self, context, next_stage):
    """判断是否应该转换到下一阶段"""
    # 检查前置条件
    if next_stage == Stage.COMPLEXITY_ANALYSIS:
        return context.user_approach is not None
    return True
```

---

## 🤝 协作方式

### 每日同步 (晚上6点,30分钟)
**讨论内容:**
1. 今天完成了什么
2. 遇到什么问题
3. 接口有没有需要调整的
4. 明天的计划

### Slack/微信沟通
- 🚨 **紧急问题**: 随时沟通
- 💬 **一般问题**: 工作时间内1小时内回复
- 📋 **接口变更**: 必须双方确认后才能修改

### Git使用规范(如果用Git)
```bash
# 开发者A的分支
git checkout -b feature/orchestrator
git commit -m "feat: 实现主编排器基础功能"

# 开发者B的分支  
git checkout -b feature/exception-handler
git commit -m "feat: 完成异常处理系统"

# 合并前必须双方review
```

---

## 📞 遇到问题怎么办?

### 场景1: 看不懂某个数据结构
👉 查看 `MODULE_INTERFACE_SPEC.md` 或直接问开发者B

### 场景2: 不知道怎么调用模块
👉 看 `examples.py` 的 `example_for_developer_a()` 函数

### 场景3: 报错了不知道怎么办
👉 查看 `EXCEPTION_HANDLING_STRATEGY.md` 或运行调试

### 场景4: 想改接口但不确定
👉 **先问开发者B!** 不要自己改,可能会影响B的工作

---

## ✅ 交接完成检查

开发者A确认以下所有项后,交接即完成:

- [ ] 能成功运行 `python3 examples.py`
- [ ] 理解了 InterviewContext 和 ModuleResponse
- [ ] 知道如何使用 safe_module_call
- [ ] 创建了 orchestrator.py 并能运行
- [ ] 知道如何注册和调用模块
- [ ] 清楚第2天要做什么

---

**祝开发顺利! 有问题随时找开发者B! 🚀**
