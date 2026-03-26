import re
import csv
from pathlib import Path

BASE_DIR = Path("variance")
OUTPUT_CSV = BASE_DIR / "aggregated_stats.csv"

EXPECTED_METRICS = ["energy", "latency", "cpu", "memory"]
STAT_FIELDS = ["n", "mean", "std", "min", "p25", "median", "p75", "max", "cv"]


def parse_stats_file(file_path):
    result = {}

    # Method = parent folder (original / codex / sysllmatic)
    result["method"] = file_path.parent.name

    with open(file_path, "r") as f:
        lines = f.readlines()

    # ---- Header fields ----
    for line in lines:
        if line.startswith("app="):
            result["app"] = line.strip().split("=")[1]
        elif line.startswith("throughput_ops_per_s="):
            result["throughput_ops_per_s"] = float(line.strip().split("=")[1])

    # ---- Find statistics table ----
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("metric"):
            start_idx = i + 2
            break

    if start_idx is None:
        return None

    for line in lines[start_idx:]:
        if not line.strip():
            break

        parts = re.split(r"\s+", line.strip())
        if len(parts) < 10:
            continue

        metric = parts[0]
        if metric not in EXPECTED_METRICS:
            continue

        values = parts[1:10]

        for stat_name, value in zip(STAT_FIELDS, values):
            key = f"{metric}_{stat_name}"
            result[key] = int(value) if stat_name == "n" else float(value)

    return result


def main():
    rows = []

    # Recursively find all stats_*.txt files
    for txt_file in BASE_DIR.rglob("stats_*.txt"):
        parsed = parse_stats_file(txt_file)
        if parsed:
            rows.append(parsed)

    if not rows:
        print("No stats files found.")
        return

    # Define consistent column order
    header = ["method", "app", "throughput_ops_per_s"]

    for metric in EXPECTED_METRICS:
        for stat in STAT_FIELDS:
            header.append(f"{metric}_{stat}")

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Saved {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
