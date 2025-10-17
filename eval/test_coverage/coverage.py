#!/usr/bin/env python3
import csv
import sys

def compute_coverage(csv_file):
    totals = {
        "INSTRUCTION": {"missed": 0, "covered": 0},
        "BRANCH": {"missed": 0, "covered": 0},
        "LINE": {"missed": 0, "covered": 0},
        "METHOD": {"missed": 0, "covered": 0},
    }

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            totals["INSTRUCTION"]["missed"] += int(row["INSTRUCTION_MISSED"])
            totals["INSTRUCTION"]["covered"] += int(row["INSTRUCTION_COVERED"])
            totals["BRANCH"]["missed"] += int(row["BRANCH_MISSED"])
            totals["BRANCH"]["covered"] += int(row["BRANCH_COVERED"])
            totals["LINE"]["missed"] += int(row["LINE_MISSED"])
            totals["LINE"]["covered"] += int(row["LINE_COVERED"])
            totals["METHOD"]["missed"] += int(row["METHOD_MISSED"])
            totals["METHOD"]["covered"] += int(row["METHOD_COVERED"])

    print("=== Overall Coverage ===")
    for metric, data in totals.items():
        total = data["missed"] + data["covered"]
        percent = 100.0 * data["covered"] / total if total > 0 else 0.0
        print(f"{metric:11s}: {percent:6.2f}%  ({data['covered']}/{total})")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python coverage_summary.py <jacoco.csv>")
        sys.exit(1)
    compute_coverage(sys.argv[1])
