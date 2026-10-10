"""Enterprise Data Analyst Agent —— Phase 1 最小可运行 Agent。

链路：FastAPI -> LangGraph(StateGraph) -> LLM -> Tool Calling -> Tool Result -> Final Answer

当前阶段只有一个确定性 Tool（能力清单），不包含数据库 / NL2SQL / RAG / MCP。
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.data_tool import (
    get_brand_analysis,
    get_region_analysis,
    get_sales_overview,
    get_sales_trend,
    query_database,
    retrieve_knowledge,
)

# .env 固定放在项目根目录，显式指定路径，避免受启动目录影响
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

# 进程内短期会话记忆：按 thread_id 保存多轮消息
_memory = MemorySaver()


class AgentConfigError(RuntimeError):
    """配置缺失（例如没有 API Key）时抛出，交给 API 层返回明确原因。"""


@tool
def list_agent_capabilities() -> str:
    """查询本 Agent 支持的能力清单。

    当用户询问“你能做什么 / 支持哪些功能 / 有哪些工具”时调用本工具。
    返回固定的能力清单，不涉及任何数据查询或计算。
    """
    return (
        "Enterprise Data Analyst Agent 能力清单：\n"
        "1. 能力自述：说明本 Agent 当前能做什么（已实现）\n"
        "2. 数据查询（NL2SQL）：把自然语言问题转成 SQL 查询订单、用户、商品数据（规划中）\n"
        "3. 数据分析：销售趋势、品牌表现、地区、年龄、价格、品类、时间等聚合分析（规划中）\n"
        "4. RFM 用户分层：计算 R/F/M 指标并划分用户价值层级（规划中）\n"
        "5. KMeans 聚类：对用户或商品做聚类分群（规划中）\n"
        "6. 图表生成：用 Plotly 输出趋势图、对比图等可视化结果（规划中）\n"
        "7. 指标解释（RAG）：解释字段含义、指标定义、业务规则与 RFM 规则（规划中）"
    )


# 阶段内所有 Tool 集中在这里注册，后续阶段继续往这个列表里加
TOOLS = [
    list_agent_capabilities,
    get_sales_overview,
    get_sales_trend,
    get_brand_analysis,
    get_region_analysis,
    query_database,
    retrieve_knowledge,
]

SYSTEM_PROMPT = (
    "你是企业数据分析 Agent 的助手，服务于电商用户行为数据分析场景。"
    "当用户询问你能做什么、支持哪些能力或有哪些工具时，必须先调用 list_agent_capabilities 工具，"
    "再根据工具返回结果用中文简洁作答；不要编造工具没有提供的能力。"
    "当用户询问整体销售情况、总销售额、总订单数等整体数据概况时，必须先调用 get_sales_overview 工具，"
    "再用返回的真实数字回答，禁止编造任何数据。"
    "当用户询问销售趋势、销售额变化、每日/每月销售情况、最近销售、哪些时间销售额更高等问题时，"
    "必须先调用 get_sales_trend 工具获取真实数据，不得自行编造趋势数字。"
    "如果用户只是问整体销售概况，仍使用 get_sales_overview，不要误调 get_sales_trend。"
    "当用户询问品牌销售、品牌排行、哪个品牌卖得最好、品牌销售额等问题时，必须调用 get_brand_analysis 工具，"
    "再用返回的真实品牌和销售额回答，不得自行编造品牌销售数字。"
    "当用户询问地区、区域、省份、城市销售排行或地区销售情况时，必须调用 get_region_analysis 工具，"
    "再用返回的真实地区和销售额回答，不得自行编造地区销售数字。"
    "可用数据表 ecommerce 的真实字段：price(金额，求和即销售额)、brand(品牌，小写英文)、"
    "category_code(品类编码)、year(年)、month(月)、age(年龄)、sex(性别)、"
    "encrypted_local(脱敏地区)、order_id、product_id、user_id、category_id。"
    "当用户提出需要自由组合筛选、排序、TopN、聚合、比较等数据库查询，而现有专用工具无法直接回答时，"
    "根据真实字段生成一条只含 SELECT 的 SQL 并调用 query_database，只能根据返回结果回答，不得编造 SQL 查询结果。"
    "当用户询问数据口径、字段含义、分析规则、项目能力等知识型问题时，优先调用 retrieve_knowledge 工具，"
    "再根据检索结果回答，不要仅凭模型记忆编造口径。真实数据计算、筛选、排序、聚合仍使用现有专用工具或 query_database，"
    "不要对所有问题都调用 RAG。"
    "回答控制在 200 字以内。"
)


def _build_llm() -> ChatOpenAI:
    """从 .env / 环境变量读取配置创建模型客户端，配置缺失时抛出明确错误。"""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    base_url = (os.getenv("OPENAI_BASE_URL") or "").strip()
    model = (os.getenv("OPENAI_MODEL") or "").strip()

    if not api_key:
        raise AgentConfigError(
            f"未读取到 OPENAI_API_KEY，请在 {ENV_PATH} 中配置该变量后重试。"
        )
    if not model:
        raise AgentConfigError(
            f"未读取到 OPENAI_MODEL，请在 {ENV_PATH} 中配置模型名（例如 gpt-4o-mini 或 deepseek-chat）。"
        )

    kwargs: dict = {"model": model, "api_key": api_key, "temperature": 0, "timeout": 60, "max_retries": 1}
    if base_url:
        # 兼容 OpenAI 官方以外的 OpenAI 协议服务（DeepSeek / DashScope 兼容模式等）
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=1)
def get_agent():
    """构建并缓存 LangGraph Agent，首次调用时才需要 API Key。"""
    llm_with_tools = _build_llm().bind_tools(TOOLS)

    def agent_node(state: MessagesState) -> dict:
        # LLM 节点：带上系统提示，决定是直接回答还是发起 Tool Calling
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        return {"messages": [llm_with_tools.invoke(messages)]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))  # 执行工具，把 ToolMessage 写回 state
    builder.add_edge(START, "agent")
    # LLM 有 tool_calls 就进 tools，否则结束
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")  # 工具结果回灌给 LLM 生成最终回答
    return builder.compile(checkpointer=_memory)


def run_agent(message: str, thread_id: str | None = None) -> str:
    """执行一次 Agent Loop；相同 thread_id 共享会话上下文。"""
    agent = get_agent()
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={
            "configurable": {"thread_id": thread_id or "default"},
            "recursion_limit": 10,  # 防止工具循环失控
        },
    )
    final_message = result["messages"][-1]
    content = final_message.content
    return content if isinstance(content, str) else str(content)
