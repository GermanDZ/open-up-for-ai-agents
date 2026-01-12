#!/usr/bin/env python3
"""Generate image description files in openup-extra-content/images-descriptions/"""

import re
from pathlib import Path
from typing import Dict, Optional

# Paths
DESCRIPTIONS_DIR = Path("openup-knowledge-base/images/descriptions")
IMAGES_DIR = Path("openup-knowledge-base/images")
OUTPUT_DIR = Path("openup-extra-content/images-descriptions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_source_paths() -> Dict[str, str]:
    """Extract source paths from existing description files."""
    source_mapping = {}
    
    for md_file in DESCRIPTIONS_DIR.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            # Extract source path from frontmatter (handles quoted and unquoted)
            match = re.search(r'^source:\s*["\']?([^"\']+)["\']?$', content, re.MULTILINE)
            if match:
                source_path = match.group(1).strip()
                # Get image filename (md filename without .md extension)
                img_name = md_file.stem
                source_mapping[img_name] = source_path
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return source_mapping


def get_image_filename_from_path(image_path: Path) -> str:
    """Get the image filename from a path."""
    return image_path.name


def generate_description_file(
    image_path: Path,
    source_path: Optional[str],
    description: str
) -> None:
    """Generate a description markdown file for an image."""
    image_filename = get_image_filename_from_path(image_path)
    md_filename = image_path.stem + ".md"
    output_path = OUTPUT_DIR / md_filename
    
    # Format source path or use placeholder
    source = source_path if source_path else f"unknown/{image_filename}"
    
    content = f"""---
title: "Image: {image_filename}"
image_file: "../{image_filename}"
source: "{source}"
---

# Image Description: {image_filename}

## Description

{description}

## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.
"""
    
    output_path.write_text(content, encoding="utf-8")
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    # Extract source paths
    source_mapping = extract_source_paths()
    print(f"Extracted {len(source_mapping)} source paths")
    
    # Get all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".gif"}
    image_files = [
        f for f in IMAGES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    print(f"Found {len(image_files)} image files to process")
    print("\nNote: This script extracts source paths. Image analysis and description generation")
    print("should be done using vision capabilities for each image.")
