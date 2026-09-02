import os
import shutil
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# ==========================================
# 1. DEFINE YOUR PATHS HERE
# ==========================================
# Update CSV_PATH and IMAGE_DIR with your actual input file/folder paths
CSV_PATH = r"C:\Users\viraj\Downloads\FETAL_PLANES_ZENODO\FETAL_PLANES_DB_data.csv" 
IMAGE_DIR = r"C:\Users\viraj\Downloads\FETAL_PLANES_ZENODO\Images" 

OUTPUT_CSV_PATH = r"C:\Users\viraj\Downloads\patientsplit801010\patient_split_80_10_10.csv"
PHYSICAL_SPLIT_DIR = r"C:\Users\viraj\Downloads\patientsplit801010"

# Target column used to create class folders (e.g., Abdomen, Femur, Brain, Thorax, Cervix, Other)
CLASS_COLUMN = 'Plane'

# ==========================================
# 2. LOAD DATA & PERFORM SPLIT
# ==========================================
if not os.path.exists(CSV_PATH):
    print(f"\n[ERROR] File not found at: {CSV_PATH}")
    print("Please check the path in line 11 of your script.")
    exit()

print("Loading dataset...")
# FETAL_PLANES_ZENODO uses semicolon delimiters
df = pd.read_csv(CSV_PATH, sep=';')

# Clean hidden spaces from column names
df.columns = df.columns.str.strip()

patient_col = 'Patient_num'
image_col = 'Image_name'

print(f"Using Patient Column: '{patient_col}'")
print(f"Using Image Column: '{image_col}'")
print(f"Organizing by Class Column: '{CLASS_COLUMN}'")

# Get list of unique patient identifiers
unique_patients = df[patient_col].unique()
print(f"Total unique patients found: {len(unique_patients)}")

# Split 1: 80% Train, 20% Temp (Val + Test)
train_patients, temp_patients = train_test_split(
    unique_patients, 
    test_size=0.20, 
    random_state=42
)

# Split 2: Divide Temp group in half (10% Val, 10% Test)
val_patients, test_patients = train_test_split(
    temp_patients, 
    test_size=0.50, 
    random_state=42
)

# Map patient assignments back to individual rows
df.loc[df[patient_col].isin(train_patients), 'Split'] = 'train'
df.loc[df[patient_col].isin(val_patients), 'Split'] = 'val'
df.loc[df[patient_col].isin(test_patients), 'Split'] = 'test'


# ==========================================
# 3. VERIFY & SAVE NEW CSV
# ==========================================
print("\n--- Split Verification ---")
print(f"Train Patients: {len(train_patients)} | Train Images: {len(df[df['Split'] == 'train'])}")
print(f"Val Patients:   {len(val_patients)}   | Val Images:   {len(df[df['Split'] == 'val'])}")
print(f"Test Patients:  {len(test_patients)}   | Test Images:  {len(df[df['Split'] == 'test'])}")

Path(OUTPUT_CSV_PATH).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_CSV_PATH, index=False, sep=';')
print(f"\nSuccess! Updated dataset saved to: {OUTPUT_CSV_PATH}")


# ==========================================
# 4. CREATE CLASS SUBFOLDERS & COPY IMAGES
# ==========================================
print("\nCreating physical folders with class subfolders...")

for split_name in ['train', 'val', 'test']:
    split_df = df[df['Split'] == split_name]
    
    for _, row in split_df.iterrows():
        # Get category name (e.g., Abdomen, Femur, Brain)
        class_name = str(row[CLASS_COLUMN]).strip()
        
        # Create folder structure: C:\...\patientsplit801010\train\Abdomen
        split_dir = Path(PHYSICAL_SPLIT_DIR) / split_name / class_name
        split_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = str(row[image_col]).strip()
        src_path = Path(IMAGE_DIR) / base_name
        dest_filename = base_name

        # Resolve image extensions if missing in CSV entries
        if not src_path.exists():
            for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                check_path = Path(IMAGE_DIR) / f"{base_name}{ext}"
                if check_path.exists():
                    src_path = check_path
                    dest_filename = f"{base_name}{ext}"
                    break
        
        dest_path = split_dir / dest_filename
        
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
        else:
            print(f"Warning: Could not find image at {src_path}")
            
print(f"\nPhysical folder creation complete! Check '{PHYSICAL_SPLIT_DIR}'.")
