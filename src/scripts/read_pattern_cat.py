from dotenv import load_dotenv
import pandas as pd
import json
import os

load_dotenv()
USER_PREFIX = os.getenv("USER_PREFIX")

def get_patterns(file_path: str):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    data = df.to_dict(orient="records")
    filtered_data = [{k: v for k, v in entry.items() if k != "Reference"} for entry in data]
    res = json.dumps(filtered_data, indent=4)
    return res

if __name__ == "__main__":
    file_path = f"{USER_PREFIX}/pattern_catalog/energy_patterns.xlsx"
    res = get_patterns(file_path=file_path)
    print(res)