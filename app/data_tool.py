"""真实数据 Tool：复用原电商项目 DataProcessor，读取真实 CSV 计算整体销售概况。

原电商项目只读，本模块不做任何修改，只通过 importlib 动态加载其 data_processor.py。
"""

from __future__ import annotations

import importlib.util
import json
import re
import sqlite3
import threading
from functools import lru_cache

import numpy as np
import pandas as pd
from langchain_core.tools import tool

# 原电商项目固定路径（只读）
ORIGINAL_DATA_DIR = (
    r"D:\实训\实训\2251600207 唐婕 电商用户消费行为分析系统实训报告 - 副本"
    r"\2251600207 唐婕 电商用户消费行为分析系统实训报告"
    r"\清洗后数据\clean_DianShang"
)
DATA_PROCESSOR_PATH = (
    r"D:\实训\实训\2251600207 唐婕 电商用户消费行为分析系统实训报告 - 副本"
    r"\2251600207 唐婕 电商用户消费行为分析系统实训报告"
    r"\可视化\DianShang_Dashboard\data_processor.py"
)


def _load_data_processor():
    """动态加载原项目的 DataProcessor，不修改原文件。"""
    spec = importlib.util.spec_from_file_location("data_processor", DATA_PROCESSOR_PATH)
    spec.cached = None  # 不生成字节码缓存，保持原项目只读
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataProcessor(ORIGINAL_DATA_DIR)


@lru_cache(maxsize=1)
def _get_processor():
    """进程内只加载一次数据，避免每次工具调用都重新读 CSV。"""
    return _load_data_processor()


# NL2SQL 相关
TABLE_NAME = "ecommerce"
MAX_ROWS = 20
_sql_lock = threading.Lock()


@lru_cache(maxsize=1)
def _get_sqlite_conn() -> sqlite3.Connection:
    """把已加载清洗的 DataFrame 写入内存 SQLite，进程内只建一次，并设为只读。"""
    df = _get_processor().df_main.copy()
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql(TABLE_NAME, conn, index=False, if_exists="replace")
    conn.execute("PRAGMA query_only = ON")  # 数据库层禁止写操作
    return conn


def _validate_sql(sql: str) -> str | None:
    """只允许单条 SELECT（含 WITH ... SELECT），返回错误信息或 None。"""
    s = sql.strip()
    if not s:
        return "SQL 为空"
    s = s.rstrip(";").strip()
    if ";" in s:
        return "只允许单条 SELECT 语句"
    head = s.upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        return "只允许 SELECT 查询"
    for kw in (
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
        "REPLACE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "GRANT", "REVOKE",
    ):
        if re.search(rf"\b{kw}\b", head):
            return f"禁止使用 {kw}"
    return None


# RAG：轻量本地检索（TF-IDF + 余弦相似度，基于 numpy，不引入向量数据库）
_ASCII_TOKEN = re.compile(r"[a-z0-9_]+")
_CJK_TOKEN = re.compile(r"[\u4e00-\u9fff]")

KNOWLEDGE_BASE = [
    "数据集说明：清洗后的电商用户行为数据约 438,974 行，主要字段见字段说明。",
    "销售额的计算方式：SUM(price)，即对 price 字段求和。",
    "品牌销售额：按 brand 分组后对 price 求和，即 SUM(price)。",
    "月度销售趋势：按 year 和 month 字段聚合统计。",
    "字段 price：表示商品金额/价格。",
    "字段 brand：表示品牌名，为小写英文。",
    "字段 category_code：表示品类编码。",
    "字段 year 和 month：由 event_date 解析得到，分别表示年份和月份。",
    "字段 age：表示用户年龄；字段 sex：表示用户性别。",
    "字段 encrypted_local：表示脱敏后的地区标识。",
    "字段 order_id、product_id、user_id、category_id：分别表示订单、商品、用户、品类 ID。",
    "口径注意：原数据中 order_id 大量重复，不使用 order_id.nunique() 作为订单量。",
    "项目能力：LangGraph Agent、Tool Calling、NL2SQL、数据分析、RAG。",
]


def _tokenize(text: str) -> list[str]:
    """中英文混合分词：英文单词 + 单个汉字 + 汉字二元组。"""
    text = text.lower()
    tokens = _ASCII_TOKEN.findall(text)
    cjk = _CJK_TOKEN.findall(text)
    tokens += cjk
    tokens += [cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)]
    return tokens


@lru_cache(maxsize=1)
def _build_index():
    """启动时建立 TF-IDF 索引并缓存。"""
    docs = [_tokenize(d) for d in KNOWLEDGE_BASE]
    vocab = sorted({t for d in docs for t in d})
    idx = {t: i for i, t in enumerate(vocab)}
    n_docs = len(docs)

    df = np.zeros(len(vocab))
    for d in docs:
        for t in set(d):
            df[idx[t]] += 1
    idf = np.log((n_docs + 1) / (df + 1)) + 1.0

    matrix = np.zeros((n_docs, len(vocab)))
    for i, d in enumerate(docs):
        for t in d:
            matrix[i, idx[t]] += 1
    matrix = matrix * idf
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    return idx, matrix, idf


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """按 TF-IDF 余弦相似度返回最相关的 Top-K 知识片段。"""
    idx, matrix, idf = _build_index()
    q = np.zeros(len(idx))
    for t in _tokenize(query):
        if t in idx:
            q[idx[t]] += 1
    q = q * idf
    norm = np.linalg.norm(q)
    q = q / norm if norm else q

    scores = matrix @ q
    results = []
    for i in np.argsort(-scores):
        if scores[i] <= 0 or len(results) >= top_k:
            break
        results.append({"content": KNOWLEDGE_BASE[i], "score": round(float(scores[i]), 4)})
    return results


@tool
def get_sales_overview() -> str:
    """查询整体销售/数据概况。

    当用户询问整体销售情况、总销售额、总订单数、客单价等整体数据概况时调用本工具。
    返回基于真实 CSV 计算得到的统计结果，禁止编造数字。
    """
    stats = _get_processor().get_overall_stats()
    if not stats:
        return "未获取到整体销售概况（数据可能为空）。"

    return (
        "整体销售概况（来自真实清洗后数据）：\n"
        f"- 总销售额：{stats['total_sales']:,.2f} 元\n"
        f"- 总订单数：{stats['total_orders']:,} 单\n"
        f"- 日均销售额：{stats['daily_avg_sales']:,.2f} 元\n"
        f"- 平均单价：{stats['avg_price']:,.2f} 元\n"
        f"- 价格中位数：{stats['median_price']:,.2f} 元\n"
        f"- 平均每单商品数：{stats['avg_order_items']:,.2f}\n"
        f"- 商品种类数：{stats['total_products']:,}\n"
        f"- 销售额最高的单个品牌销售额：{stats['top_brand_sales']:,.2f} 元"
    )


@tool
def get_sales_trend() -> dict:
    """查询销售趋势（按月聚合）。

    当用户询问销售趋势、销售额变化、每日/每月销售情况、最近销售情况、
    哪些时间销售额更高等问题时调用本工具。
    返回基于真实 CSV 聚合得到的月度销售额与订单数，禁止编造数字。
    """
    try:
        dp = _get_processor()
        trend = dp.get_aggregated_sales_trends()  # 复用原项目按月聚合逻辑
        if trend is None or trend.empty:
            return {"success": False, "error": "没有销售趋势数据"}

        # 排除 1970 等脏数据，只保留真实年份
        trend = trend[trend["year"] >= 2000]
        if trend.empty:
            return {"success": False, "error": "没有有效日期数据"}

        data = []
        for _, row in trend.iterrows():
            data.append(
                {
                    "date": row["date"].strftime("%Y-%m"),
                    "sales": round(float(row["total_sales"]), 2),
                    "orders": int(row["order_count"]),
                }
            )

        return {
            "success": True,
            "start_date": data[0]["date"],
            "end_date": data[-1]["date"],
            "granularity": "monthly",
            "data_count": len(data),
            "data": data,
        }
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


@tool
def get_brand_analysis() -> dict:
    """查询品牌销售排行（销售额 Top 10）。

    当用户询问哪个品牌销售额最高、品牌销售排行、前十品牌、哪个品牌卖得最好等问题时调用本工具。
    返回基于真实 CSV 计算得到的品牌销售额排行，禁止编造数字。
    """
    try:
        dp = _get_processor()
        brand = dp.get_aggregated_brand_performance()  # 复用原项目品牌聚合（已按销售额降序，Top20）
        if brand is None or brand.empty:
            return {"success": False, "error": "没有品牌数据"}

        top = brand.head(10)  # 默认只返回销售额 Top 10
        data = [
            {"brand": str(row["brand"]), "sales": round(float(row["total_sales"]), 2)}
            for _, row in top.iterrows()
        ]

        return {
            "success": True,
            "metric": "sales",
            "data_count": len(data),
            "data": data,
        }
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


@tool
def get_region_analysis() -> dict:
    """查询地区销售排行（销售额 Top 10）。

    当用户询问地区、区域、省份、城市销售排行，哪个地区销售额最高、地区销售情况等问题时调用本工具。
    返回基于真实 CSV 计算得到的地区销售额排行，禁止编造数字。
    """
    try:
        dp = _get_processor()
        region = dp.get_region_sales_data()  # 复用原项目地区聚合
        if region is None or region.empty:
            return {"success": False, "error": "没有地区数据"}

        region = region.sort_values("total_sales", ascending=False).head(10)
        data = [
            {"region": str(row["region"]), "sales": round(float(row["total_sales"]), 2)}
            for _, row in region.iterrows()
        ]

        return {
            "success": True,
            "metric": "sales",
            "data_count": len(data),
            "data": data,
        }
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


@tool
def query_database(sql: str) -> dict:
    """在真实电商数据上执行只读 SQL（仅允许 SELECT），返回结构化结果。

    当用户需要自由组合筛选、排序、TopN、聚合、比较等查询，而现有专用工具无法直接回答时调用本工具。
    参数 sql 只能是一条 SELECT（或 WITH ... SELECT）语句，返回最多 20 行，禁止编造查询结果。
    """
    err = _validate_sql(sql)
    if err:
        return {"success": False, "error": err}

    sql = sql.strip().rstrip(";").strip()
    # 限制返回行数：最多 20 行；已有末尾 LIMIT 且不超过 20 则保留，超过则改小，否则追加
    m = re.search(r"\s+LIMIT\s+(\d+)\s*$", sql, flags=re.IGNORECASE)
    if m:
        if int(m.group(1)) > MAX_ROWS:
            sql = re.sub(r"\s+LIMIT\s+\d+\s*$", f" LIMIT {MAX_ROWS}", sql, flags=re.IGNORECASE)
    else:
        sql = f"{sql} LIMIT {MAX_ROWS}"

    try:
        with _sql_lock:
            df = pd.read_sql_query(sql, _get_sqlite_conn())
        records = json.loads(df.to_json(orient="records"))
        return {
            "success": True,
            "sql": sql,
            "columns": [str(c) for c in df.columns],
            "data_count": len(records),
            "data": records,
        }
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}


@tool
def retrieve_knowledge(query: str) -> dict:
    """检索项目知识库，返回与问题最相关的知识片段。

    当用户询问数据口径、字段含义、分析规则、项目能力等知识型问题时调用本工具。
    """
    try:
        results = retrieve(query, top_k=3)
        return {"success": True, "results": results}
    except Exception as exc:
        return {"success": False, "error": f"{type(exc).__name__}: {exc}"}
