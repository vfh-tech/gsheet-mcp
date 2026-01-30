import os
import io  # noqa: F401
import pandas as pd
from typing import List, Any, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# Configuration
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

mcp = FastMCP("Google Sheet Manager")


def get_service():
    """Authenticates and returns the Google Sheets API service."""
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("SERVICE_ACCOUNT_FILE environment variable not set")

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Service account file not found: {SERVICE_ACCOUNT_FILE}"
        )

    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
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
        sheet_metadata = (
            service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        )
        sheets = sheet_metadata.get("sheets", [])

        if not sheets:
            return "No sheets found in this spreadsheet."

        data = []
        for sheet in sheets:
            props = sheet["properties"]
            data.append(
                {
                    "Index": props.get("index"),
                    "Title": props.get("title"),
                    "Sheet ID": props.get("sheetId"),
                    "Grid Properties": str(props.get("gridProperties", {})),
                }
            )

        df = pd.DataFrame(data)
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error listing sheets: {e}"


@mcp.tool()
def read_sheet_data(
    sheet_name: str, range_name: str = None, last_20_rows: bool = False
) -> str:
    """
    Reads data from a specific sheet.

    Args:
        sheet_name (str): The name of the sheet to read (e.g., 'Sheet1')
        range_name (str): Optional A1 notation range (e.g., 'A1:C10'). If omitted, reads the whole sheet.
        last_20_rows (bool): If True, reads only the last 20 rows of data (plus header). Default False.

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
        elif last_20_rows:
            # Get sheet metadata to find row count
            sheet_metadata = (
                service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            )
            sheets = sheet_metadata.get("sheets", [])
            row_count = None
            for sheet in sheets:
                if sheet["properties"]["title"] == sheet_name:
                    row_count = sheet["properties"]["gridProperties"]["rowCount"]
                    break

            if row_count and row_count > 1:
                # Calculate range for last 20 rows (keeping header at row 1)
                # If sheet has 1000 rows, read rows 981-1000 (20 rows)
                start_row = max(
                    2, row_count - 19
                )  # Start from row 2 if less than 20 rows
                target_range = f"'{sheet_name}'!A{start_row}:ZZ{row_count}"
            else:
                # Fallback: read entire sheet
                target_range = sheet_name

        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID, range=target_range)
            .execute()
        )

        values = result.get("values", [])

        if not values:
            return "No data found."

        if last_20_rows and not range_name:
            # When reading last 20 rows, we need to get header separately
            header_result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!1:1")
                .execute()
            )
            header = header_result.get("values", [[]])[0]
            data = values  # values already contains the last 20 rows
        else:
            # First row is usually the header
            header = values[0]
            data = values[1:]

        # Normalize row lengths
        max_len = len(header)
        for row in data:
            if len(row) < max_len:
                row.extend([""] * (max_len - len(row)))
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


@mcp.tool()
def create_sheet(title: str) -> str:
    """
    Creates a new sheet with the given title.

    Args:
        title (str): The title for the new sheet.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        body = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body
        ).execute()
        return f"Successfully created sheet '{title}'."
    except Exception as e:
        return f"Error creating sheet: {e}"


@mcp.tool()
def rename_sheet(old_title: str, new_title: str) -> str:
    """
    Renames an existing sheet.

    Args:
        old_title (str): The current name of the sheet.
        new_title (str): The new name for the sheet.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        # Find sheetId
        sheet_metadata = (
            service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        )
        sheets = sheet_metadata.get("sheets", [])
        sheet_id = None
        for sheet in sheets:
            if sheet["properties"]["title"] == old_title:
                sheet_id = sheet["properties"]["sheetId"]
                break

        if sheet_id is None:
            return f"Error: Sheet '{old_title}' not found."

        body = {
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "title": new_title},
                        "fields": "title",
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body
        ).execute()
        return f"Successfully renamed sheet '{old_title}' to '{new_title}'."
    except Exception as e:
        return f"Error renaming sheet: {e}"


@mcp.tool()
def append_data(sheet_name: str, values: List[List[Any]]) -> str:
    """
    Appends rows of data to a specific sheet.
    WARNING: This tool modifies data. Confirm with the user before executing.

    Args:
        sheet_name (str): The name of the sheet.
        values (List[List[Any]]): A list of rows, where each row is a list of values.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        body = {"values": values}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return f"Successfully appended {len(values)} rows to '{sheet_name}'."
    except Exception as e:
        return f"Error appending data: {e}"


def index_to_column(index: int) -> str:
    """Converts a 0-based index to an A1 column letter."""
    result = ""
    while index >= 0:
        result = chr(ord("A") + (index % 26)) + result
        index = (index // 26) - 1
    return result


@mcp.tool()
def add_column(sheet_name: str, header: str, values: List[Any] = None) -> str:
    """
    Adds a new column to the right of existing data.
    WARNING: This tool modifies data. Confirm with the user before executing.

    Args:
        sheet_name (str): The name of the sheet.
        header (str): The header title for the new column.
        values (List[Any]): Optional list of values for the column (starting from row 2).
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()

        # Get current column count by reading the first row
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=SPREADSHEET_ID, range=f"'{sheet_name}'!1:1")
            .execute()
        )
        existing_headers = result.get("values", [[]])[0]
        col_index = len(existing_headers)
        col_letter = index_to_column(col_index)

        # Add header
        header_range = f"'{sheet_name}'!{col_letter}1"
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range,
            valueInputOption="RAW",
            body={"values": [[header]]},
        ).execute()

        # Add values if provided
        if values:
            values_range = f"'{sheet_name}'!{col_letter}2"
            body_values = [[v] for v in values]  # Must be list of lists (vertical)
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=values_range,
                valueInputOption="USER_ENTERED",
                body={"values": body_values},
            ).execute()

        return f"Successfully added column '{header}' at index {col_letter}."
    except Exception as e:
        return f"Error adding column: {e}"


def get_sheet_id(service, title: str) -> Optional[int]:
    """Helper to find the sheetId for a given sheet title."""
    try:
        sheet_metadata = (
            service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        )
        sheets = sheet_metadata.get("sheets", [])
        for sheet in sheets:
            if sheet["properties"]["title"] == title:
                return sheet["properties"]["sheetId"]
    except Exception:
        pass
    return None


@mcp.tool()
def delete_sheet(sheet_name: str) -> str:
    """
    Deletes a specific sheet.
    WARNING: Irreversible operation. Confirm with user.

    Args:
        sheet_name (str): The name of the sheet to delete.
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        sheet_id = get_sheet_id(service, sheet_name)

        if sheet_id is None:
            return f"Error: Sheet '{sheet_name}' not found."

        body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body
        ).execute()
        return f"Successfully deleted sheet '{sheet_name}'."
    except Exception as e:
        return f"Error deleting sheet: {e}"


@mcp.tool()
def delete_row(sheet_name: str, start_index: int, end_index: int) -> str:
    """
    Deletes rows from start_index (inclusive) to end_index (exclusive).
    0-based index. e.g. 0 is the first row.
    WARNING: Irreversible operation. Confirm with user.

    Args:
        sheet_name (str): The name of the sheet.
        start_index (int): The 0-based starting row index (inclusive).
        end_index (int): The 0-based ending row index (exclusive).
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        sheet_id = get_sheet_id(service, sheet_name)

        if sheet_id is None:
            return f"Error: Sheet '{sheet_name}' not found."

        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": end_index,
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body
        ).execute()
        return (
            f"Successfully deleted rows {start_index} to {end_index} in '{sheet_name}'."
        )
    except Exception as e:
        return f"Error deleting rows: {e}"


@mcp.tool()
def delete_column(sheet_name: str, start_index: int, end_index: int) -> str:
    """
    Deletes columns from start_index (inclusive) to end_index (exclusive).
    0-based index. e.g. 0 is Column A.
    WARNING: Irreversible operation. Confirm with user.

    Args:
        sheet_name (str): The name of the sheet.
        start_index (int): The 0-based starting column index (inclusive).
        end_index (int): The 0-based ending column index (exclusive).
    """
    if not SPREADSHEET_ID:
        return "Error: SPREADSHEET_ID environment variable is not set."

    try:
        service = get_service()
        sheet_id = get_sheet_id(service, sheet_name)

        if sheet_id is None:
            return f"Error: Sheet '{sheet_name}' not found."

        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_index,
                            "endIndex": end_index,
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body
        ).execute()
        return f"Successfully deleted columns {start_index} to {end_index} in '{sheet_name}'."
    except Exception as e:
        return f"Error deleting columns: {e}"


def run():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
