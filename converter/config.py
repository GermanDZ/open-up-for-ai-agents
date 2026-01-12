"""Configuration for OpenUP converter."""

from pathlib import Path

# Paths
SOURCE_DIR = Path(".tmp/openup")
OUTPUT_DIR = Path("openup-knowledge-base")

# Processing
PARALLEL_WORKERS = 8
MAX_RETRIES = 3

# Path transformation rules
PATH_MAPPINGS = {
    # Core mappings
    r"core\.default\.": "core/",
    r"core\.mgmt\.": "core/",
    r"core\.tech\.": "core/",
    r"core\.gen\.": "core/",

    # Practice mappings
    r"practice\.mgmt\.": "practice-management/",
    r"practice\.tech\.": "practice-technical/",
    r"practice\.gen\.": "practice-general/",

    # Process mappings
    r"process\.openup\.": "process/",
    r"process\.": "process/",

    # Publish mappings
    r"publish\.openup\.": "guides/",
    r"publish\.": "guides/",
}

# Suffixes to remove from path components
REMOVE_SUFFIXES = [".base", ".extend_supp", ".slot", "_def", "_view", "_concept"]

# Content type patterns
CONTENT_TYPES = {
    "Role": "roles",
    "Task": "tasks",
    "Artifact": "workproducts",
    "Concept": "concepts",
    "Guideline": "guidelines",
    "Checklist": "checklists",
    "Example": "examples",
    "Template": "templates",
    "SupportingMaterial": "guides",
    "RoadMap": "roadmaps",
    "Report": "reports",
}

# HTML parsing config
SKIP_SELECTORS = [
    "div#breadcrumbs",
    "div#contentPageToolbar",
    "table.copyright",
    "script",
    "noscript",
    ".expandCollapseLink",
    ".pageTitleSeparator",
]

CONTENT_SELECTORS = {
    "overview": "div.overview",
    "sections": "div.sectionContent",
    "step_heading": "div.stepHeading",
    "step_content": "div.stepContent",
}

# Markdown conversion
MARKDOWN_CONFIG = {
    "heading_style": "ATX",
    "bullets": "-",
    "wrap": False,
    "body_width": 0,  # No wrapping
}
