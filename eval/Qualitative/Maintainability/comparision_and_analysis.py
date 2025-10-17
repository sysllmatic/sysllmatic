#!/usr/bin/env python3
import sys
import os
import pandas as pd

METRICS = ["Total nloc", "Avg.NLOC", "AvgCCN", "Fun Cnt", "Avg.token"]

def load_app_csv(app, flavor):
    """
    flavor in {"original", "optimized"}.
    Expects files like: <app>_original.csv and <app>_optimized.csv
    """
    fname = f"data/{app}_{flavor}.csv"
    if not os.path.isfile(fname):
        raise FileNotFoundError(f"Missing file: {fname}")
    df = pd.read_csv(fname)
    # Ensure required columns exist
    missing = [c for c in METRICS if c not in df.columns]
    if missing:
        raise ValueError(f"{fname} is missing columns: {missing}")
    return df

def summarize(df):
    """Return dict of means for the metrics we care about."""
    return {metric: df[metric].mean() for metric in METRICS}

def compare_app(app):
    dorig = load_app_csv(app, "original")
    dopt  = load_app_csv(app, "optimized")

    s_orig = summarize(dorig)
    s_opt  = summarize(dopt)

    rows = []
    for metric in METRICS:
        delta = s_opt[metric] - s_orig[metric]
        delta_pct = (delta / s_orig[metric] * 100.0) if s_orig[metric] != 0 else float("nan")
        # Pretty column naming
        display_name = metric
        if metric == "Fun Cnt":
            display_name = "Avg Functions Cnt"
        elif metric == "Avg.token":
            display_name = "Avg Tokens"
        elif metric == "Total nloc":
            display_name = "Avg Total NLOC"
        rows.append({
            "App": app,
            "Metric": display_name,
            "Original": round(s_orig[metric], 3),
            "Optimized": round(s_opt[metric], 3),
            "Delta": round(delta, 3),
            "Delta %": round(delta_pct, 2),
        })
    return rows

def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_ccn.py <app1> [<app2> ...]")
        sys.exit(1)

    apps = sys.argv[1:]
    all_rows = []
    for app in apps:
        try:
            all_rows.extend(compare_app(app))
        except Exception as e:
            print(f"[WARN] Skipping '{app}': {e}")

    if not all_rows:
        print("No results produced. Check file names and columns.")
        sys.exit(2)

    out = pd.DataFrame(all_rows, columns=["App", "Metric", "Original", "Optimized", "Delta", "Delta %"])
    out.to_csv("comparison_summary.csv", index=False)
    print(out.to_string(index=False))
    print("\nWrote comparison_summary.csv")

if __name__ == "__main__":
    main()
