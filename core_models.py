"""
核心数据结构定义
作者: 开发者B
日期: Day 1
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


# ==================== 枚举定义 ====================

class Stage(Enum):
    """面试教学的7个标准阶段"""
    PROBLEM_CLARIFICATION = 0    # 题意确认
    THOUGHT_ARTICULATION = 1     # 思路口述
    COMPLEXITY_ANALYSIS = 2      # 复杂度分析
    PSEUDOCODE_DESIGN = 3        # 伪代码/框架实现
    EDGE_CASE_CHECK = 4          # 边界条件检查
    FOLLOW_UP = 5                # follow-up追问
    PATTERN_SUMMARY = 6          # 题型套路总结


class ExceptionLevel(Enum):
    """异常严重程度"""
    CRITICAL = 1    # 致命错误,必须中止会话
    ERROR = 2       # 严重错误,需要降级服务
    WARNING = 3     # 警告,可以继续但需记录
    INFO = 4        # 信息性异常,正常处理流程


# ==================== 消息与上下文 ====================

@dataclass
class Message:
    """单条对话消息"""
    role: str           # "user" 或 "assistant"
    content: str        # 消息内容
    timestamp: float    # 时间戳
    stage: Stage        # 发送时所处的阶段
    
    def __post_init__(self):
        if self.role not in ["user", "assistant"]:
            raise ValueError(f"Invalid role: {self.role}")


@dataclass
class InterviewContext:
    """
    面试会话的全局上下文
    在所有模块间传递,但模块不应直接修改它
    """
    
    # ===== 基础信息 =====
    session_id: str                          # 会话唯一ID
    problem_text: str                        # 题目原文
    problem_metadata: Dict[str, Any]         # 题目元数据(难度、标签等)
    
    # ===== 状态管理 =====
    current_stage: Stage                     # 当前所处阶段
    stage_history: List[Stage]               # 阶段历史记录
    stage_start_time: float                  # 当前阶段开始时间
    
    # ===== 对话记录 =====
    conversation_history: List[Message]      # 完整对话历史
    current_user_input: str                  # 当前用户输入
    
    # ===== 各模块的输出缓存 =====
    identified_pattern: Optional[str] = None         # 题型识别结果
    complexity_expectation: Optional[str] = None     # 复杂度期望
    user_approach: Optional[str] = None              # 用户思路总结
    pseudocode: Optional[str] = None                 # 用户伪代码
    detected_issues: List[str] = field(default_factory=list)  # 发现的问题列表
    
    # ===== 异常处理相关 =====
    consecutive_invalid_inputs: int = 0              # 连续无效输入次数
    skip_requested: bool = False                     # 是否请求跳过
    skipped_stages: List[Stage] = field(default_factory=list)  # 已跳过的阶段
    frustration_detected: bool = False               # 是否检测到沮丧
    answer_requests: int = 0                         # 要求直接答案的次数
    
    # ===== 元数据 =====
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外的元数据
    
    # ===== 用户画像(后期实现) =====
    user_profile: Optional[Dict] = None
    
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.now().timestamp(),
            stage=self.current_stage
        )
        self.conversation_history.append(msg)
    
    def transition_to(self, next_stage: Stage):
        """转换到下一阶段"""
        self.stage_history.append(self.current_stage)
        self.current_stage = next_stage
        self.stage_start_time = datetime.now().timestamp()


@dataclass
class ModuleResponse:
    """
    所有模块的统一返回格式
    """
    success: bool                    # 是否成功执行
    assistant_message: str           # 给用户的回复内容
    next_stage: Optional[Stage]      # 建议的下一阶段(None表示保持当前阶段)
    context_updates: Dict[str, Any]  # 需要更新到context的字段
    metadata: Dict[str, Any]         # 模块内部元数据(用于调试/日志)
    
    # 错误处理
    error_message: Optional[str] = None
    exception_level: Optional[ExceptionLevel] = None
    
    def __post_init__(self):
        # 验证必填字段
        if self.success and not self.assistant_message:
            raise ValueError("Success response must have assistant_message")
        
        if not self.success and not self.error_message:
            raise ValueError("Failed response must have error_message")


# ==================== 工厂函数 ====================

def create_mock_context(
    problem_text: str = "Sample problem",
    current_stage: Stage = Stage.PROBLEM_CLARIFICATION,
    session_id: str = "test_session"
) -> InterviewContext:
    """
    创建用于测试的Mock上下文
    开发者A和B都可以用这个函数生成测试数据
    """
    return InterviewContext(
        session_id=session_id,
        problem_text=problem_text,
        problem_metadata={"difficulty": "Medium", "tags": ["Array"]},
        current_stage=current_stage,
        stage_history=[],
        stage_start_time=datetime.now().timestamp(),
        conversation_history=[],
        current_user_input="",
        metadata={}
    )


def create_success_response(
    message: str,
    next_stage: Optional[Stage] = None,
    **context_updates
) -> ModuleResponse:
    """快速创建成功响应的辅助函数"""
    return ModuleResponse(
        success=True,
        assistant_message=message,
        next_stage=next_stage,
        context_updates=context_updates,
        metadata={}
    )


def create_error_response(
    error_msg: str,
    level: ExceptionLevel = ExceptionLevel.ERROR
) -> ModuleResponse:
    """快速创建错误响应的辅助函数"""
    return ModuleResponse(
        success=False,
        assistant_message="I encountered an issue. Let me try to help you another way.",
        next_stage=None,
        context_updates={},
        metadata={},
        error_message=error_msg,
        exception_level=level
    )


# ==================== 常量定义 ====================

# 阶段转换规则(简化版,第2天由开发者A完善)
STAGE_TRANSITION_RULES = {
    Stage.PROBLEM_CLARIFICATION: Stage.THOUGHT_ARTICULATION,
    Stage.THOUGHT_ARTICULATION: Stage.COMPLEXITY_ANALYSIS,
    Stage.COMPLEXITY_ANALYSIS: Stage.PSEUDOCODE_DESIGN,
    Stage.PSEUDOCODE_DESIGN: Stage.EDGE_CASE_CHECK,
    Stage.EDGE_CASE_CHECK: Stage.FOLLOW_UP,
    Stage.FOLLOW_UP: Stage.PATTERN_SUMMARY,
    Stage.PATTERN_SUMMARY: None  # 结束
}

# 可跳过的阶段
SKIPPABLE_STAGES = {
    Stage.COMPLEXITY_ANALYSIS,
    Stage.PATTERN_SUMMARY
}

# 核心阶段(不可跳过)
CRITICAL_STAGES = {
    Stage.THOUGHT_ARTICULATION,
    Stage.PSEUDOCODE_DESIGN,
    Stage.EDGE_CASE_CHECK
}
