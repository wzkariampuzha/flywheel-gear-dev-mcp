"""Documentation parsers for different content types."""

import json
import re
from typing import Optional

from bs4 import BeautifulSoup
from lxml import etree
from markdownify import markdownify as md


def parse_html(content: str, url: str, strip_deprecated: bool = True) -> str:
    """Parse HTML content and convert to clean markdown.

    Args:
        content: Raw HTML content
        url: Source URL (for context)
        strip_deprecated: Whether to remove deprecated sections

    Returns:
        Clean markdown documentation
    """
    soup = BeautifulSoup(content, "html.parser")

    # Remove unwanted elements
    for element in soup.find_all(
        ["script", "style", "nav", "header", "footer", "aside"]
    ):
        element.decompose()

    # Try to find main content area
    main_content = None
    for selector in [
        "main",
        "article",
        '[role="main"]',
        ".content",
        ".documentation",
        "#content",
    ]:
        main_content = soup.select_one(selector)
        if main_content:
            break

    # If no main content found, use body or entire soup
    if not main_content:
        main_content = soup.find("body") or soup

    # Remove deprecated sections if requested
    if strip_deprecated:
        main_content = _remove_deprecated_sections(main_content)

    # Convert to markdown
    markdown = md(str(main_content), heading_style="ATX", bullets="-")

    # Clean up excessive whitespace
    markdown = re.sub(r"\n\s*\n\s*\n+", "\n\n", markdown)
    markdown = markdown.strip()

    return markdown


def parse_xml(content: str, filter_sections: Optional[list[str]] = None) -> str:
    """Parse XML content (specifically for DICOM standard).

    Args:
        content: Raw XML content
        filter_sections: Specific sections to extract (e.g., ['data_dictionary', 'transfer_syntaxes'])

    Returns:
        Formatted markdown documentation from XML
    """
    try:
        root = etree.fromstring(content.encode("utf-8"))
    except Exception:
        # If full parse fails, try to extract just the relevant parts
        root = etree.fromstring(
            content.encode("utf-8"), parser=etree.XMLParser(recover=True)
        )

    output_lines = ["# DICOM Standard Documentation\n"]

    # If filter_sections specified, extract only those
    if filter_sections:
        if "data_dictionary" in filter_sections:
            output_lines.extend(_extract_dicom_data_dictionary(root))

        if "transfer_syntaxes" in filter_sections:
            output_lines.extend(_extract_dicom_transfer_syntaxes(root))
    else:
        # Extract all content
        text = etree.tostring(root, encoding="unicode", method="text")
        output_lines.append(text)

    return "\n".join(output_lines)


def parse_json_schema(content: str) -> str:
    """Parse and format JSON schema for manifest.

    Args:
        content: Raw JSON content

    Returns:
        Pretty-formatted JSON with descriptions
    """
    try:
        data = json.loads(content)

        # Create a more readable markdown format
        output = ["# Gear Manifest JSON Schema\n"]

        # Add schema metadata
        if "description" in data:
            output.append(f"{data['description']}\n")

        # Format properties
        if "properties" in data:
            output.append("## Properties\n")
            for prop_name, prop_def in data["properties"].items():
                output.append(f"### `{prop_name}`")
                if isinstance(prop_def, dict):
                    if "description" in prop_def:
                        output.append(f"{prop_def['description']}")
                    if "type" in prop_def:
                        output.append(f"- **Type:** `{prop_def['type']}`")
                    if "required" in data and prop_name in data["required"]:
                        output.append("- **Required:** Yes")
                output.append("")

        # Also include raw JSON for reference
        output.append("## Full Schema (JSON)\n")
        output.append("```json")
        output.append(json.dumps(data, indent=2))
        output.append("```")

        return "\n".join(output)

    except json.JSONDecodeError as e:
        return f"# Error Parsing JSON Schema\n\nFailed to parse JSON: {e}\n\n```\n{content}\n```"


def parse_gitlab_repo(content: str, strip_deprecated: bool = True) -> str:
    """Parse markdown content from GitLab repository.

    For now, this is similar to HTML parsing but specific to GitLab's markdown.
    Future enhancement: could fetch repo tree and combine multiple .md files.

    Args:
        content: GitLab HTML/markdown content
        strip_deprecated: Whether to remove deprecated sections

    Returns:
        Clean markdown documentation
    """
    # GitLab renders markdown as HTML, so parse it similarly
    return parse_html(content, "", strip_deprecated)


# Helper functions


def _remove_deprecated_sections(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove sections marked as deprecated from BeautifulSoup object.

    Args:
        soup: BeautifulSoup object to clean

    Returns:
        Cleaned BeautifulSoup object
    """
    deprecated_patterns = [
        re.compile(r"deprecat", re.IGNORECASE),
        re.compile(r"legacy", re.IGNORECASE),
        re.compile(r"obsolete", re.IGNORECASE),
    ]

    # Find elements containing deprecated markers
    for pattern in deprecated_patterns:
        # Check headings
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if pattern.search(heading.get_text()):
                # Remove the heading and all content until the next heading of same/higher level
                _remove_section(heading)

        # Check divs and sections with deprecated in class or id
        for element in soup.find_all(["div", "section", "article"]):
            classes = element.get("class", [])
            element_id = element.get("id", "")
            if any(pattern.search(str(c)) for c in classes) or pattern.search(
                element_id
            ):
                element.decompose()

        # Check for deprecated badges/labels
        for element in soup.find_all(["span", "div", "p"]):
            if pattern.search(element.get_text()) and len(element.get_text()) < 50:
                # If it's a short text (likely a badge), remove parent
                parent = element.find_parent(["div", "section", "article"])
                if parent:
                    parent.decompose()

    return soup


def _remove_section(heading):
    """Remove a heading and all content until the next same-level heading."""
    level = int(heading.name[1])  # Extract number from h1, h2, etc.

    # Find all siblings after this heading
    for sibling in list(heading.next_siblings):
        if sibling.name and sibling.name.startswith("h"):
            sibling_level = int(sibling.name[1])
            if sibling_level <= level:
                # Reached next same/higher level heading, stop
                break
        if hasattr(sibling, "decompose"):
            sibling.decompose()

    heading.decompose()


def _extract_dicom_data_dictionary(root) -> list[str]:
    """Extract DICOM data dictionary from XML root.

    Args:
        root: XML root element

    Returns:
        List of markdown lines for data dictionary
    """
    output = ["\n## DICOM Data Dictionary\n"]

    # Look for common DICOM data dictionary structures
    # This is a simplified version - actual DICOM XML structure varies
    data_dict_elements = root.xpath(
        ".//*[contains(local-name(), 'DataElement') or contains(local-name(), 'tag')]"
    )

    if data_dict_elements:
        output.append("| Tag | Name | VR | Description |")
        output.append("|-----|------|----|-----------  |")

        for elem in data_dict_elements[:100]:  # Limit to first 100 for brevity
            tag = elem.get("tag", "N/A")
            name = elem.get("name", elem.text or "N/A")
            vr = elem.get("vr", "N/A")
            output.append(f"| {tag} | {name} | {vr} | ... |")
    else:
        output.append(
            "*Data dictionary section found but structure not recognized. Full XML parsing may be needed.*\n"
        )

    return output


def _extract_dicom_transfer_syntaxes(root) -> list[str]:
    """Extract DICOM transfer syntaxes from XML root.

    Args:
        root: XML root element

    Returns:
        List of markdown lines for transfer syntaxes
    """
    output = ["\n## DICOM Transfer Syntaxes\n"]

    # Look for transfer syntax elements
    ts_elements = root.xpath(".//*[contains(local-name(), 'TransferSyntax')]")

    if ts_elements:
        for elem in ts_elements:
            uid = elem.get("uid", elem.text or "N/A")
            name = elem.get("name", "N/A")
            output.append(f"- **{name}**: `{uid}`")
    else:
        output.append(
            "*Transfer syntax section found but structure not recognized. Full XML parsing may be needed.*\n"
        )

    return output
