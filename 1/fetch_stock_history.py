import os
from datetime import datetime

import pandas as pd
import tushare as ts


def main() -> None:
    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("环境变量 TUSHARE_TOKEN 未设置")

    pro = ts.pro_api(token)
    symbols = {
        "贵州茅台": "600519.SH",
        "五粮液": "000858.SZ",
        "广发证券": "000776.SZ",
        "中芯国际": "688981.SH",
    }

    start_date = "20200101"
    end_date = datetime.today().strftime("%Y%m%d")

    all_frames = []
    for name, ts_code in symbols.items():
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            continue
        df["name"] = name
        all_frames.append(df)

    if not all_frames:
        raise RuntimeError("未获取到任何历史行情数据")

    result = pd.concat(all_frames, ignore_index=True)
    result["trade_date"] = pd.to_datetime(result["trade_date"], format="%Y%m%d")
    result = result.sort_values(by=["trade_date", "ts_code"], ascending=[True, True]).reset_index(drop=True)
    result["trade_date"] = result["trade_date"].dt.strftime("%Y-%m-%d")

    output_path = os.path.join(os.path.dirname(__file__), "四支股票历史价格_2020至今.xlsx")
    result.to_excel(output_path, sheet_name="history_prices", index=False)
    print(f"已生成文件: {output_path}")
    print(f"总记录数: {len(result)}")


if __name__ == "__main__":
    main()
