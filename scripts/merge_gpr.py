#!/usr/bin/env python3
"""Merge manually downloaded GPR data into market_long.csv.

Expected GPR input columns:
- date column: one of [date, DATE, Date]
- value column: one of [value, GPR, gpr]

Usage:
  python scripts/merge_gpr.py \
    --market data_processed/market_long.csv \
    --gpr data_raw/gpr_daily.csv \
    --out data_processed/market_with_gpr_long.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def normalize_gpr(gpr_path: Path) -> pd.DataFrame:
    gpr = pd.read_csv(gpr_path)

    date_col = next((c for c in ["date", "DATE", "Date"] if c in gpr.columns), None)
    value_col = next((c for c in ["value", "GPR", "gpr"] if c in gpr.columns), None)

    if date_col is None or value_col is None:
        raise ValueError("GPR file must contain date/date-like and value/GPR columns")

    out = gpr[[date_col, value_col]].rename(columns={date_col: "date", value_col: "value"}).copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).copy()
    out["date"] = out["date"].dt.date
    out["variable"] = "GPR"
    return out[["date", "variable", "value"]]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--market", default="data_processed/market_long.csv")
    p.add_argument("--gpr", required=True)
    p.add_argument("--out", default="data_processed/market_with_gpr_long.csv")
    args = p.parse_args()

    market = pd.read_csv(args.market)
    market["date"] = pd.to_datetime(market["date"], errors="coerce").dt.date
    market = market.dropna(subset=["date"]).copy()

    gpr_long = normalize_gpr(Path(args.gpr))

    combined = pd.concat([market, gpr_long], ignore_index=True)
    combined = combined.drop_duplicates(subset=["date", "variable"], keep="last")
    combined = combined.sort_values(["date", "variable"]).reset_index(drop=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(out_path, index=False)

    print(f"Saved merged file: {out_path} ({len(combined):,} rows)")


if __name__ == "__main__":
    main()
