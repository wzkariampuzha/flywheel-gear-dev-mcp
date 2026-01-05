# Flywheel Gear Development MCP Server

An MCP (Model Context Protocol) server that provides fresh Flywheel documentation for gear development. Designed for use with Claude Code CLI.

## Features

- **Fresh documentation on startup**: Fetches latest docs every time the server starts
- **10 curated documentation sources**: Flywheel gear libraries, APIs, DICOM standard, and guides
- **Deprecation filtering**: Automatically removes deprecated content to keep Claude focused on current APIs
- **Easy configuration**: Add/remove documentation sources via `config.yaml`
- **Parallel fetching**: Fast startup with async parallel downloads
- **Smart parsing**: Converts HTML/XML/JSON to clean markdown

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) or pip

### Install from source

```bash
# Clone the repository
cd flywheel-gear-dev-mcp

# Install dependencies with uv
uv sync

# Or with pip (after creating a virtual environment)
pip install -e .
```

## Configuration for Claude Code

### Option 1: Using the CLI (Recommended)

Add the MCP server using the `claude mcp add` command:

```bash
claude mcp add flywheel-gear-dev \
  --scope local \
  -- uv run --directory /absolute/path/to/flywheel-gear-dev-mcp flywheel-gear-mcp
```

Replace `/absolute/path/to/flywheel-gear-dev-mcp` with the actual path to this project.

### Option 2: Using .mcp.json

Create or edit `.mcp.json` in your project directory:

```json
{
  "mcpServers": {
    "flywheel-gear-dev": {
      "command": "uv",
      "args": ["run", "flywheel-gear-mcp"]
    }
  }
}
```

This will make the MCP server available when working in this project directory.

## Usage

### Starting the server

The server is automatically started by Claude Code when you launch a session. No manual start needed!

### Testing the server manually

To verify the server works before configuring it with Claude Code:

```bash
# Run the server (will start and wait for MCP messages)
uv run flywheel-gear-mcp

# Run with verbose logging
uv run flywheel-gear-mcp --verbose
```

### Logging

The server creates both console and file logs:

- **Console**: INFO level by default, DEBUG with `--verbose` flag
- **File logs**: Written to `logs/flywheel-gear-mcp.log` (always DEBUG level)
- **Rotation**: 10MB max per file, 5 backup files kept
- **Location**: `logs/` directory in your current working directory

The `logs/` directory is automatically created on first run and is excluded from git via `.gitignore`.

### Using the tools in Claude Code

Once configured, you can ask Claude to use the documentation tools:

```
"Can you get the fw-gear documentation?"
"Show me the DICOM standard data dictionary"
"What are the gear manifest schema requirements?"
```

### Available tools

- `get_fw_gear_docs` - fw-gear library documentation
- `get_fw_classification_docs` - fw-classification library
- `get_fw_file_docs` - fw-file library
- `get_flywheel_api_docs` - Flywheel platform Python API
- `get_dicom_standard` - DICOM standard (filtered to data dictionary and transfer syntaxes)
- `get_file_types_guide` - Flywheel file types guide
- `get_bids_guide` - BIDS in Flywheel guide
- `get_batch_gears_guide` - Batch gear execution guide
- `get_gear_specs` - Gear specifications
- `get_manifest_schema` - Gear manifest JSON schema
- `list_available_docs` - List all cached documentation sources

## Customizing documentation sources

Edit `config.yaml` to add, remove, or modify documentation sources:

```yaml
documentation_sources:
  - tool_name: get_my_custom_docs
    display_name: "My Custom Documentation"
    description: "Description here"
    urls:
      - https://example.com/docs
    type: html  # or xml, json, gitlab_repo
    strip_deprecated: true
```

### Supported types

- `html` - HTML documentation (auto-converts to markdown)
- `xml` - XML documentation (for DICOM standard)
- `json` - JSON schemas
- `gitlab_repo` - GitLab repository markdown files

### Refresh documentation

To fetch fresh documentation, simply restart the MCP server by restarting Claude Code.

## Troubleshooting

### Server won't start

1. **Check config path**: Ensure `cwd` in your MCP config points to the directory with `config.yaml`
2. **Check Python version**: Requires Python 3.13+
3. **Check dependencies**: Run `uv sync` again
4. **Check log files**: Review `logs/flywheel-gear-mcp.log` for detailed error messages

### Documentation not loading

1. **Check network**: Ensure you can access Flywheel documentation URLs
2. **Check logs**: Review `logs/flywheel-gear-mcp.log` or run with verbose flag: `flywheel-gear-mcp --verbose`
3. **Test URLs**: Verify URLs in `config.yaml` are accessible

### Tools not appearing in Claude Code

1. **Restart Claude Code** after configuration changes
2. **Check config.json syntax**: Ensure valid JSON
3. **Check server status**: Look for MCP server errors in Claude Code logs

## Development

### Project structure

```
flywheel-gear-dev-mcp/
├── src/flywheel_gear_mcp/
│   ├── __init__.py
│   ├── server.py       # MCP server entry point
│   ├── fetcher.py      # Async HTTP fetching and caching
│   ├── parsers.py      # HTML/XML/JSON parsing
│   └── tools.py        # Dynamic tool generation
├── config.yaml         # Documentation sources (user-editable)
├── pyproject.toml      # Dependencies and metadata
└── README.md
```

### Running tests

```bash
# Run with verbose logging
flywheel-gear-mcp --verbose
```

### Adding new documentation sources

1. Edit `config.yaml`
2. Add a new entry to `documentation_sources`
3. Restart the server
4. The tool will be automatically available!

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
