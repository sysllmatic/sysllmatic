import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# === Step 1: Load and Parse Dataset ===
def load_dataset(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# === Step 2: Extract Optimization Patterns ===
def extract_patterns(data):
    pattern_hierarchy = defaultdict(lambda: defaultdict(int))
    for entry in data:
        pattern_str = entry.get("optimization_pattern", "")
        if ";" in pattern_str:
            high_level, sub = pattern_str.split(";", 1)
            high_level = high_level.strip()
            sub = sub.strip()
            pattern_hierarchy[high_level][sub] += 1
    return pattern_hierarchy

# === Step 3: Convert to DataFrame ===
def to_dataframe(pattern_hierarchy):
    records = []
    for high_level, sub_dict in pattern_hierarchy.items():
        for sub, count in sub_dict.items():
            records.append((high_level, sub, count))
    return pd.DataFrame(records, columns=["HighLevel", "SubPattern", "Count"])

# === Step 4: Plot Stacked Bar Chart ===
def plot_stacked_chart(df):
    pivot_df = df.pivot_table(index="HighLevel", columns="SubPattern", values="Count", aggfunc="sum").fillna(0)
    pivot_df.plot(kind="bar", stacked=True, figsize=(16, 6))
    plt.title("Stacked Column Chart of Optimization Patterns")
    plt.ylabel("Count")
    plt.xlabel("High-Level Optimization Patterns")
    plt.xticks(rotation=45, ha='right')
    plt.legend(title="Sub-Patterns", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig("optimization_patterns.png", bbox_inches="tight")
    plt.show()

# === Main ===
if __name__ == "__main__":
    dataset = load_dataset("output.json")  # Replace with your filename
    pattern_hierarchy = extract_patterns(dataset)
    df = to_dataframe(pattern_hierarchy)
    plot_stacked_chart(df)
