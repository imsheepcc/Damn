"""
异常处理工具
提供统一的异常处理、输入验证、错误恢复机制
作者: 开发者B
日期: Day 1
"""

import logging
import time
from datetime import datetime
from typing import Tuple, Optional, Callable, Any
from core_models import (
    InterviewContext, 
    ModuleResponse, 
    Stage, 
    ExceptionLevel,
    create_error_response,
    create_success_response,
    SKIPPABLE_STAGES,
    CRITICAL_STAGES
)
from module_interface import ModuleInterface
import os


# ==================== 异常类定义 ====================

class InterviewCoachException(Exception):
    """面试教练系统的基础异常类"""
    def __init__(self, message: str, level: ExceptionLevel = ExceptionLevel.ERROR):
        self.message = message
        self.level = level
        super().__init__(self.message)


class LLMCallException(InterviewCoachException):
    """LLM调用失败异常"""
    pass


class StateInconsistencyException(InterviewCoachException):
    """状态不一致异常"""
    pass


class InvalidInputException(InterviewCoachException):
    """无效输入异常"""
    def __init__(self, message: str, input_type: str):
        self.input_type = input_type
        super().__init__(message, ExceptionLevel.INFO)


# ==================== 异常处理器 ====================

class ExceptionHandler:
    """统一的异常处理器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """设置日志系统"""
        logger = logging.getLogger("InterviewCoach")
        logger.setLevel(logging.INFO)
        
        # 控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        os.makedirs("logs", exist_ok=True)
        
        # 文件处理器
        fh = logging.FileHandler(
            f"logs/exceptions_{datetime.now().strftime('%Y%m%d')}.log",
            mode='a'
        )
        fh.setLevel(logging.WARNING)
        
        # 格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        
        logger.addHandler(ch)
        logger.addHandler(fh)
        
        return logger
    
    def handle_skip_request(self, context: InterviewContext) -> ModuleResponse:
        """
        处理用户跳过请求
        
        Args:
            context: 当前上下文
            
        Returns:
            ModuleResponse: 处理结果
        """
        current_stage = context.current_stage
        
        # 核心阶段不允许跳过
        if current_stage in CRITICAL_STAGES:
            self.logger.warning(
                f"User attempted to skip critical stage: {current_stage.name}"
            )
            return create_success_response(
                message=(
                    "I understand you want to move forward, but this stage is crucial for interview success. "
                    f"In real interviews, skipping **{self._get_stage_name_cn(current_stage)}** would be a red flag. "
                    "How about we spend just 2-3 minutes on this? It'll make a big difference."
                ),
                next_stage=None,
                skip_requested=True
            )
        
        # 可选阶段允许跳过
        elif current_stage in SKIPPABLE_STAGES:
            next_stage = self._get_next_stage(current_stage)
            skipped = context.skipped_stages + [current_stage]
            
            self.logger.info(f"User skipped optional stage: {current_stage.name}")
            
            return create_success_response(
                message=(
                    f"Okay, we can move on for now. But remember, in a real interview, "
                    f"{self._get_skip_reminder(current_stage)}. Let's continue to the next part."
                ),
                next_stage=next_stage,
                skipped_stages=skipped
            )
        
        # 其他情况,默认不允许
        else:
            return create_success_response(
                message="Let's complete this part first before moving on.",
                next_stage=None
            )
    
    def handle_invalid_input(
        self, 
        context: InterviewContext, 
        input_type: str
    ) -> ModuleResponse:
        """
        处理无效输入
        
        Args:
            context: 当前上下文
            input_type: 无效输入类型 (empty/too_short/off_topic/repeated)
            
        Returns:
            ModuleResponse: 处理结果
        """
        templates = {
            "empty": "I didn't catch that. Could you share your thoughts?",
            "too_short": "That's a bit brief! Could you elaborate a bit more?",
            "off_topic": "Hmm, that seems unrelated. Let me rephrase the question.",
            "repeated": "I notice you've said something similar before. Want to try a different angle?"
        }
        
        invalid_count = context.consecutive_invalid_inputs + 1
        
        # 连续3次无效,触发帮助模式
        if invalid_count >= 3:
            self.logger.warning(f"3 consecutive invalid inputs in session {context.session_id}")
            return self._trigger_help_mode(context)
        
        return create_success_response(
            message=templates.get(input_type, templates["empty"]),
            next_stage=None,
            consecutive_invalid_inputs=invalid_count
        )
    
    def handle_frustration(self, context: InterviewContext) -> ModuleResponse:
        """
        处理用户沮丧情绪
        
        Args:
            context: 当前上下文
            
        Returns:
            ModuleResponse: 包含鼓励和更强引导的响应
        """
        self.logger.info(f"Frustration detected in session {context.session_id}")
        
        encouragements = [
            "I can tell this is challenging, and that's completely normal! Even experienced engineers struggle with these problems at first.",
            "Let me help you break this down into smaller steps. We'll tackle it together.",
            "How about we approach this differently? Sometimes a fresh angle makes all the difference."
        ]
        
        import random
        encouragement = random.choice(encouragements)
        
        return create_success_response(
            message=encouragement + "\n\nLet me give you a helpful hint to get started.",
            next_stage=None,
            frustration_detected=True,
            hint_level="detailed"
        )
    
    def handle_llm_failure(
        self, 
        error: Exception, 
        context: InterviewContext,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> ModuleResponse:
        """
        处理LLM调用失败
        
        Args:
            error: 异常对象
            context: 当前上下文
            retry_count: 当前重试次数
            max_retries: 最大重试次数
            
        Returns:
            ModuleResponse: 降级响应
        """
        if retry_count < max_retries:
            # 指数退避重试
            wait_time = 2 ** retry_count
            self.logger.warning(
                f"LLM call failed, retrying in {wait_time}s (attempt {retry_count + 1}/{max_retries})"
            )
            time.sleep(wait_time)
            # 实际使用时这里会重新调用LLM
            # 这里只是返回指示需要重试
            return None  # 表示需要重试
        
        else:
            # 降级为模板回复
            self.logger.error(f"LLM call failed after {max_retries} retries: {error}")
            fallback_msg = self._get_fallback_template(context.current_stage)
            
            return create_success_response(
                message=fallback_msg,
                next_stage=None,
                fallback_used=True
            )
    
    def _trigger_help_mode(self, context: InterviewContext) -> ModuleResponse:
        """触发帮助模式,提供更多引导"""
        return create_success_response(
            message=(
                "I notice you might be stuck. No worries! Let me help you with a more detailed hint.\n\n"
                "Try thinking about it this way: [具体的引导问题会在这里生成]"
            ),
            next_stage=None,
            consecutive_invalid_inputs=0,  # 重置计数
            help_mode_triggered=True
        )
    
    def _get_fallback_template(self, stage: Stage) -> str:
        """获取降级模板回复"""
        templates = {
            Stage.PROBLEM_CLARIFICATION: "Let's make sure we understand the problem. What are the inputs and expected outputs?",
            Stage.THOUGHT_ARTICULATION: "Let's think about this step by step. What would be the simplest approach to solve this, even if not optimal?",
            Stage.COMPLEXITY_ANALYSIS: "Can you analyze the time and space complexity of your approach?",
            Stage.PSEUDOCODE_DESIGN: "Now let's write out the pseudocode or main logic structure.",
            Stage.EDGE_CASE_CHECK: "What edge cases should we consider? Think about empty inputs, extreme values, etc.",
            Stage.FOLLOW_UP: "Great work! Now let's think about: could we optimize this further?",
            Stage.PATTERN_SUMMARY: "Let's summarize: what pattern did we use here, and when would you use it again?"
        }
        return templates.get(stage, "Let's continue with the next step.")
    
    def _get_stage_name_cn(self, stage: Stage) -> str:
        """获取阶段的中文名称"""
        names = {
            Stage.PROBLEM_CLARIFICATION: "题意确认",
            Stage.THOUGHT_ARTICULATION: "思路讲解",
            Stage.COMPLEXITY_ANALYSIS: "复杂度分析",
            Stage.PSEUDOCODE_DESIGN: "代码实现",
            Stage.EDGE_CASE_CHECK: "边界检查",
            Stage.FOLLOW_UP: "深入讨论",
            Stage.PATTERN_SUMMARY: "总结"
        }
        return names.get(stage, stage.name)
    
    def _get_skip_reminder(self, stage: Stage) -> str:
        """获取跳过提醒"""
        reminders = {
            Stage.COMPLEXITY_ANALYSIS: "discussing complexity shows analytical maturity",
            Stage.PATTERN_SUMMARY: "summarizing patterns helps you in future problems"
        }
        return reminders.get(stage, "this step is valuable")
    
    def _get_next_stage(self, current: Stage) -> Stage:
        """获取下一阶段"""
        from core_models import STAGE_TRANSITION_RULES
        return STAGE_TRANSITION_RULES.get(current)


# ==================== 输入验证器 ====================

class InputValidator:
    """用户输入验证器"""
    
    @staticmethod
    def validate(user_input: str, context: InterviewContext) -> Tuple[bool, Optional[str]]:
        """
        验证用户输入
        
        Args:
            user_input: 用户输入
            context: 当前上下文
            
        Returns:
            Tuple[是否有效, 异常类型]
        """
        # 空输入
        if not user_input or user_input.strip() == "":
            return False, "empty"
        
        # 过短输入
        if len(user_input.strip()) < 5:
            return False, "too_short"
        
        # 检测重复输入
        if len(context.conversation_history) >= 3:
            recent_inputs = [
                msg.content for msg in context.conversation_history[-3:] 
                if msg.role == "user"
            ]
            if user_input.strip() in recent_inputs:
                return False, "repeated"
        
        # 简单相关性检查(可以后续改进为LLM判断)
        # 暂时只检查是否包含一些明显无关的内容
        off_topic_keywords = ["weather", "天气", "吃饭", "lunch", "游戏", "game"]
        if any(kw in user_input.lower() for kw in off_topic_keywords):
            return False, "off_topic"
        
        return True, None
    
    @staticmethod
    def detect_skip_request(user_input: str) -> bool:
        """检测是否是跳过请求"""
        skip_keywords = ["skip", "跳过", "下一个", "next", "pass"]
        return any(kw in user_input.lower() for kw in skip_keywords)
    
    @staticmethod
    def detect_frustration(user_input: str) -> bool:
        """检测沮丧情绪"""
        frustration_keywords = [
            "too hard", "太难", "give up", "放弃", 
            "don't know", "不会", "can't", "不懂"
        ]
        return any(kw in user_input.lower() for kw in frustration_keywords)
    
    @staticmethod
    def detect_answer_request(user_input: str) -> bool:
        """检测直接要答案"""
        answer_keywords = [
            "give me the answer", "tell me the answer", "直接告诉我",
            "what's the solution", "答案是什么", "just show me"
        ]
        return any(kw in user_input.lower() for kw in answer_keywords)


# ==================== 安全模块调用包装器 ====================

def safe_module_call(
    module: ModuleInterface, 
    context: InterviewContext,
    exception_handler: ExceptionHandler
) -> ModuleResponse:
    """
    安全地调用模块,统一处理异常
    
    Args:
        module: 要调用的模块
        context: 当前上下文
        exception_handler: 异常处理器
        
    Returns:
        ModuleResponse: 模块响应或错误响应
    """
    try:
        # 前置验证
        if not module.validate_context(context):
            raise StateInconsistencyException(
                f"Context validation failed for {module.module_name}"
            )
        
        # 执行模块
        response = module.process(context)
        
        # 后置验证
        if not isinstance(response, ModuleResponse):
            raise ValueError(f"{module.module_name} returned invalid response type")
        
        return response
    
    except LLMCallException as e:
        return exception_handler.handle_llm_failure(e, context)
    
    except StateInconsistencyException as e:
        exception_handler.logger.error(f"State inconsistency: {e.message}")
        return create_error_response(
            error_msg=e.message,
            level=ExceptionLevel.ERROR
        )
    
    except Exception as e:
        # 未预期的异常
        exception_handler.logger.critical(
            f"Unexpected exception in {module.module_name}: {str(e)}"
        )
        return create_error_response(
            error_msg=f"Unexpected error: {str(e)}",
            level=ExceptionLevel.CRITICAL
        )
