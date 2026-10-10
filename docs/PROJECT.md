# Enterprise Data Analyst Agent 项目说明

## 项目定位

面向深圳 AI 应用开发 / Agent 开发岗位面试的个人求职作品集项目，单 Agent。

用于证明对以下能力的理解：

- LLM Agent Loop
- LangGraph
- Tool Calling
- NL2SQL
- 数据分析工具调用
- RAG
- FastAPI
- 基础 Agent Evaluation
- （后续视情况）MCP

## 目标架构（规划）

用户 → FastAPI → LangGraph Agent → Intent / Planning → Tool Calling（SQL/NL2SQL、数据分析、RFM、KMeans、图表、RAG）→ Validation / Retry → 最终回答

## 技术栈

- Python 3.11.9
- FastAPI
- LangGraph 1.x / LangChain 1.x
- langchain-openai（模型调用）
- pandas / plotly（数据分析与可视化）
- pydantic / python-dotenv

## 当前目录结构

```text
D:\Agent_project
├─ .env
├─ app
│  ├─ agent.py
│  └─ main.py
└─ docs
   ├─ PROJECT.md
   ├─ CURRENT_STATUS.md
   ├─ DEVELOPMENT_LOG.md
   ├─ PROBLEMS.md
   ├─ DECISIONS.md
   ├─ TEST_RECORD.md
   └─ AGENT_MEMORY.md
```

> 注：原始电商数据分析项目与本项目分离，后续只读取其 cleaned_ecommerce_data.csv 或复用 DataProcessor，不修改原项目。
