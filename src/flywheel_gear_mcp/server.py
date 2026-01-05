"""Flywheel Gear Development MCP Server.

This server provides Flywheel documentation through MCP tools.
Documentation is fetched fresh on each server startup.
"""

import asyncio
import logging
import logging.handlers
import os
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent

from . import fetcher, tools


def _setup_logging(verbose: bool = False):
    """Configure both file and console logging with rotation.

    Args:
        verbose: Enable DEBUG level logging if True
    """
    # Create logs directory if it doesn't exist
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler (INFO level by default, DEBUG if verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler (always DEBUG level)
    # Max 10MB per file, keep 5 backup files
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "flywheel-gear-mcp.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)


# Logger will be configured in main()
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("flywheel-gear-mcp")

# Global state
_initialized = False


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available documentation tools.

    Returns:
        List of MCP tool definitions
    """
    # Ensure initialization
    await _ensure_initialized()

    # Load tool definitions from config
    config_path = _find_config_path()
    tool_defs = tools.load_tool_definitions(config_path)

    # Add the special list_docs tool
    tool_defs.append(tools.create_list_docs_tool())

    # Convert to MCP Tool objects
    mcp_tools = []
    for tool_def in tool_defs:
        mcp_tools.append(
            Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                inputSchema=tool_def["inputSchema"],
            )
        )

    return mcp_tools


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a documentation tool.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of text content responses
    """
    # Ensure initialization
    await _ensure_initialized()

    # Special handling for list_docs tool
    if name == "list_available_docs":
        content = await tools.execute_list_docs_tool(arguments)
    else:
        # Execute regular documentation tool
        content = await tools.execute_tool(name, arguments)

    return [TextContent(type="text", text=content)]


async def _ensure_initialized():
    """Ensure the server is initialized with fresh documentation."""
    global _initialized

    if _initialized:
        return

    logger.info("Initializing Flywheel Gear MCP Server...")

    # Find config file
    config_path = _find_config_path()

    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        logger.error(
            "Please ensure config.yaml exists in the project root or current directory."
        )
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info(f"Using configuration: {config_path}")

    # Fetch all documentation sources
    try:
        await fetcher.fetch_all_docs(config_path)
        logger.info("Documentation fetched and cached successfully!")
        _initialized = True
    except Exception as e:
        logger.error(f"Failed to fetch documentation: {e}", exc_info=True)
        raise


def _find_config_path() -> str:
    """Find the config.yaml file.

    Looks in:
    1. Current working directory
    2. Parent directories (up to 3 levels)
    3. Package installation directory

    Returns:
        Path to config.yaml
    """
    # Try current directory
    if os.path.exists("config.yaml"):
        return "config.yaml"

    # Try parent directories
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents[:3]):
        config_path = parent / "config.yaml"
        if config_path.exists():
            return str(config_path)

    # Try package directory
    package_dir = Path(__file__).parent.parent.parent
    config_path = package_dir / "config.yaml"
    if config_path.exists():
        return str(config_path)

    # Default to current directory (will fail later with clear error)
    return "config.yaml"


def main():
    """Main entry point for the MCP server."""
    import sys

    # Set up logging (both console and file)
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    global logger
    logger = _setup_logging(verbose)

    if verbose:
        logger.debug("Verbose logging enabled")

    logger.info("Starting Flywheel Gear MCP Server...")
    logger.info("Logs are being written to: logs/flywheel-gear-mcp.log")
    logger.info("Documentation will be fetched fresh on first tool call.")

    # Run the server
    from mcp.server.stdio import stdio_server

    async def arun():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream, app.create_initialization_options()
            )

    asyncio.run(arun())


if __name__ == "__main__":
    main()
