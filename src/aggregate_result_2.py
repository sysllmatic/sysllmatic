import csv

csv_path = 'final_results/baseline/profcodegen/profcodegen_humaneval.csv'

speedups = []
optimized = []
with open(csv_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            speedup = float(row['Speedup'])
            if speedup > 0:
                # Append to the list
                speedups.append(speedup)
            if speedup >= 1.1:
                optimized.append(speedup)
        except (KeyError, ValueError):
            print(f"Skipping row due to missing or invalid data: {row}")
            continue

if speedups:
    avg_speedup = sum(speedups) / len(speedups)
    print(f"correctness: {len(speedups)/ 164}")
    print(f'Average Speedup: {round(avg_speedup, 3)}')
    print(f'Optimized Speedup: {round(len(optimized) / 164 * 100, 3)}%')
else:
    print('No valid speedup data found.')