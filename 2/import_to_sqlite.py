import os
import sqlite3
from pathlib import Path

import pandas as pd


def infer_sqlite_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    if pd.api.types.is_float_dtype(series):
        return "REAL"
    return "TEXT"


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    source_xlsx = next((base_dir.parent / "1").glob("*.xlsx"), None)
    if source_xlsx is None:
        raise RuntimeError("未找到来源 Excel 文件")

    df = pd.read_excel(source_xlsx, sheet_name=0)
    table_name = "stock_history"

    col_defs = []
    for col in df.columns:
        col_type = infer_sqlite_type(df[col])
        col_defs.append(f"    {quote_ident(str(col))} {col_type}")

    create_sql = (
        f"CREATE TABLE IF NOT EXISTS {quote_ident(table_name)} (\n"
        + ",\n".join(col_defs)
        + "\n);\n"
    )

    sql_file = base_dir / "create_stock_history_table.sql"
    sql_file.write_text(create_sql, encoding="utf-8")

    db_path = base_dir / "stock_history.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"DROP TABLE IF EXISTS {quote_ident(table_name)}")
        conn.execute(create_sql)
        df.to_sql(table_name, conn, if_exists="append", index=False)
        row_count = conn.execute(f"SELECT COUNT(1) FROM {quote_ident(table_name)}").fetchone()[0]

    print(f"SOURCE_XLSX={source_xlsx}")
    print(f"SQL_FILE={sql_file}")
    print(f"DB_FILE={db_path}")
    print(f"TABLE_NAME={table_name}")
    print(f"ROW_COUNT={row_count}")


if __name__ == "__main__":
    main()
