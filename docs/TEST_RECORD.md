# 测试记录

## Phase 2（真实数据接入 + 第一个数据分析 Tool）

- CSV 读取：`cleaned_ecommerce_data.csv` 用 `gb2312` 编码读取成功，438,974 行 × 18 列。
- Tool 执行：`get_sales_overview` 返回真实统计（总销售额 100,489,920.84 元、总订单 7,911 单等）。
- 编译检查：`py_compile app\agent.py app\main.py app\data_tool.py` 通过。
- LangGraph 真实调用：问「整体销售情况怎么样？」→ Agent 调用 `get_sales_overview` → 返回真实数字。
- FastAPI `/chat`：HTTP 200，回答包含真实数字。

## Phase 1

- `py_compile app\agent.py app\main.py`：通过。
- import 与路由检查：`/chat` 路由存在，Tool 注册正常。
- 缺 Key 报错路径：明确提示 `.env` 缺少 `OPENAI_API_KEY`。
- 确定性 Loop 测试（fake LLM）：消息数 2 → 4，Tool 调用与回灌各一次，最终回答正确。
- FastAPI `TestClient` 走 `/chat`：HTTP 200，返回 `{"answer": "..."}`。
- uvicorn 真实启动 + `POST /chat`：服务启动正常，缺 Key 时返回 HTTP 500 及明确原因。
- 真实 DeepSeek `/chat` 请求：HTTP 200。
