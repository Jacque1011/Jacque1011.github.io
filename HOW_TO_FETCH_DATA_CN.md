# 如何抓取本研究所需数据（可直接执行）

## 1) 安装依赖
```bash
pip install pandas yfinance pandas_datareader
```

## 2) 运行抓取脚本
```bash
python scripts/fetch_data_example.py --start 2000-01-01 --end 2026-05-04
```

## 3) 输出文件说明
- `data_raw/yfinance_long.csv`：Yahoo Finance原始长表。
- `data_raw/fred_long.csv`：FRED原始长表。
- `data_processed/market_long.csv`：统一后的长表（`date, variable, value`）。
- `reports/fetch_log.md`：每次抓取的日志与缺失统计。

## 4) 如何加入 GPR（关键）
1. 从 Caldara-Iacoviello 官方页面下载 GPR 日度/周度数据；
2. 整理为三列：`date,variable,value`，其中 `variable=GPR`；
3. 与 `data_processed/market_long.csv` 按行拼接；
4. 对 GPR 做标准化（z-score），价格类变量做对数收益率。

## 5) 下一步（衔接你的研究流程）
- 先用最小变量集：`GPR, WTI, SP500, Gold`；
- 跑通：预处理 → MODWT分解 → TVP-VAR-BK溢出网络；
- 成功后再扩展到三层网络全变量。
