# Flywheel Gear Development MCP Server

Give Claude expert knowledge of Flywheel gear development while you code.

## The Problem

[Developing gears for Flywheel](https://docs.flywheel.io/Developer_Guides/gear/building_tutorial/) means wrestling with documentation scattered across 10+ sources—many deprecated, conflicting, or redundant. You're constantly switching between browser tabs, searching for the right API reference, and wondering if what you're reading is still current.

## The Solution

This MCP (Model Context Protocol) server gives Claude Code direct access to all of the Flywheel and DICOM documentation on command. Now when you ask Claude "What's the correct way to write a DICOM secondary?", it can reference the actual current specs—no hallucination or without loading all of the DICOM standard docs into memory and clogging up your context.

**What's MCP?** It's a protocol that lets Claude Code access external tools and data. This server runs locally on your machine (started and stopped by `claude` only in the directory that you are developing a Flywheel gear) and feeds fresh Flywheel docs to Claude on demand.

**Who is this for?** Flywheel developers using [Claude Code CLI](https://claude.ai/download) to build gears.

## Quick Start

```bash
# 1. Clone and install the MCP server
git clone https://github.com/wzkariampuzha/flywheel-gear-dev-mcp.git
cd flywheel-gear-dev-mcp
uv sync

# 2. Navigate to your gear project
cd /path/to/your/gear-project

# 3. Add the MCP server
claude mcp add flywheel-gear-dev \
  --scope local \
  -- uv run --directory /full/path/to/flywheel-gear-dev-mcp flywheel-gear-mcp

# 4. Start Claude Code and ask:
# "Show me the gear manifest schema requirements"
```

## Configuration

Two ways to configure the server in your gear project:

### Option 1: CLI (Recommended)

From your gear project directory:

```bash
claude mcp add flywheel-gear-dev \
  --scope local \
  -- uv run --directory /absolute/path/to/flywheel-gear-dev-mcp flywheel-gear-mcp
```

### Option 2: .mcp.json file

Create `.mcp.json` in your gear project:

```json
{
  "mcpServers": {
    "flywheel-gear-dev": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/flywheel-gear-dev-mcp", "flywheel-gear-mcp"]
    }
  }
}
```

## Usage

### Starting the server

The server is automatically started by Claude Code when you launch a session. 

### Using the tools in Claude Code

Once configured, you can ask Claude to use the documentation tools:

```
"Can you get the fw-gear documentation?"
"Show me the DICOM standard data dictionary"
"What are the gear manifest schema requirements?"
```

## Features
- **Fresh documentation on startup**: Fetches latest docs every time the server starts
- **10 curated documentation sources**: Flywheel gear libraries, APIs, DICOM standard, and guides that you can add/remove/edit in [config](config.yaml)
- **Deprecation filtering**: Automatically removes deprecated content to keep LLMs focused on current APIs
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

### Customizing documentation sources

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

## How It Works

1. **One-time setup**: Install the MCP server code once, configure it in your gear projects
2. **Automatic startup**: When you run `claude` in your gear project, Claude Code automatically starts this MCP server in the background
3. **On-demand docs**: When Claude needs Flywheel documentation, it calls this server via MCP protocol
4. **Fresh data**: The server fetches latest docs from URLs on first request, caches them for the session
5. **Automatic shutdown**: Server stops when you exit Claude Code

The server runs locally—no data leaves your machine.

## Troubleshooting

### Server won't start

1. **Check Python version**: Requires Python 3.13+
2. **Check dependencies**: Run `uv sync` again
3. **Check log files**: Review `logs/flywheel-gear-mcp.log` for detailed error messages

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
