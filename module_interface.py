"""
模块接口定义
所有子模块必须继承ModuleInterface并实现其方法
作者: 开发者B
日期: Day 1
"""

from abc import ABC, abstractmethod
from core_models import InterviewContext, ModuleResponse


class ModuleInterface(ABC):
    """
    所有子模块必须实现的接口
    
    设计原则:
    1. 模块不应直接修改context,而是通过返回context_updates
    2. 模块应该是无状态的(所有状态都在context中)
    3. 模块之间不应该互相调用
    """
    
    def __init__(self, module_name: str):
        """
        Args:
            module_name: 模块名称,用于日志和调试
        """
        self.module_name = module_name
    
    @abstractmethod
    def process(self, context: InterviewContext) -> ModuleResponse:
        """
        处理当前上下文,生成回复
        
        这是模块的核心方法,必须实现
        
        Args:
            context: 当前会话上下文
            
        Returns:
            ModuleResponse: 包含回复内容和状态更新
            
        注意:
        - 不要直接修改context对象
        - 所有对context的修改通过返回的context_updates字典
        - 如果遇到错误,返回success=False的响应
        """
        pass
    
    @abstractmethod
    def should_activate(self, context: InterviewContext) -> bool:
        """
        判断该模块是否应该在当前状态下激活
        
        由主编排器调用,用于决定哪个模块处理当前请求
        
        Args:
            context: 当前会话上下文
            
        Returns:
            bool: True表示应该激活该模块
            
        示例:
            # ProblemTypeRecognizer只在PROBLEM_CLARIFICATION阶段激活
            return context.current_stage == Stage.PROBLEM_CLARIFICATION
        """
        pass
    
    def validate_context(self, context: InterviewContext) -> bool:
        """
        验证上下文是否满足该模块的前置条件
        
        可选实现,默认返回True
        子类可以重写此方法来检查必要的字段是否存在
        
        Args:
            context: 当前会话上下文
            
        Returns:
            bool: True表示前置条件满足
            
        示例:
            # CodeReviewer需要pseudocode字段存在
            return context.pseudocode is not None
        """
        return True
    
    def get_module_info(self) -> dict:
        """
        返回模块的元信息
        用于调试和监控
        """
        return {
            "name": self.module_name,
            "class": self.__class__.__name__,
            "activated_stages": self._get_activated_stages()
        }
    
    def _get_activated_stages(self) -> list:
        """
        子类可以重写,说明自己在哪些阶段会被激活
        用于文档和调试
        """
        return []


# ==================== 四大核心模块接口定义 ====================

class ProblemTypeRecognizer(ModuleInterface):
    """
    题型识别与套路归纳模块
    
    职责:
    - 识别题目类型(DP/图/滑窗/双指针等)
    - 生成解题线索(不直接给答案)
    - 判断合理的复杂度期望范围
    
    激活时机: Stage.PROBLEM_CLARIFICATION
    前置条件: problem_text不为空
    输出: 更新context.identified_pattern, context.complexity_expectation
    """
    
    def __init__(self):
        super().__init__("ProblemTypeRecognizer")
    
    def _get_activated_stages(self):
        from core_models import Stage
        return [Stage.PROBLEM_CLARIFICATION]


class GuidedThoughtGenerator(ModuleInterface):
    """
    引导式思路教练模块
    
    职责:
    - 生成分层提示(由浅入深)
    - 引导用户从暴力解到优化解
    - 评估用户回答,给出针对性引导
    - 纠正偏离的思路
    
    激活时机: Stage.THOUGHT_ARTICULATION, Stage.COMPLEXITY_ANALYSIS
    前置条件: identified_pattern已设置
    输出: 更新context.user_approach
    """
    
    def __init__(self):
        super().__init__("GuidedThoughtGenerator")
    
    def _get_activated_stages(self):
        from core_models import Stage
        return [Stage.THOUGHT_ARTICULATION, Stage.COMPLEXITY_ANALYSIS]


class CodeEdgeCaseReviewer(ModuleInterface):
    """
    代码与边界检查模块
    
    职责:
    - 检查伪代码逻辑漏洞
    - 生成边界测试用例
    - 以问题方式引导(不直接指出错误)
    - 识别常见错误模式
    
    激活时机: Stage.PSEUDOCODE_DESIGN, Stage.EDGE_CASE_CHECK
    前置条件: context.pseudocode不为空
    输出: 更新context.detected_issues
    """
    
    def __init__(self):
        super().__init__("CodeEdgeCaseReviewer")
    
    def _get_activated_stages(self):
        from core_models import Stage
        return [Stage.PSEUDOCODE_DESIGN, Stage.EDGE_CASE_CHECK]


class FollowUpGenerator(ModuleInterface):
    """
    面试官追问模块
    
    职责:
    - 生成进阶follow-up问题
    - 提出优化方向
    - 生成变体题目
    - 压力测试情景模拟
    
    激活时机: Stage.FOLLOW_UP
    前置条件: 用户已完成基础解答
    输出: 生成追问内容
    """
    
    def __init__(self):
        super().__init__("FollowUpGenerator")
    
    def _get_activated_stages(self):
        from core_models import Stage
        return [Stage.FOLLOW_UP]


# ==================== 模块注册表 ====================

def get_all_modules() -> dict:
    """
    获取所有可用模块的实例
    主编排器会调用这个函数来初始化所有模块
    
    注意: 这个函数返回的是占位符
    实际使用时,应该返回各模块的具体实现类实例
    
    Returns:
        dict: {模块名: 模块实例}
    """
    # 第1天暂时返回空字典
    # 开发者A和B会在后续几天实现具体的模块类
    # 例如: from modules.recognizer import ConcreteRecognizer
    return {
        # "recognizer": ConcreteRecognizer(),
        # "thought_coach": ConcreteThoughtCoach(),
        # "code_reviewer": ConcreteCodeReviewer(),
        # "follow_up": ConcreteFollowUpGenerator()
    }
