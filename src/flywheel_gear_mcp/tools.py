"""Dynamic MCP tool generation based on configuration."""

import logging
from datetime import datetime

import yaml

from . import fetcher

logger = logging.getLogger(__name__)


def load_tool_definitions(config_path: str = "config.yaml") -> list[dict]:
    """Load tool definitions from config file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        List of tool definition dictionaries for MCP
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    sources = config.get("documentation_sources", [])
    tools = []

    for source in sources:
        tool_name = source["tool_name"]
        display_name = source.get("display_name", tool_name)
        description = source.get("description", f"Get {display_name} documentation")

        tool_def = {
            "name": tool_name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": {},  # No parameters needed
                "required": [],
            },
        }
        tools.append(tool_def)

    logger.info(f"Loaded {len(tools)} tool definitions from {config_path}")
    return tools


async def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a documentation tool.

    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments (typically empty for these tools)

    Returns:
        Formatted documentation content
    """
    doc = fetcher.get_cached_doc(tool_name)

    if not doc:
        return f"# Error\n\nDocumentation for '{tool_name}' not found in cache. Please restart the server."

    # Format response with metadata
    output = []

    # Header
    output.append(f"# {doc['display_name']}")
    output.append("")

    if doc.get("description"):
        output.append(f"*{doc['description']}*")
        output.append("")

    # Metadata
    output.append("## Metadata")
    output.append("")
    output.append(f"- **Source URL(s):** {', '.join(doc['urls'])}")

    fetched_at = doc.get("fetched_at")
    if isinstance(fetched_at, datetime):
        output.append(f"- **Fetched:** {fetched_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        output.append(f"- **Fetched:** {fetched_at}")

    size_kb = doc.get("size", 0) / 1024
    output.append(f"- **Size:** {size_kb:.1f} KB")
    output.append("")

    # Check for errors
    if "error" in doc:
        output.append(f"⚠️ **Warning:** Partial or failed fetch - {doc['error']}")
        output.append("")

    # Content
    output.append("---")
    output.append("")
    output.append(doc["content"])

    return "\n".join(output)


def create_list_docs_tool() -> dict:
    """Create a special tool that lists all available documentation sources.

    Returns:
        Tool definition for list_available_docs
    """
    return {
        "name": "list_available_docs",
        "description": "List all available Flywheel documentation sources with metadata",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    }


async def execute_list_docs_tool(arguments: dict) -> str:
    """Execute the list_available_docs tool.

    Args:
        arguments: Tool arguments (ignored)

    Returns:
        Formatted list of all documentation sources
    """
    all_docs = fetcher.get_all_cached_docs()

    output = ["# Available Flywheel Documentation Sources\n"]

    if not all_docs:
        output.append(
            "*No documentation currently cached. Server may still be starting up.*\n"
        )
        return "\n".join(output)

    output.append(f"Total sources: {len(all_docs)}\n")

    for tool_name, doc in all_docs.items():
        output.append(f"## `{tool_name}`")
        output.append(f"**{doc['display_name']}**")

        if doc.get("description"):
            output.append(f"\n*{doc['description']}*")

        output.append(f"\n- URLs: {len(doc['urls'])}")

        size_kb = doc.get("size", 0) / 1024
        output.append(f"- Size: {size_kb:.1f} KB")

        if "error" in doc:
            output.append(f"- ⚠️ Status: Error - {doc['error']}")
        else:
            output.append("- ✓ Status: Successfully cached")

        output.append("")

    return "\n".join(output)
