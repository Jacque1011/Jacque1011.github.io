#!/usr/bin/env python3
"""Minimal data fetching pipeline for the spillover-network project.

Usage:
  python scripts/fetch_data_example.py --start 2000-01-01 --end 2026-05-04

Outputs:
  - data_raw/*.csv (source-specific wide tables)
  - data_processed/market_long.csv (date, variable, value)
  - reports/fetch_log.md
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr

RAW_DIR = Path("data_raw")
PROC_DIR = Path("data_processed")
REPORT_DIR = Path("reports")

YF_TICKERS = {
    "WTI": "CL=F",
    "Brent": "BZ=F",
    "HenryHub": "NG=F",
    "SP500": "^GSPC",
    "MSCIWorldProxy": "URTH",
    "Gold": "GC=F",
    "Copper": "HG=F",
}

FRED_SERIES = {
    "DXY": "DTWEXBGS",      # Broad dollar index
    "VIX": "VIXCLS",        # CBOE VIX
    "US10Y": "DGS10",       # 10Y Treasury
    "EFFR": "DFF",          # Effective federal funds rate
}


def fetch_yfinance(start: str, end: str) -> pd.DataFrame:
    rows = []
    for var, ticker in YF_TICKERS.items():
        df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
        if df.empty:
            continue
        close = df[["Close"]].rename(columns={"Close": "value"}).copy()
        close["variable"] = var
        close = close.reset_index().rename(columns={"Date": "date"})
        rows.append(close[["date", "variable", "value"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "variable", "value"])


def fetch_fred(start: str, end: str) -> pd.DataFrame:
    rows = []
    for var, code in FRED_SERIES.items():
        s = pdr.DataReader(code, "fred", start, end)
        if s.empty:
            continue
        df = s.reset_index().rename(columns={"DATE": "date", code: "value"})
        df["variable"] = var
        rows.append(df[["date", "variable", "value"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "variable", "value"])


def write_fetch_log(start: str, end: str, combined: pd.DataFrame) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    stats = (
        combined.groupby("variable")["value"]
        .agg(n_obs="count", n_missing=lambda x: x.isna().sum())
        .reset_index()
    )
    lines = [
        "# Fetch Log",
        "",
        f"- Run time: {snapshot_time}",
        f"- Sample: {start} to {end}",
        "- Sources: Yahoo Finance (yfinance), FRED (pandas_datareader)",
        "",
        "## Variable-level stats",
        "",
        "| variable | n_obs | n_missing |",
        "|---|---:|---:|",
    ]
    for _, row in stats.iterrows():
        lines.append(f"| {row['variable']} | {int(row['n_obs'])} | {int(row['n_missing'])} |")

    (REPORT_DIR / "fetch_log.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2000-01-01")
    parser.add_argument("--end", default=datetime.utcnow().strftime("%Y-%m-%d"))
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    yf_long = fetch_yfinance(args.start, args.end)
    fred_long = fetch_fred(args.start, args.end)

    yf_long.to_csv(RAW_DIR / "yfinance_long.csv", index=False)
    fred_long.to_csv(RAW_DIR / "fred_long.csv", index=False)

    combined = pd.concat([yf_long, fred_long], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"]).dt.date
    combined = combined.sort_values(["date", "variable"]).reset_index(drop=True)
    combined.to_csv(PROC_DIR / "market_long.csv", index=False)

    write_fetch_log(args.start, args.end, combined)
    print(f"Saved {len(combined):,} rows to {PROC_DIR / 'market_long.csv'}")


if __name__ == "__main__":
    main()
