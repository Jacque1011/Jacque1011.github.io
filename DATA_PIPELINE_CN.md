# 数据抓取 + 整理 + 清洗（一键流程）

你只需要手动下载 GPR；其他都交给 Python。

## 0. 安装依赖
```bash
pip install pandas yfinance pandas_datareader numpy
```

## 1. 抓取市场与宏观数据（自动）
```bash
python scripts/fetch_data_example.py --start 2000-01-01 --end 2026-05-04
```
输出：
- `data_raw/yfinance_long.csv`
- `data_raw/fred_long.csv`
- `data_processed/market_long.csv`
- `reports/fetch_log.md`

## 2. 你手动下载 GPR 后并表（半自动）
把你的 GPR 文件放到：`data_raw/gpr_daily.csv`

要求最少两列：
- 日期列：`date` 或 `DATE` 或 `Date`
- 数值列：`value` 或 `GPR` 或 `gpr`

然后运行：
```bash
python scripts/merge_gpr.py --gpr data_raw/gpr_daily.csv
```
输出：
- `data_processed/market_with_gpr_long.csv`

## 3. 数据清洗和建模前处理（自动）
```bash
python scripts/preprocess_pipeline.py \
  --input data_processed/market_with_gpr_long.csv \
  --out data_processed/model_input_long.csv \
  --qc reports/preprocess_qc.md
```
处理逻辑：
- 价格变量（WTI/Brent/SP500/Gold等）→ 对数收益率 `100*Δln(P)`
- 风险与宏观水平变量（GPR/VIX/DXY/US10Y/EFFR）→ z-score
- 自动输出缺失与统计报告

## 4. 你下一步直接用这个文件建模
- `data_processed/model_input_long.csv`
