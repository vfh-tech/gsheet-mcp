import os
import io
import pandas as pd
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# Configuration
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

mcp = FastMCP("Google Sheet Reader (API)")

def get_service():
    """Authenticates and returns the Google Sheets API service."""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("SERVICE_ACCOUNT_FILE environment variable not set")
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service

@mcp.tool()
def list_sheets() -> str:
    """
    Lists all sheets in the configured spreadsheet.
    
    Returns:
        Markdown table containing Sheet ID, Title, and Index.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        if not sheets:
            return "No sheets found in this spreadsheet."

        data = []
        for sheet in sheets:
            props = sheet['properties']
            data.append({
                "Index": props.get('index'),
                "Title": props.get('title'),
                "Sheet ID": props.get('sheetId'),
                "Grid Properties": str(props.get('gridProperties', {}))
            })
            
        df = pd.DataFrame(data)
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error listing sheets: {e}"

@mcp.tool()
def read_sheet_data(sheet_name: str, range_name: str = None) -> str:
    """
    Reads data from a specific sheet.
    
    Args:
        sheet_name (str): The name of the sheet to read (e.g., 'Sheet1')
        range_name (str): Optional A1 notation range (e.g., 'A1:C10'). If omitted, reads the whole sheet.
        
    Returns:
        Markdown table of the data.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        
        # Construct range
        target_range = sheet_name
        if range_name:
            target_range = f"'{sheet_name}'!{range_name}"
            
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=target_range).execute()
        
        values = result.get('values', [])
        
        if not values:
            return "No data found."

        # First row is usually the header
        header = values[0]
        data = values[1:]
        
        # Normalize row lengths
        max_len = len(header)
        for row in data:
            if len(row) < max_len:
                row.extend([''] * (max_len - len(row)))
            elif len(row) > max_len:
                 # Extend header if data has more columns
                 new_cols = len(row) - max_len
                 for i in range(new_cols):
                     header.append(f"Col_{max_len + i + 1}")
                 max_len = len(header)

        df = pd.DataFrame(data, columns=header)
        return df.to_markdown(index=False)

    except Exception as e:
        return f"Error reading sheet data: {e}"

if __name__ == "__main__":
    mcp.run()
