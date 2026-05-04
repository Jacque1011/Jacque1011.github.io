#!/usr/bin/env python3
"""Preprocess long-format market data for spillover modeling.

Steps:
1) Pivot long -> wide
2) Compute log returns for price variables
3) Z-score standardization for level variables (e.g., GPR, VIX, DXY, rates)
4) Export cleaned long + quality report
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

PRICE_VARS = {"WTI", "Brent", "HenryHub", "SP500", "MSCIWorldProxy", "Gold", "Copper"}
LEVEL_ZSCORE_VARS = {"GPR", "DXY", "VIX", "US10Y", "EFFR"}


def zscore(x: pd.Series) -> pd.Series:
    mu = x.mean(skipna=True)
    sd = x.std(skipna=True)
    if pd.isna(sd) or sd == 0:
        return x * np.nan
    return (x - mu) / sd


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data_processed/market_with_gpr_long.csv")
    p.add_argument("--out", default="data_processed/model_input_long.csv")
    p.add_argument("--qc", default="reports/preprocess_qc.md")
    args = p.parse_args()

    df = pd.read_csv(args.input)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()

    wide = df.pivot_table(index="date", columns="variable", values="value", aggfunc="last").sort_index()

    out = pd.DataFrame(index=wide.index)
    for col in wide.columns:
        s = pd.to_numeric(wide[col], errors="coerce")
        if col in PRICE_VARS:
            out[col] = 100 * np.log(s).diff()
        elif col in LEVEL_ZSCORE_VARS:
            out[col] = zscore(s)
        else:
            out[col] = s

    long = out.reset_index().melt(id_vars="date", var_name="variable", value_name="value").sort_values(["date", "variable"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    long.to_csv(out_path, index=False)

    # QC report
    qc = long.copy()
    summary = (
        qc.groupby("variable")["value"]
        .agg(n_obs=lambda x: x.notna().sum(), missing=lambda x: x.isna().sum(), mean="mean", std="std")
        .reset_index()
    )

    qc_lines = [
        "# Preprocess QC Report",
        "",
        f"- Input: `{args.input}`",
        f"- Output: `{args.out}`",
        "",
        "| variable | n_obs | missing | mean | std |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        qc_lines.append(
            f"| {r['variable']} | {int(r['n_obs'])} | {int(r['missing'])} | {r['mean']:.6f} | {r['std']:.6f} |"
        )

    qc_path = Path(args.qc)
    qc_path.parent.mkdir(parents=True, exist_ok=True)
    qc_path.write_text("\n".join(qc_lines), encoding="utf-8")

    print(f"Saved cleaned data: {out_path} ({len(long):,} rows)")
    print(f"Saved QC report: {qc_path}")


if __name__ == "__main__":
    main()
