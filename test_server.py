from server import list_sheets, read_sheet_data
from dotenv import load_dotenv
import sys

load_dotenv()

print("--- Testing List Sheets ---")
sheets = list_sheets()
print(sheets)

print("\n--- Testing Read Data (data) ---")
# Using a valid sheet name found in the previous step
data = read_sheet_data(sheet_name="data", range_name="A1:F50")
print(data)

if (
    "Error" in data and "Error" not in sheets
):  # strict check if reading failed but listing worked
    print("\n[FAIL] Read data failed.")
    sys.exit(1)

print("\n[SUCCESS] Script executed.")
