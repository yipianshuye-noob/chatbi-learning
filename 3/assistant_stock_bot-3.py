import json
import os
import sqlite3
import time
from pathlib import Path

import dashscope
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from qwen_agent.agents import Assistant
from qwen_agent.gui import WebUI
from qwen_agent.tools.base import BaseTool, register_tool

# 解决中文显示问题
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "2" / "stock_history.sqlite"
IMAGE_DIR = BASE_DIR / "image_show"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# 配置 DashScope
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")
dashscope.timeout = 30

system_prompt = """我是股票查询助手，基于 SQLite 数据库中的 stock_history 表回答问题。
表结构如下：
CREATE TABLE stock_history (
    ts_code TEXT,        -- 股票代码
    trade_date TEXT,     -- 交易日期，格式 YYYY-MM-DD
    open REAL,           -- 开盘价
    high REAL,           -- 最高价
    low REAL,            -- 最低价
    close REAL,          -- 收盘价
    pre_close REAL,      -- 昨收价
    change REAL,         -- 涨跌额
    pct_chg REAL,        -- 涨跌幅
    vol REAL,            -- 成交量
    amount REAL,         -- 成交额
    name TEXT            -- 股票名称
);

可查询股票包括：贵州茅台、五粮液、广发证券、中芯国际。

SQL 生成要求：
1. 仅使用 SELECT 查询，禁止写入或删除操作。
2. 日期字段是 trade_date（TEXT），比较时按 YYYY-MM-DD 处理。
3. 用户问“最近/最新”时，优先按 trade_date DESC 排序并 LIMIT。

每当 exc_sql 工具返回 markdown 表格和图片时，你必须原样输出工具返回的全部内容（包括图片 markdown），不要只总结表格，也不要省略图片。
"""

functions_desc = [
    {
        "name": "exc_sql",
        "description": "执行 SQLite 查询并返回结果表格与图表",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_input": {
                    "type": "string",
                    "description": "待执行的 SQL 查询语句",
                }
            },
            "required": ["sql_input"],
        },
    },
]


def _generate_chart_png(df_sql: pd.DataFrame, save_path: Path) -> None:
    """根据查询结果自动生成图表。"""
    if df_sql.empty or len(df_sql.columns) < 2:
        return

    plot_df = df_sql.copy()
    x_col = plot_df.columns[0]
    y_cols = [c for c in plot_df.columns[1:] if pd.api.types.is_numeric_dtype(plot_df[c])]
    if not y_cols:
        return

    x_labels = plot_df[x_col].astype(str).tolist()
    x = np.arange(len(plot_df))
    bottom = np.zeros(len(plot_df))

    plt.figure(figsize=(11, 6))
    for col in y_cols[:4]:
        plt.bar(x, plot_df[col].astype(float), bottom=bottom, label=str(col))
        bottom += plot_df[col].astype(float).to_numpy()

    plt.xticks(x, x_labels, rotation=45)
    plt.xlabel(str(x_col))
    plt.ylabel("数值")
    plt.title("股票查询结果可视化")
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()


@register_tool("exc_sql")
class ExcSQLTool(BaseTool):
    """执行 SQL 查询并输出 markdown 表格与图片。"""

    description = "执行 SQLite 查询并返回前 200 行结果"
    parameters = [
        {
            "name": "sql_input",
            "type": "string",
            "description": "待执行的 SQL 查询语句",
            "required": True,
        }
    ]

    def call(self, params: str, **kwargs) -> str:
        args = json.loads(params)
        sql_input = args["sql_input"].strip()
        sql_lower = sql_input.lower()

        # 仅允许查询语句，避免修改数据库
        if not sql_lower.startswith("select"):
            raise ValueError("只允许执行 SELECT 查询语句")

        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(sql_input, conn)

        preview = df.head(200)
        md = preview.to_markdown(index=False)

        filename = f"stock_chart_{int(time.time() * 1000)}.png"
        save_path = IMAGE_DIR / filename
        _generate_chart_png(preview, save_path)

        img_md = ""
        if save_path.exists():
            img_md = f"\n\n![查询图表](image_show/{filename})"
        return f"{md}{img_md}"


def init_agent_service() -> Assistant:
    """初始化股票查询助手。"""
    llm_cfg = {
        "model": "qwen-turbo",
        "timeout": 30,
        "retry_count": 3,
    }
    bot = Assistant(
        llm=llm_cfg,
        name="股票查询助手",
        description="基于 SQLite 的股票行情查询与分析助手",
        system_message=system_prompt,
        function_list=["exc_sql"],
    )
    return bot


def app_tui() -> None:
    """终端交互模式。"""
    bot = init_agent_service()
    messages = []
    while True:
        query = input("user question: ").strip()
        if not query:
            print("请输入有效问题")
            continue
        messages.append({"role": "user", "content": query})
        response = []
        for response in bot.run(messages):
            print("bot response:", response)
        messages.extend(response)


def app_gui() -> None:
    """Web 图形界面模式。"""
    bot = init_agent_service()
    chatbot_config = {
        "prompt.suggestions": [
            "查询贵州茅台最近10个交易日收盘价",
            "统计2024年每个月四只股票的平均涨跌幅",
            "比较贵州茅台和五粮液在2023年的最高价与最低价",
        ]
    }
    WebUI(bot, chatbot_config=chatbot_config).run()


if __name__ == "__main__":
    app_gui()
