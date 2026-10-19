from pathlib import Path
import pandas as pd

# 1. Locate the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 2. Define the file paths (Change the longitudinal filename if needed)
baseline_file = PROJECT_ROOT / "data" / "raw" /"thai"/ "baseline and lab data.csv"
longitudinal_file = PROJECT_ROOT / "data" / "raw" / "thai"/"longitudinal_creatinine.csv" # <--- CHECK THIS NAME

print("--- INSPECTING BASELINE CSV ---")
if baseline_file.exists():
    df_base = pd.read_csv(baseline_file)
    print("Baseline Columns:", df_base.columns.tolist())
    # Check if there is any date column
    date_cols = [c for c in df_base.columns if 'date' in c.lower() or 'time' in c.lower()]
    print("Baseline date columns:", date_cols)
else:
    print("Baseline file NOT found at:", baseline_file)

print("\n--- INSPECTING LONGITUDINAL CSV ---")
if longitudinal_file.exists():
    df_long = pd.read_csv(longitudinal_file)
    print("Shape:", df_long.shape)
    print("Longitudinal Columns:", df_long.columns.tolist())
    print("\nFirst 5 rows:")
    print(df_long.head().to_string())
    
    # Check duplicates
    print("\nDuplicate (id, day) pairs:", df_long.duplicated(subset=['id', 'day']).sum())
    
    # Check creatinine values
    print("\nCreatinine Stats:")
    print(df_long['cr'].describe())
else:
    print("Longitudinal file NOT found at:", longitudinal_file)
    print("Files actually in data/raw:")
    raw_dir = PROJECT_ROOT / "data" / "raw"
    if raw_dir.exists():
        print([f.name for f in raw_dir.iterdir()])