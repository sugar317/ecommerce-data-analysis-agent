# 项目开发记忆日志

## 目前做到哪里

Phase 2 第一工具已完成：Agent 已接入真实数据，问「整体销售情况怎么样？」会读取真实 CSV 并返回真实数字。

## 最近做了什么

- 新增 `app/data_tool.py`，复用原电商项目 DataProcessor 实现 `get_sales_overview`，并接入 Agent。
- 验证 CSV 读取、Tool 执行、真实 LangGraph 调用、`/chat` 全部通过。
- 完成 Phase 1 代码与验证，真实 `/chat` 请求返回 HTTP 200。
- 建立 `docs/` 开发归档系统（本文件所属目录）。

## 下一步做什么

等待用户指示进入下一阶段；后续优先复用原项目 DataProcessor 的其余统计方法（趋势 / 品牌 / 地区 / 年龄 / 价格 / 品类 / 时间），不重写统计逻辑。

## 原电商项目准确路径（只读）

- 数据处理器：`D:\实训\实训\2251600207 唐婕 电商用户消费行为分析系统实训报告 - 副本\2251600207 唐婕 电商用户消费行为分析系统实训报告\可视化\DianShang_Dashboard\data_processor.py`
- 清洗后数据：`D:\实训\实训\2251600207 唐婕 电商用户消费行为分析系统实训报告 - 副本\2251600207 唐婕 电商用户消费行为分析系统实训报告\清洗后数据\clean_DianShang\cleaned_ecommerce_data.csv`
- 注意：目录名含「系统」，CSV 编码为 `gb2312`。

## 重要约束

- Python 版本固定 3.11.9，使用当前 `.venv`，不新建虚拟环境。
- 不使用 Docker / Kubernetes / Multi-Agent / 复杂长期 Memory / GraphRAG / LoRA / vLLM / SGLang。
- 暂不引入 Redis（除非后续确有必要）。
- 不一次性生成整个项目，每阶段验证后再进入下一阶段。
- 不修改已经能运行的代码、不修改原电商项目（只读）。
- 代码必须能实际运行，中文注释，Plotly 标题与坐标轴用英文。
- 已实现与计划实现必须区分清楚，不虚报。
