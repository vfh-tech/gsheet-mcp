# Google Sheet MCP Server

An MCP (Model Context Protocol) server that allows AI agents to read, write, and manage Google Sheets using the Google Sheets API v4.

## Features

- **List Sheets**: Retrieve a list of all sheets in a spreadsheet with their names, IDs, and grid properties.
- **Read Content**: Read data from specific sheets or ranges, returned as formatted Markdown tables.
- **Write Content**: API to create sheets, append data, and add columns.
- **Manage Structure**: Rename sheets and delete sheets, columns, or rows.

## Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: `uv` (recommended) or `pip`
- **Google Cloud Project**:
    - "Google Sheets API" enabled.
    - Service Account created with a JSON key file.
- **Access**: The Service Account email **MUST** have **"Editor"** access to the target Google Sheet to perform write operations.

## Getting service-account-key.json

1.  **Create Project**: Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
2.  **Enable API**: Search for "Google Sheets API" and click **Enable**.
3.  **Create Service Account**:
    - Go to **IAM & Admin** > **Service Accounts**.
    - Click **Create Service Account**.
    - Name it (e.g., `sheet-mcp-bot`) and click **Create and Continue**.
    - Grant **"Editor"** role, then click **Done**.
4.  **Generate Key**:
    - Click on the newly created Service Account email.
    - Go to the **Keys** tab > **Add Key** > **Create new key**.
    - Select **JSON** and click **Create**.
    - The file will download automatically. Rename it to `service-account-key.json`.
5.  **Share Sheet**: Open your target Google Sheet, click **Share**, and paste the Service Account email (found in the JSON file under `client_email`) with **Editor** permissions.

## Installation

1.  **Clone/Open** this repository.
2.  **Install dependencies**:
    ```bash
    uv sync
    # or
    pip install mcp pandas python-dotenv google-api-python-client google-auth
    ```

## Configuration

1.  **Service Account**: Place your Google Service Account JSON key in the project root and name it `service-account-key.json` (or update `.env` to point to its path).
2.  **Environment Variables**: Create a `.env` file:
    ```env
    SPREADSHEET_ID=your_spreadsheet_id_here
    SERVICE_ACCOUNT_FILE=service-account-key.json
    ```
    *Tip: The Spreadsheet ID is the long string in your sheet's URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`*

## Usage with MCP Clients

Add this configuration to your MCP settings file (e.g., `claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "google-sheet": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/sheet-mcp",
        "run",
        "server.py"
      ],
      "env": {
        "SPREADSHEET_ID": "your_spreadsheet_id_here",
        "SERVICE_ACCOUNT_FILE": "service-account-key.json"
      }
    }
  }
}
```

## Testing

A verification script is included to test the connection and tools:

```bash
uv run test_server.py
```

## Tools Available

### Read Operations
- `list_sheets()`: Lists all sheets in the configured spreadsheet.
- `read_sheet_data(sheet_name: str, range_name: str = None, last_20_rows: bool = False)`: Reads data from the specified sheet. Set `last_20_rows=True` to read only the last 20 rows (plus header).

### Write Operations
- `create_sheet(title: str)`: Creates a new sheet (tab).
- `rename_sheet(old_title: str, new_title: str)`: Renames an existing sheet.
- `append_data(sheet_name: str, values: List[List[Any]])`: Appends rows of data to the bottom of a sheet.
- `add_column(sheet_name: str, header: str, values: List[Any] = None)`: Adds a new column to the right of the existing data, with an optional header and values.

### Delete Operations (Destructive)
- `delete_sheet(sheet_name: str)`: Deletes an entire sheet.
- `delete_row(sheet_name: str, start_index: int, end_index: int)`: Deletes rows within a specified range.
- `delete_column(sheet_name: str, start_index: int, end_index: int)`: Deletes columns within a specified range.
