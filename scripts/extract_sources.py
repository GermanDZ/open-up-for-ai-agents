#!/usr/bin/env python3
"""Extract source paths from existing description files."""

import re
from pathlib import Path

DESCRIPTIONS_DIR = Path("openup-knowledge-base/images/descriptions")
source_mapping = {}

for md_file in DESCRIPTIONS_DIR.glob("*.md"):
    try:
        content = md_file.read_text(encoding="utf-8")
        match = re.search(r'^source:\s*["\']?([^"\']+)["\']?$', content, re.MULTILINE)
        if match:
            source_path = match.group(1).strip()
            img_name = md_file.stem
            source_mapping[img_name] = source_path
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

# Output as Python dict for easy import
print("SOURCE_MAPPING = {")
for img, src in sorted(source_mapping.items()):
    print(f'    "{img}": "{src}",')
print("}")
