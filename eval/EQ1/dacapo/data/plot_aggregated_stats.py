#!/usr/bin/env python
"""
Plot aggregated stats per app and metric comparing methods,
using 95% Confidence Intervals for error bars and a 1.0 baseline.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DEFAULT_METRICS = [
    "throughput_ops_per_s",
    "energy_mean",
    "latency_mean",
    "cpu_mean",
    "memory_mean",
]

DEFAULT_METHOD_ORDER = ["original", "codex", "sysllmatic", "compiler", "codex_and_compiler", "sysllmatic_and_compiler"]

METRIC_LABELS = {
    "throughput_ops_per_s": "Throughput",
    "energy_mean": "Energy",
    "latency_mean": "Latency",
    "cpu_mean": "CPU",
    "memory_mean": "Memory",
}

def std_for_metric(df: pd.DataFrame, metric: str) -> str | None:
    if metric.endswith("_mean"):
        cand = metric[:-5] + "_std"
        return cand if cand in df.columns else None
    return None

def throughput_std_from_latency(app_df: pd.DataFrame) -> pd.Series | None:
    if "throughput_ops_per_s" not in app_df.columns:
        return None
    if "latency_mean" not in app_df.columns or "latency_std" not in app_df.columns:
        return None
    rel = app_df["latency_std"] / app_df["latency_mean"]
    return app_df["throughput_ops_per_s"] * rel

def ratio_std(num: pd.Series, num_std: pd.Series, den: pd.Series, den_std: pd.Series) -> pd.Series:
    rel = (num_std / num).pow(2) + (den_std / den).pow(2)
    return (num / den) * rel.pow(0.5)

def build_improvement_df(df: pd.DataFrame, metrics: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    apps = sorted(df["app"].unique())
    methods = [m for m in DEFAULT_METHOD_ORDER if m in df["method"].unique() and m != "original"]
    rows = []
    std_rows = []

    for app in apps:
        base = df[(df["app"] == app) & (df["method"] == "original")]
        if base.empty:
            continue
        for method in methods:
            cur = df[(df["app"] == app) & (df["method"] == method)]
            if cur.empty:
                continue
            for metric in metrics:
                if metric == "throughput_ops_per_s":
                    num = cur[metric].iloc[0]
                    den = base[metric].iloc[0]
                    num_std = None
                    den_std = None
                    if "latency_mean" in df.columns and "latency_std" in df.columns:
                        num_std = throughput_std_from_latency(cur).iloc[0]
                        den_std = throughput_std_from_latency(base).iloc[0]
                else:
                    num = base[metric].iloc[0]
                    den = cur[metric].iloc[0]
                    std_col = std_for_metric(df, metric)
                    num_std = None
                    den_std = None
                    if std_col is not None:
                        num_std = base[std_col].iloc[0]
                        den_std = cur[std_col].iloc[0]

                val = num / den if den != 0 else float("nan")
                rows.append({"app": app, "method": method, "metric": metric, "value": val})
                
                if num_std is not None and den_std is not None and den != 0 and num != 0:
                    std_val = ratio_std(
                        pd.Series([num]),
                        pd.Series([num_std]),
                        pd.Series([den]),
                        pd.Series([den_std]),
                    ).iloc[0]
                else:
                    std_val = float("nan")
                std_rows.append({"app": app, "method": method, "metric": metric, "value": std_val})

    return pd.DataFrame(rows), pd.DataFrame(std_rows)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plot aggregated stats per app/metric.")
    p.add_argument("--input", default="variance/aggregated_stats.csv", help="Input CSV path")
    p.add_argument("--out-dir", default="variance/plots", help="Output directory")
    p.add_argument(
        "--metrics",
        nargs="+",
        default=DEFAULT_METRICS,
        help="Metrics to plot (column names)",
    )
    p.add_argument(
        "--n-runs", 
        type=int, 
        default=20, 
        help="Number of runs per benchmark (used to calculate 95% CI)"
    )
    return p.parse_args()

def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)

    missing = [m for m in args.metrics if m not in df.columns]
    if missing:
        raise SystemExit(f"Missing metrics in CSV: {missing}")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    method_order = [m for m in DEFAULT_METHOD_ORDER if m in df["method"].unique() and m != "original"]
    apps = sorted(df["app"].unique())
    mean_df, std_df = build_improvement_df(df, args.metrics)
    
    ci_df = std_df.copy()
    ci_df["value"] = ci_df["value"] * 1.96 / np.sqrt(args.n_runs)
    
    mean_df.to_csv(out_dir / "improvements.csv", index=False)

    n_apps = len(apps)
    n_cols = 3
    n_rows = (n_apps + n_cols - 1) // n_cols
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(4.6 * n_cols, 3.6 * n_rows),
        constrained_layout=True,
        squeeze=False,
    )
    
    app_names = {
        "biojava": "Biojava",
        "fop": "Fop",
        "pmd": "PMD",
        "zxing": "ZXing",
        "graphchi": "GraphChi"
    }

    for idx, app in enumerate(apps):
        r = idx // n_cols
        c = idx % n_cols
        ax = axes[r][c]
        pivot = mean_df[mean_df["app"] == app].pivot(index="metric", columns="method", values="value")
        pivot = pivot.reindex(index=args.metrics, columns=method_order)
        
        yerr_matrix = None
        ci_pivot = ci_df[ci_df["app"] == app].pivot(index="metric", columns="method", values="value")
        if not ci_pivot.empty:
            ci_pivot = ci_pivot.reindex(index=args.metrics, columns=method_order)
            yerr_matrix = ci_pivot.to_numpy()

        x = range(len(args.metrics))
        n_methods = len(method_order)
        width = 0.8 / max(n_methods, 1)
        colors = ["#fc8d62", "#3f70e3", "#4abe99", "#eaa380", "#83a3e7"]
        
        # Add a baseline at 1.0 (no improvement line)
        ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, zorder=1)

        for i, method in enumerate(method_order):
            y = pivot[method].to_numpy()
            yerr = None
            if yerr_matrix is not None:
                yerr = yerr_matrix[:, i]
            ax.bar(
                [v + i * width for v in x],
                y,
                width=width,
                label=method,
                yerr=yerr,
                capsize=3,
                color=colors[i % len(colors)],
                zorder=2 # Ensure bars are drawn over the baseline
            )

        ax.set_xticks([v + width * (n_methods - 1) / 2 for v in x], [METRIC_LABELS.get(m, m) for m in args.metrics])
        ax.tick_params(axis="x", rotation=25)
        ax.set_title(app_names.get(app, app))
        ax.set_ylabel("Improvement (x)")

    for idx in range(n_apps, n_rows * n_cols):
        r = idx // n_cols
        c = idx % n_cols
        axes[r][c].set_visible(False)

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower right", ncol=1, fontsize=12)
    fig.suptitle("Improvement vs original (higher is better)   Error bars denote 95% Confidence Intervals", fontsize=15)
    out_path = out_dir / "baseline_dacapo.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

if __name__ == "__main__":
    main()