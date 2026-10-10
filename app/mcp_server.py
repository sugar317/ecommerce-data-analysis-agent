"""MCP Server（最小 hello Tool）。

注意：当前安装的是 mcp 2.x，FastMCP 已更名为 MCPServer。
"""

from mcp.server.mcpserver import MCPServer

from app.data_tool import query_database

mcp = MCPServer("ecommerce-analyst")


@mcp.tool()
def hello(name: str) -> str:
    """返回问候语：Hello, {name}"""
    return f"Hello, {name}"


@mcp.tool()
def query_ecommerce_data(sql: str) -> dict:
    """在真实电商数据上执行只读 SQL，复用现有 query_database 的安全与数据逻辑。"""
    return query_database.invoke({"sql": sql})


if __name__ == "__main__":
    mcp.run()
