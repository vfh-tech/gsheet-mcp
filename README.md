# Google Sheet MCP Server

An MCP (Model Context Protocol) server that allows AI agents to read and interact with Google Sheets using the Google Sheets API v4.

## Features

- **List Sheets**: Retrieve a list of all sheets in a spreadsheet with their names, IDs, and grid properties.
- **Read Content**: Read data from specific sheets or ranges, returned as formatted Markdown tables.
- **Metadata**: Access sheet-level metadata like column and row counts.

## Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: `uv` (recommended) or `pip`
- **Google Cloud Project**:
    - "Google Sheets API" enabled.
    - Service Account created with a JSON key file.
- **Access**: The Service Account email must have "Viewer" or "Editor" access to the target Google Sheet.

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

- `list_sheets()`: Lists all sheets in the configured spreadsheet.
- `read_sheet_data(sheet_name: str, range_name: str = None)`: Reads data from the specified sheet.
