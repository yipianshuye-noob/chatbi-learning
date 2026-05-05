CREATE TABLE IF NOT EXISTS "stock_history" (
    "ts_code" TEXT,
    "trade_date" TEXT,
    "open" REAL,
    "high" REAL,
    "low" REAL,
    "close" REAL,
    "pre_close" REAL,
    "change" REAL,
    "pct_chg" REAL,
    "vol" REAL,
    "amount" REAL,
    "name" TEXT
);
