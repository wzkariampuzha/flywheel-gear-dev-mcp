# Flywheel Gear Development MCP Server

An MCP (Model Context Protocol) server that provides fresh Flywheel documentation for gear development. Designed for use with Claude Code CLI or possibly other LLMs (haven't tested them there yet).

## Features
- **Fresh documentation on startup**: Fetches latest docs every time the server starts
- **10 curated documentation sources**: Flywheel gear libraries, APIs, DICOM standard, and guides that you can add/remove/edit in [config](config.yaml)
- **Deprecation filtering**: Automatically removes deprecated content to keep LLMs focused on current APIs

## Installation
### Prerequisites
- [uv](https://github.com/astral-sh/uv) or pip (Python 3.13+)

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

## Contributing
Contributions welcome! Please open an issue or PR.
