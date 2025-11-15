# 算法面试教练Agent - 模块交互协议与异常处理系统

> 📖 **文档说明**: 本文档介绍系统的核心架构设计,包括模块间如何通信、数据如何流转、以及如何优雅处理各种异常情况。

---

## 🎯 一、系统概述

### 1.1 这是什么?

这是一个**模拟真实技术面试**的AI教练系统。不同于直接给答案的刷题网站,我们的系统像真实面试官一样:
- 引导你说出解题思路
- 检查你的代码逻辑
- 追问优化方案
- 在7个标准阶段中训练你的面试技能

### 1.2 核心设计理念

**模块化架构** - 把复杂系统拆分成独立的"专家"模块:

```
         主编排器 (大脑)
              │
    ┌─────────┼─────────┬─────────┐
    │         │         │         │
 题型识别   思路教练    代码检查   追问生成
  专家       专家       专家       专家
```

每个模块:
- ✅ 只负责一件事
- ✅ 通过统一接口通信
- ✅ 可以独立开发和测试
- ✅ 可以随时添加新模块

---

## 🏗️ 二、核心架构

### 2.1 七个面试阶段

模拟真实技术面试的完整流程:

```
阶段0: 题意确认 ──→ "你理解题目要求吗?"
  ↓
阶段1: 思路口述 ──→ "说说你的解题想法"
  ↓
阶段2: 复杂度分析 ──→ "时间和空间复杂度是多少?"
  ↓
阶段3: 伪代码设计 ──→ "写出主要的代码逻辑"
  ↓
阶段4: 边界检查 ──→ "考虑过空数组的情况吗?"
  ↓
阶段5: Follow-up ──→ "能进一步优化吗?"
  ↓
阶段6: 套路总结 ──→ "这题用了什么经典模式?"
```

**为什么这样设计?**
- 这是Google/Meta等公司面试的标准流程
- 训练完整的解题思维链条
- 培养清晰的技术表达能力

### 2.2 模块职责划分

四个核心"专家"模块:

| 模块 | 负责阶段 | 核心职责 |
|------|---------|---------|
| 🔍 题型识别 | 阶段0 | 识别题目类型,给出解题线索 |
| 💭 思路教练 | 阶段1-2 | 引导用户从暴力解到优化解 |
| 🔬 代码检查 | 阶段3-4 | 检查逻辑漏洞,生成边界测试 |
| 🚀 追问生成 | 阶段5 | 提出优化方向和变体问题 |

---

## 🧩 三、核心数据结构

### 3.1 InterviewContext - 系统的"记忆"

把它想象成一个**会话的完整档案**,记录着面试过程中发生的一切:

#### 它包含什么?

**📍 位置信息**
```python
current_stage: Stage              # 现在在第几步?
stage_history: List[Stage]        # 已经走过哪些步骤?
```

**📝 题目信息**
```python
problem_text: str                 # 题目原文
problem_metadata: Dict            # 难度、标签等元数据
```

**💬 对话记录**
```python
conversation_history: List[Message]  # 完整的对话历史
current_user_input: str              # 当前用户说了什么
```

**🎯 分析结果** (各模块产生的信息)
```python
identified_pattern: str           # 识别出的题型 (如"动态规划")
complexity_expectation: str       # 期望的复杂度范围
user_approach: str                # 用户的解题思路
pseudocode: str                   # 用户写的伪代码
detected_issues: List[str]        # 发现的潜在问题
```

#### 为什么需要这个结构?

想象真实面试:
- 面试官会**记住**你之前说的话
- 基于你的回答**调整**后续问题
- 最后给出**综合评价**

Context就是这个"记忆系统"!

**关键规则:**
```
⚠️ 模块不能直接修改Context!
✅ 只能通过Response的context_updates返回修改建议
```

### 3.2 ModuleResponse - 模块的统一回复格式

每个模块处理完后,返回这个**标准格式**:

```python
ModuleResponse(
    success: bool,              # ✓ 处理成功还是失败?
    assistant_message: str,     # 💬 要对用户说什么?
    next_stage: Stage,          # ➡️  建议进入哪个阶段?
    context_updates: Dict,      # 📝 需要更新哪些信息?
    metadata: Dict              # 📊 调试信息 (给开发者看)
)
```

#### 实际例子

**场景:** 用户说"我想用hash table"

```python
# 思路教练模块返回:
ModuleResponse(
    success=True,
    assistant_message="Great! Hash table is a good direction. "
                     "What would be the time complexity of this approach?",
    next_stage=Stage.COMPLEXITY_ANALYSIS,
    context_updates={
        "user_approach": "Hash Table方法"
    },
    metadata={"confidence": 0.9}
)
```

**为什么用统一格式?**
- 主编排器不需要知道每个模块内部怎么工作
- 像USB接口一样:不管什么设备,插上就能用
- 便于添加新模块,不影响现有代码

---

## 🔌 四、模块接口设计

### 4.1 抽象基类 - 所有模块的"契约"

所有专家模块必须实现这两个方法:

```python
class ModuleInterface:
    """所有模块的基础模板"""
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        """
        核心方法: 处理当前情况,给出回复
        
        输入: 当前的会话状态
        输出: 标准格式的回复
        
        就像问"老板让我干活,我该怎么做?"
        """
        pass
    
    def should_activate(self, context: InterviewContext) -> bool:
        """
        判断: 我是否应该在当前情况下出场?
        
        就像问"这个任务是我该干的吗?"
        
        例如:
        - 题型识别专家只在"题意确认"阶段工作
        - 代码检查专家只在"写代码"阶段工作
        """
        pass
```

### 4.2 四大模块详解

#### 🔍 模块1: 题型识别 (ProblemTypeRecognizer)

**工作场景:**
```
用户输入题目: 
"给定一个数组,找两个数之和等于target"

↓ 模块分析 ↓

关键词: 数组、两个数、目标值
可能模式: Hash Table / 双指针
复杂度期望: O(n) time, O(n) or O(1) space

↓ 输出回复 ↓

"I notice this is a classic search problem. 
 Think about: if you've already seen a number, 
 how would you remember it for later?"
```

**核心原则:**
- ❌ 不直接告诉用户"用Hash Table"
- ✅ 给线索:"如何记住已经看过的数字?"
- ❌ 不给出完整代码
- ✅ 引导思考方向

**激活条件:**
```python
def should_activate(self, context):
    return context.current_stage == Stage.PROBLEM_CLARIFICATION
```

#### 💭 模块2: 思路教练 (GuidedThoughtGenerator)

**工作场景:**
```
用户: "我想遍历数组两次,用两个for循环"

↓ 模块判断 ↓

识别: 这是暴力解法 O(n²)
方向: 可行,但可以优化
策略: 不直接否定,而是引导思考

↓ 分层提示 ↓

第1层: "这个方法可以work!但复杂度是多少?"
第2层: "有没有办法在一次遍历中完成?"
第3层: "想想:我们需要快速查找,什么数据结构擅长这个?"
```

**核心技巧:**
- 🎯 苏格拉底式提问 (问题引导,不直接告知)
- 📊 分层提示 (由浅入深,逐步加强)
- 🔄 思路纠偏 (温和地调整方向)

**激活条件:**
```python
def should_activate(self, context):
    return context.current_stage in [
        Stage.THOUGHT_ARTICULATION,
        Stage.COMPLEXITY_ANALYSIS
    ]
```

#### 🔬 模块3: 代码检查 (CodeEdgeCaseReviewer)

**工作场景:**
```
用户提交伪代码:
for i in range(len(arr)):
    if arr[i] == target:
        return i

↓ 模块检查 ↓

主逻辑: ✓ 基本正确
潜在问题:
  - arr为空数组? ❌ 会出错
  - target不存在? ❌ 没有返回值
  - 数组中有None? ❌ 比较会失败

↓ 引导提问 ↓

"Your code looks good for the happy path! 
 Let me ask you a few questions:
 1. What happens if the array is empty?
 2. What should we return if target is not found?
 3. Could there be any None values in the array?"
```

**核心方法:**
- 🧪 "干跑"代码 (心算模拟执行)
- 🎯 常见错误识别 (空指针、越界、类型错误)
- ❓ 问题式引导 (不直接说错,而是问"如果...会怎样?")

**激活条件:**
```python
def should_activate(self, context):
    return context.current_stage in [
        Stage.PSEUDOCODE_DESIGN,
        Stage.EDGE_CASE_CHECK
    ]
```

#### 🚀 模块4: 追问生成 (FollowUpGenerator)

**工作场景:**
```
用户完成基础解法: Hash Table, O(n) time, O(n) space

↓ 生成追问方向 ↓

方向1: 优化空间
  "Can you solve it with O(1) extra space?"

方向2: 题目变体
  "What if we need to find three numbers that sum to target?"

方向3: 特殊情况
  "How would you handle duplicate values in the array?"

方向4: 实际应用
  "If the array is sorted, could we do better?"
```

**追问策略:**
- 💡 基于题型的问题库
- 📈 难度递进式追问
- 🔄 引导到相关题目家族

**激活条件:**
```python
def should_activate(self, context):
    return context.current_stage == Stage.FOLLOW_UP
```

---

## ⚙️ 五、系统工作流程

### 5.1 完整的处理循环

```
1. 用户输入
   "I think we can use a hash table"
   
   ↓
   
2. 输入验证
   ✓ 不是空白
   ✓ 长度合理 (>5字符)
   ✓ 不是重复内容
   
   ↓
   
3. 特殊情况检测
   □ 想跳过某步? → 根据阶段决定是否允许
   □ 表示沮丧? → 情感支持 + 降低难度
   □ 要直接答案? → 解释为什么要自己思考
   
   ↓
   
4. 选择合适模块
   当前阶段: THOUGHT_ARTICULATION
   → 激活"思路教练"模块
   
   ↓
   
5. 模块处理
   思路教练分析:
   - 用户提到Hash Table ✓
   - 这是正确方向 ✓
   - 生成下一层引导
   
   ↓
   
6. 更新Context
   通过context_updates更新:
   - user_approach = "Hash Table"
   - current_stage = COMPLEXITY_ANALYSIS
   
   ↓
   
7. 返回回复
   "Great! Hash table is an excellent approach.
    Now, what would be the time and space complexity?"
```

### 5.2 状态转换规则

**什么时候可以进入下一阶段?**

每个阶段都有"前置条件":

```python
阶段0 → 阶段1: 题意确认 → 思路口述
条件: identified_pattern 不为空
解释: 必须先识别出题型,才能讨论思路

阶段1 → 阶段2: 思路口述 → 复杂度分析  
条件: user_approach 不为空
解释: 必须说出解题思路,才能分析复杂度

阶段2 → 阶段3: 复杂度分析 → 伪代码设计
条件: 用户输入包含"complexity"相关内容
解释: 必须讨论过复杂度,才能开始写代码

阶段3 → 阶段4: 伪代码设计 → 边界检查
条件: pseudocode 不为空
解释: 必须先有代码,才能检查边界

阶段4 → 阶段5: 边界检查 → Follow-up
条件: 完成边界讨论
解释: 基础功能完成后,才能深入探讨
```

**为什么要有这些条件?**
- 确保不跳过关键步骤
- 模拟真实面试的严谨性
- 训练系统化的解题习惯

---

## 🛡️ 六、异常处理系统

### 6.1 设计原则

**用户体验第一:**

```
温和优先  → 永远不批评用户
教育性    → 把错误变成学习机会
透明度    → 诚实告知,但提供解决方案
鼓励性    → 保持积极正向的氛围
灵活性    → 允许用户以不同方式使用
```

### 6.2 常见异常场景

#### 场景1: 想跳过某个阶段

**核心阶段** (不允许跳过):
- 思路口述
- 伪代码设计  
- 边界检查

**可选阶段** (允许跳过):
- 复杂度分析
- 套路总结

**处理方式:**
```python
用户: "Can we skip this part?"

系统判断:
if 当前阶段 in 核心阶段:
    回复: "I understand you want to move forward, but this 
           stage is crucial for interview success. Let's 
           spend just 2-3 minutes on this?"
    
else:  # 可选阶段
    回复: "Okay, we can move on. But remember, in real 
           interviews, discussing complexity shows analytical 
           maturity. Let's continue."
    允许跳过 ✓
```

#### 场景2: 检测到沮丧情绪

**触发词:**
- "too hard", "太难"
- "give up", "放弃"
- "don't know", "不会"

**处理流程:**
```
1. 情感支持
   "I can tell this is challenging, and that's 
    completely normal! Even experienced engineers 
    struggle with these problems."

2. 降低难度
   - 提供更详细的提示
   - 分解成更小的步骤
   - 给出思考框架

3. 提供选择
   "Would you like:
    a) A stronger hint to continue
    b) Try a simpler problem first"
```

#### 场景3: 无效输入处理

**检测类型:**

```python
空输入: ""
→ "I didn't catch that. Could you share your thoughts?"

过短: "ok" (< 5字符)
→ "That's a bit brief! Could you elaborate?"

重复: 和前3条消息一样
→ "I notice you've said something similar. 
   Want to try a different angle?"

离题: 完全不相关的内容
→ "Hmm, that seems unrelated. Let me rephrase 
   the question..."
```

**连续3次无效?**
```
第1次 → 温和提示
第2次 → 再次提示  
第3次 → 触发帮助模式
      → "I notice you might be stuck. Let me 
          give you a more detailed hint..."
```

#### 场景4: LLM调用失败

**重试机制:**
```
第1次失败 → 等2秒,重试
第2次失败 → 等4秒,重试
第3次失败 → 等8秒,重试
第4次失败 → 使用降级模板
```

**降级模板示例:**
```python
阶段1 (思路口述):
"Let's think about this step by step. What would 
 be the simplest approach to solve this problem?"

阶段3 (伪代码):
"Now let's write out the main logic structure of 
 your solution."

阶段4 (边界检查):
"What edge cases should we consider? Think about 
 empty inputs, extreme values, etc."
```

### 6.3 安全调用包装器

所有模块调用都通过`safe_module_call`包装:

```python
def safe_module_call(module, context, handler):
    """统一的异常处理包装器"""
    
    try:
        # 1. 前置验证
        if not module.validate_context(context):
            raise StateInconsistencyException
        
        # 2. 执行模块
        response = module.process(context)
        
        # 3. 后置验证
        if not validate_response(response):
            raise ValueError("Invalid response format")
        
        return response
        
    except LLMCallException as e:
        # LLM失败 → 重试或降级
        return handler.handle_llm_failure(e, context)
        
    except StateInconsistencyException as e:
        # 状态不一致 → 尝试恢复或回退
        return handler.handle_state_error(context)
        
    except Exception as e:
        # 未知错误 → 记录日志,返回通用错误
        log_error(f"Unexpected error: {e}")
        return create_error_response(e)
```

**为什么需要这个?**
- 统一的错误处理逻辑
- 保证用户体验不中断
- 完整的错误日志记录
- 便于调试和监控

---

## 🔧 七、开发者指南

### 7.1 如何添加新模块?

**3步快速上手:**

```python
# 步骤1: 继承基类
from module_interface import ModuleInterface

class MyNewModule(ModuleInterface):
    """你的新模块"""
    
    # 步骤2: 实现should_activate
    def should_activate(self, context):
        """我什么时候该工作?"""
        return context.current_stage == Stage.MY_STAGE
    
    # 步骤3: 实现process
    def process(self, context):
        """我该怎么工作?"""
        
        # 读取信息
        user_input = context.current_user_input
        
        # 处理逻辑
        result = my_logic(user_input)
        
        # 返回标准格式
        return ModuleResponse(
            success=True,
            assistant_message="你要说的话",
            next_stage=Stage.NEXT,
            context_updates={"new_field": result}
        )
```

就这么简单!

### 7.2 黄金规则 (必须遵守!)

**✅ 允许做:**
- 读取context的任何字段
- 返回任何你想说的话
- 调用工具函数
- 记录日志

**❌ 禁止做:**
```python
# ❌ 错误: 直接修改context
context.identified_pattern = "DP"

# ✅ 正确: 通过context_updates返回
return ModuleResponse(
    context_updates={"identified_pattern": "DP"}
)
```

**为什么?**
- 所有修改可追踪
- 避免并发问题
- 便于调试和回滚
- 主编排器统一管理状态

### 7.3 调试技巧

**查看当前状态:**
```python
print(f"当前阶段: {context.current_stage.name}")
print(f"识别题型: {context.identified_pattern}")
print(f"对话条数: {len(context.conversation_history)}")
```

**检查模块激活:**
```python
module = MyModule()
is_active = module.should_activate(context)
print(f"模块是否激活: {is_active}")
```

**使用辅助函数:**
```python
from core_models import create_success_response

# 快速创建响应
response = create_success_response(
    message="你的回复",
    next_stage=Stage.NEXT,
    field_name="field_value"
)
```

---

## 📚 八、快速开始

### 8.1 环境准备

```bash
# 1. 确保有Python 3.8+
python --version

# 2. 创建logs目录
mkdir logs

# 3. 运行测试
python examples.py
```

### 8.2 第一个示例

```python
from core_models import create_mock_context, Stage
from module_interface import ModuleInterface
from core_models import ModuleResponse

# 1. 创建一个简单模块
class SimpleModule(ModuleInterface):
    
    def should_activate(self, context):
        return context.current_stage == Stage.PROBLEM_CLARIFICATION
    
    def process(self, context):
        return ModuleResponse(
            success=True,
            assistant_message="Hello! Let's solve this together.",
            next_stage=Stage.THOUGHT_ARTICULATION,
            context_updates={},
            metadata={}
        )

# 2. 创建测试上下文
context = create_mock_context(
    problem_text="Find two numbers that sum to target"
)

# 3. 测试模块
module = SimpleModule()
if module.should_activate(context):
    response = module.process(context)
    print(response.assistant_message)
```

---



