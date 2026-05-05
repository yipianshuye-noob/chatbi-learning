-- 常用复合索引：按股票代码+交易日期（查询单只股票时间区间）
CREATE INDEX IF NOT EXISTS idx_stock_history_ts_code_trade_date
ON stock_history (ts_code, trade_date);

-- 常用复合索引：按交易日期+股票代码（查询某天/区间内多只股票）
CREATE INDEX IF NOT EXISTS idx_stock_history_trade_date_ts_code
ON stock_history (trade_date, ts_code);
