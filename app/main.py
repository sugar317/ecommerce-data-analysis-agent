"""Enterprise Data Analyst Agent —— FastAPI 入口（Phase 1 只提供 POST /chat）。

启动：uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent import AgentConfigError, run_agent

app = FastAPI(title="Enterprise Data Analyst Agent", version="0.1.0")

# 允许本地演示页面（file:// 或其他端口）调用 /chat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """请求体：{"message": "我可以让这个Agent做什么？"}"""

    message: str = Field(..., min_length=1, description="用户问题")
    thread_id: str | None = Field(default=None, description="会话 ID，相同 ID 共享上下文")


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """接收用户问题，走一次 LangGraph Agent Loop，返回最终回答。"""
    try:
        answer = run_agent(request.message, thread_id=request.thread_id)
    except AgentConfigError as exc:
        # 配置问题（例如缺少 API Key）直接暴露原因，便于定位
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        # 模型/网络/工具异常：返回类型和原始信息，不静默失败
        raise HTTPException(
            status_code=502,
            detail=f"Agent 执行失败：{type(exc).__name__}: {exc}",
        ) from exc
    return ChatResponse(answer=answer)
