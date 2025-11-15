"""
开发者B第1天交付物使用示例
展示如何使用已定义的接口和异常处理系统
"""

from core_models import (
    InterviewContext, 
    ModuleResponse, 
    Stage,
    create_mock_context,
    create_success_response
)
from module_interface import (
    ModuleInterface,
    ProblemTypeRecognizer,
    CodeEdgeCaseReviewer
)
from exception_handler import (
    ExceptionHandler,
    InputValidator,
    safe_module_call
)


# ==================== 示例1: 使用Mock Context ====================

def example_create_context():
    """示例:创建测试用的上下文"""
    
    # 方法1: 使用工厂函数
    context = create_mock_context(
        problem_text="Given an array nums, find two numbers that add up to target.",
        current_stage=Stage.PROBLEM_CLARIFICATION,
        session_id="demo_001"
    )
    
    print("=== Mock Context Created ===")
    print(f"Session ID: {context.session_id}")
    print(f"Current Stage: {context.current_stage}")
    print(f"Problem: {context.problem_text}")
    
    return context


# ==================== 示例2: 实现一个简单模块 ====================

class SimpleRecognizer(ProblemTypeRecognizer):
    """
    示例:开发者B实现的简单题型识别模块
    这个是给开发者B看的,展示如何继承接口并实现
    """
    
    def process(self, context: InterviewContext) -> ModuleResponse:
        """识别题目类型并给出线索"""
        
        problem = context.problem_text.lower()
        
        # 简单的关键词匹配(真实实现会用LLM)
        if "two sum" in problem or "add up to" in problem:
            pattern = "Hash Table / Two Pointer"
            complexity = "O(n) time, O(n) space with hash table"
            hint = "Think about: if you've seen a number before, how would you remember it?"
            
        elif "sorted array" in problem:
            pattern = "Binary Search / Two Pointer"
            complexity = "O(log n) for binary search"
            hint = "The array is sorted - how can we take advantage of that?"
            
        else:
            pattern = "General Problem Solving"
            complexity = "Start with brute force, then optimize"
            hint = "Let's start by understanding what we need to do."
        
        return create_success_response(
            message=f"I notice this looks like a **{pattern}** problem. {hint}",
            next_stage=Stage.THOUGHT_ARTICULATION,
            identified_pattern=pattern,
            complexity_expectation=complexity
        )
    
    def should_activate(self, context: InterviewContext) -> bool:
        """只在题意确认阶段激活"""
        return context.current_stage == Stage.PROBLEM_CLARIFICATION
    
    def validate_context(self, context: InterviewContext) -> bool:
        """检查是否有题目文本"""
        return bool(context.problem_text and context.problem_text.strip())


# ==================== 示例3: 使用异常处理 ====================

def example_exception_handling():
    """示例:如何使用异常处理器"""
    
    handler = ExceptionHandler()
    validator = InputValidator()
    context = create_mock_context()
    
    # 测试各种用户输入
    test_inputs = [
        ("", "空输入"),
        ("ok", "过短输入"),
        ("This is too hard, I give up!", "沮丧情绪"),
        ("Can we skip this part?", "跳过请求"),
        ("Let me think about using a hash table", "正常输入")
    ]
    
    print("\n=== Exception Handling Examples ===")
    
    for user_input, description in test_inputs:
        print(f"\n输入: '{user_input}' ({description})")
        
        # 1. 验证输入
        is_valid, error_type = validator.validate(user_input, context)
        
        if not is_valid:
            response = handler.handle_invalid_input(context, error_type)
            print(f"处理结果: {response.assistant_message}")
            continue
        
        # 2. 检测特殊请求
        if validator.detect_skip_request(user_input):
            response = handler.handle_skip_request(context)
            print(f"跳过请求: {response.assistant_message}")
            continue
        
        if validator.detect_frustration(user_input):
            response = handler.handle_frustration(context)
            print(f"情绪支持: {response.assistant_message}")
            continue
        
        print("✓ 正常输入,可以继续处理")


# ==================== 示例4: 安全调用模块 ====================

def example_safe_module_call():
    """示例:如何安全地调用模块"""
    
    context = create_mock_context(
        problem_text="Find two numbers in an array that add up to a target."
    )
    
    # 创建模块和异常处理器
    recognizer = SimpleRecognizer()
    handler = ExceptionHandler()
    
    print("\n=== Safe Module Call Example ===")
    
    # 使用safe_module_call包装器
    response = safe_module_call(recognizer, context, handler)
    
    if response.success:
        print(f"✓ 模块执行成功")
        print(f"助手回复: {response.assistant_message}")
        print(f"下一阶段: {response.next_stage}")
        print(f"Context更新: {response.context_updates}")
    else:
        print(f"✗ 模块执行失败: {response.error_message}")


# ==================== 示例5: 开发者A如何使用这些接口 ====================

def example_for_developer_a():
    """
    示例:开发者A在主编排器中如何使用开发者B的接口
    这展示了两位开发者的协作方式
    """
    
    print("\n=== Developer A Usage Example ===")
    
    # 开发者A会这样使用:
    context = create_mock_context()
    context.current_user_input = "I think we can use a hash table"
    
    # 1. 创建一个示例模块(实际开发时会从modules/目录导入)
    recognizer = SimpleRecognizer()
    
    # 2. 检查模块是否应该激活
    if recognizer.should_activate(context):
        print(f"当前阶段: {context.current_stage}")
        print(f"模块 '{recognizer.module_name}' 应该被激活")
        
        # 3. 安全调用模块
        handler = ExceptionHandler()
        response = safe_module_call(recognizer, context, handler)
        
        # 4. 更新context
        if response.success:
            for key, value in response.context_updates.items():
                setattr(context, key, value)
            
            if response.next_stage:
                context.transition_to(response.next_stage)
            
            print(f"\n✓ Context已更新")
            print(f"识别的模式: {context.identified_pattern}")
            print(f"新阶段: {context.current_stage}")
            print(f"助手回复: {response.assistant_message}")
    else:
        print("模块不应该在当前阶段激活")


# ==================== 运行所有示例 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("开发者B第1天交付物 - 使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_create_context()
    example_exception_handling()
    example_safe_module_call()
    example_for_developer_a()
    
    print("\n" + "=" * 60)
    print("所有示例执行完毕!")
    print("开发者A可以参考example_for_developer_a()来使用这些接口")
    print("=" * 60)
