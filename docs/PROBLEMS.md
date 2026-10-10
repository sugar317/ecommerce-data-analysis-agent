# 问题记录

## 1. 未激活 .venv 导致 dotenv 找不到

- 现象：未激活虚拟环境时，dotenv 找不到 `.env`。
- 原因：依赖当前工作目录查找 `.env`。
- 解决：代码中使用 `.env` 的绝对路径加载（`Path(__file__).resolve().parents[1] / ".env"`），同时启动前激活 `.venv`。

## 2. .env 未配置导致 KEY MISSING

- 现象：`.env` 中 `OPENAI_API_KEY` 为空，调用报 KEY MISSING。
- 解决：填写 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`；代码对缺失配置返回明确错误，不静默失败。

## 3. PowerShell 中文显示乱码

- 现象：PowerShell 控制台输出中文乱码。
- 解决：运行 Python 前设置 `PYTHONIOENCODING=utf-8`，或先执行 `chcp 65001`。

## 4. 原电商项目路径与 CSV 编码（Phase 2 发现）

- 现象：提供的路径中 `\_` 是 Markdown 转义，实际目录名为 `DianShang_Dashboard`、`clean_DianShang`；目录名含「系统」。
- 现象：CSV 默认按 UTF-8 读取报 `UnicodeDecodeError`。
- 解决：按实际路径读取；CSV 使用 `gb2312` 编码（与原 DataProcessor 一致）。
