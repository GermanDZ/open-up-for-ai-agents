#!/usr/bin/env python3
"""Main conversion script."""

import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict
import time
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from converter.config import SOURCE_DIR, OUTPUT_DIR, PARALLEL_WORKERS
from converter.path_mapper import PathMapper
from converter.markdown_converter import MarkdownConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def convert_single_file(args: tuple) -> tuple:
    """Convert a single HTML file to Markdown."""
    rel_path, abs_path, converter = args

    try:
        # Convert to markdown
        markdown_content = converter.convert_file(abs_path, rel_path)

        # Get new path
        new_path = converter.path_mapper.get_new_path(rel_path)

        if not new_path:
            logger.error(f"No mapping found for: {rel_path}")
            return (rel_path, False, "No mapping")

        return (rel_path, True, new_path, markdown_content)

    except Exception as e:
        logger.error(f"Error converting {rel_path}: {e}")
        return (rel_path, False, str(e))


def write_markdown_file(output_dir: Path, rel_path: str, content: str):
    """Write markdown content to file."""
    output_path = output_dir / rel_path

    # Create parent directories
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def extract_referenced_images(source_dir: Path) -> set:
    """
    Scan all HTML files and extract referenced image paths.
    Excludes files from ignored directories (logs, noapplet, nav).

    Returns:
        Set of relative image paths referenced in HTML files
    """
    from bs4 import BeautifulSoup
    import posixpath

    referenced_images = set()

    # Scan all HTML files
    for html_file in source_dir.glob("**/*.html"):
        # Skip files in excluded directories
        rel_path = str(html_file.relative_to(source_dir)).lower()
        skip_patterns = ['index.htm', 'logs/', 'noapplet/', 'applet/', 'nav_view']
        if any(rel_path.startswith(pattern) or f'/{pattern}' in rel_path or pattern in rel_path
               for pattern in skip_patterns):
            continue

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')

            # Find all img tags
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src', '')
                if not src or src.startswith(('http://', 'https://', 'data:')):
                    continue

                # Skip decorative table-leading images
                # Pattern: <td width="50"><img src="..."></td><td>content</td>
                parent_td = img_tag.find_parent('td')
                if parent_td:
                    width = parent_td.get('width', '')
                    if width == '50':
                        # This is a decorative icon cell, skip it
                        continue

                # Resolve relative path from HTML file location
                html_rel_path = html_file.relative_to(source_dir)
                html_dir = posixpath.dirname(str(html_rel_path))

                # Resolve image path
                resolved = posixpath.normpath(posixpath.join(html_dir, src))
                referenced_images.add(resolved)

        except Exception as e:
            continue

    return referenced_images


def copy_images(source_dir: Path, output_dir: Path, referenced_images: set = None) -> Dict[str, str]:
    """
    Copy only referenced image files to /images/ directory in output.
    Convert GIF files to PNG format.
    Filters out decorative UI elements (navigation, icons, banners).
    Returns mapping of source_path -> images/filename for link fixing.

    Args:
        source_dir: Source directory containing HTML files
        output_dir: Output directory for markdown
        referenced_images: Set of image paths actually referenced in HTML (if None, copies all)

    Returns:
        Dict mapping source image paths to output image paths
    """
    import shutil
    from PIL import Image
    from collections import defaultdict

    # Decorative image patterns to exclude (UI elements, navigation, etc.)
    DECORATIVE_PATTERNS = [
        # Navigation elements
        'tab_', 'titleback_', 'top_sm', 'bottom_', 'arrow_',
        # Icons and buttons
        'circle_', 'icon_', 'back.', 'back_to_top', 'print.', 'bookmark.',
        'collapse', 'display_views', 'u_bold', 'up_arrow',
        # Borders and spacing
        'shim.', 'true.', 'sample_sectionhead', 'step_sample',
        # Banners and splash screens
        'banner.', 'splash.', 'topbar_mockup', 'EPFC_banner',
        # RUP branding
        'rup1', 'no_rup',
        # Action buttons (hide/show/expand)
        'action_',
        # OpenUP banner (decorative header)
        'openup_banner',
        # Type indicator icons (decorative table elements)
        'role.png', 'role.gif',
        'task.png', 'task.gif',
        'artifact.png', 'artifact.gif',
        'concept.png', 'concept.gif',
        'guideline.png', 'guideline.gif',
        'guidance.png', 'guidance.gif',
        'practice.png', 'practice.gif',
        'checklist.png', 'checklist.gif',
        'template.png', 'template.gif',
        'report.png', 'report.gif',
        'example.png', 'example.gif',
        'tool.png', 'tool.gif',
        'technique.png', 'technique.gif',
        'roadmap.png', 'roadmap.gif',
        'whitepaper.png', 'whitepaper.gif',
        'domain_shape.png', 'domain_shape.gif',
        # UI decorative elements
        'divider.', 'expand.', 'folder.', 'file.',
        'forward.', 'next.', 'previous.', 'plus.', 'noplus.',
        'visual.', 'searchrecord.',
    ]

    dest_images = output_dir / "images"
    dest_images.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    skipped_count = 0
    image_mapping = {}  # source_rel_path -> images/filename
    name_counts = defaultdict(int)  # Track duplicate names

    # Find all images in source
    for img_file in source_dir.glob("**/*"):
        if not img_file.is_file():
            continue
        if img_file.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif']:
            continue

        # Get relative path from source
        rel_path = str(img_file.relative_to(source_dir))

        # Skip if not referenced (only if referenced_images set is provided)
        if referenced_images is not None and rel_path not in referenced_images:
            skipped_count += 1
            continue

        # Skip decorative images
        filename_lower = img_file.name.lower()
        if any(pattern in filename_lower for pattern in DECORATIVE_PATTERNS):
            skipped_count += 1
            continue

        # Generate unique name: use original filename, add counter if duplicate
        base_name = img_file.stem
        ext = '.png' if img_file.suffix.lower() == '.gif' else img_file.suffix

        # Create unique name
        if name_counts[base_name] > 0:
            final_name = f"{base_name}_{name_counts[base_name]}{ext}"
        else:
            final_name = f"{base_name}{ext}"
        name_counts[base_name] += 1

        dest_file = dest_images / final_name

        # Copy or convert
        try:
            if img_file.suffix.lower() == '.gif':
                # Convert GIF to PNG
                with Image.open(img_file) as img:
                    if img.mode not in ['RGB', 'RGBA']:
                        img = img.convert('RGBA')
                    img.save(dest_file, 'PNG')
            else:
                # Copy as-is
                shutil.copy2(img_file, dest_file)

            # Store mapping
            image_mapping[rel_path] = f"images/{final_name}"
            copied_count += 1

        except Exception as e:
            logger.warning(f"Failed to process image {rel_path}: {e}")
            continue

    logger.info(f"Copied {copied_count} content images to /images/ (skipped {skipped_count} decorative images)")
    return image_mapping


def generate_image_sidecars(source_dir: Path, output_dir: Path, image_mapping: Dict[str, str]) -> int:
    """
    Generate sidecar markdown files for each image with descriptions.
    Extracts alt text and context from HTML sources.

    Returns:
        Number of sidecar files generated
    """
    from bs4 import BeautifulSoup
    from PIL import Image
    import re

    sidecars_dir = output_dir / "images" / "descriptions"
    sidecars_dir.mkdir(parents=True, exist_ok=True)

    generated_count = 0

    # For each image in the mapping, find its source HTML and extract context
    for source_rel_path, dest_path in image_mapping.items():
        # Get the image filename
        img_filename = dest_path.replace('images/', '')
        img_full_path = output_dir / "images" / img_filename

        # Determine image category based on path and filename
        category = categorize_image(source_rel_path, img_filename)

        # Extract context from HTML source
        img_source_path = source_dir / source_rel_path
        context = extract_image_context(img_source_path.parent, img_filename.replace('.png', '.gif'))

        # Get image dimensions
        try:
            with Image.open(img_full_path) as img:
                width, height = img.size
                dimensions = f"{width}x{height}"
        except:
            dimensions = "unknown"

        # Generate sidecar content
        sidecar_content = generate_sidecar_content(
            img_filename, category, dimensions, context, source_rel_path
        )

        # Write sidecar file
        sidecar_filename = img_filename.replace('.jpg', '.md').replace('.png', '.md').replace('.jpeg', '.md')
        sidecar_path = sidecars_dir / sidecar_filename

        with open(sidecar_path, 'w', encoding='utf-8') as f:
            f.write(sidecar_content)

        generated_count += 1

    logger.info(f"Generated {generated_count} image sidecar files")
    return generated_count


def categorize_image(source_path: str, filename: str) -> str:
    """Categorize image based on path and filename."""
    filename_lower = filename.lower()
    source_lower = source_path.lower()

    if 'role' in source_lower and any(x in filename_lower for x in ['architect', 'developer', 'analyst', 'tester', 'manager', 'engineer']):
        return 'role_icon'
    elif any(x in filename_lower for x in ['lifecycle', 'flow', 'diagram']):
        return 'process_diagram'
    elif any(x in filename_lower for x in ['uml', 'class', 'sequence', 'activity']):
        return 'uml_diagram'
    elif any(x in filename_lower for x in ['architecture', 'component', 'deployment']):
        return 'architecture_diagram'
    elif filename_lower in ['role.png', 'task.png', 'artifact.png', 'concept.png', 'guideline.png']:
        return 'type_icon'
    else:
        return 'illustration'


def extract_image_context(html_dir: Path, img_filename: str) -> Dict[str, str]:
    """Extract alt text and surrounding context from HTML files."""
    from bs4 import BeautifulSoup

    context = {
        'alt_text': '',
        'caption': '',
        'surrounding_text': ''
    }

    # Find HTML files in the same directory that might reference this image
    for html_file in html_dir.glob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'lxml')

            # Find img tags
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src', '')
                if img_filename in src or img_filename.replace('.png', '.gif') in src:
                    context['alt_text'] = img_tag.get('alt', '')

                    # Look for caption in surrounding text
                    parent = img_tag.parent
                    if parent:
                        # Check for bold text (often captions) before the image
                        prev_sibling = parent.find_previous_sibling()
                        if prev_sibling and prev_sibling.find('b'):
                            context['caption'] = prev_sibling.get_text(strip=True)

                        # Get surrounding paragraph text
                        para = img_tag.find_parent('p')
                        if para:
                            context['surrounding_text'] = para.get_text(strip=True)[:500]

                    return context
        except Exception as e:
            continue

    return context


def read_manual_description(filename: str) -> dict:
    """
    Read manual description file for an image if it exists.

    Args:
        filename: Image filename (e.g., '4plus1_2.jpg')

    Returns:
        dict with 'description' and 'for_llms' keys, or None if file doesn't exist
    """
    import re
    from pathlib import Path

    # Convert image filename to markdown filename
    md_filename = filename.replace('.jpg', '.md').replace('.png', '.md').replace('.jpeg', '.md')

    # Path to manual descriptions directory (relative to scripts dir)
    manual_dir = Path(__file__).parent.parent / "openup-extra-content" / "images-descriptions"
    manual_path = manual_dir / md_filename

    if not manual_path.exists():
        return None

    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract Description section
        desc_match = re.search(r'## Description\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else None

        # Extract For LLMs section
        llms_match = re.search(r'## For LLMs\s*\n(.*?)(?=\Z)', content, re.DOTALL)
        for_llms = llms_match.group(1).strip() if llms_match else None

        if description or for_llms:
            return {
                'description': description,
                'for_llms': for_llms
            }
    except Exception as e:
        # If error reading/parsing manual file, return None to fall back to auto-generated
        logger.warning(f"Error reading manual description for {filename}: {e}")
        return None

    return None


def generate_sidecar_content(filename: str, category: str, dimensions: str,
                            context: Dict[str, str], source_path: str) -> str:
    """Generate markdown content for image sidecar file."""

    # Check for manual description
    manual_content = read_manual_description(filename)

    content = f"""---
title: "Image: {filename}"
image_file: "../{filename}"
category: "{category}"
dimensions: "{dimensions}"
source: "{source_path}"
---

# Image Description: {filename}

"""

    # Add alt text if available
    if context.get('alt_text'):
        content += f"**Alt Text:** {context['alt_text']}\n\n"

    # Add caption if available
    if context.get('caption'):
        content += f"**Caption:** {context['caption']}\n\n"

    # Use manual description if available, otherwise use category-specific auto-generated content
    if manual_content and manual_content.get('description'):
        # Use manual description
        content += f"## Description\n\n{manual_content['description']}\n\n"
    elif category == 'role_icon':
        role_name = filename.split('_')[0].title()
        role_upper = role_name.upper()
        content += f"""## Description

This is a visual icon representing the **{role_name}** role in the OpenUP methodology.

### Text Representation
```
[{role_upper} ICON]
- Role identifier image
- Used to visually represent the {role_name} role in documentation
```

### Purpose
This icon helps readers quickly identify content related to the {role_name} role throughout the OpenUP documentation.
"""

    elif category == 'type_icon':
        type_name = filename.replace('.png', '').replace('.jpg', '').title()
        type_upper = type_name.upper()
        content += f"""## Description

This is a type indicator icon for **{type_name}** elements in the OpenUP methodology.

### Text Representation
```
[{type_upper}]
```

### Purpose
This icon appears in tables and headings to indicate {type_name}-type content elements.
"""

    elif category in ['process_diagram', 'uml_diagram', 'architecture_diagram']:
        category_display = category.replace('_', ' ')
        content += f"""## Description

This is a {category_display} showing process flow, relationships, or structure.

"""
        if context.get('alt_text'):
            content += f"{context['alt_text']}\n\n"

        if context.get('caption'):
            content += f"### Caption\n{context['caption']}\n\n"

        content += """### Diagram Type
Process flow / lifecycle diagram

### Key Elements
[This would require manual analysis or AI vision to describe specific elements]

### Mermaid Representation
[To be added - requires manual conversion or AI vision to interpret the diagram structure]

"""

    else:  # illustration
        content += f"""## Description

This image provides visual context for the associated content.

"""
        if context.get('alt_text'):
            content += f"{context['alt_text']}\n\n"

        if context.get('surrounding_text'):
            content += f"### Context\n{context['surrounding_text']}\n\n"

    # Use manual "For LLMs" section if available, otherwise use generic one
    if manual_content and manual_content.get('for_llms'):
        content += f"## For LLMs\n\n{manual_content['for_llms']}\n\n"
    else:
        content += """## For LLMs

This sidecar file provides text-based description of the image to enable understanding without visual processing.

"""

    return content


def populate_related_metadata(output_dir: Path, path_mapper: PathMapper) -> int:
    """
    Populate the 'related' field in frontmatter for all markdown files.

    Returns:
        Number of files modified
    """
    import re
    import yaml
    import posixpath
    from pathlib import Path as P

    # Build reverse mapping: source_url → md_path
    source_to_md = {}
    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract source_url
            match = re.search(r'^source_url:\s*(.+)$', content, re.MULTILINE)
            if match:
                source_url = match.group(1).strip()
                rel_md_path = str(md_file.relative_to(output_dir))
                source_to_md[source_url] = rel_md_path
        except:
            continue

    def resolve_html_link(source_html: str, href: str) -> str:
        """Resolve a relative HTML link."""
        href = href.split('#')[0].strip()
        if not href or href.startswith(('http://', 'https://', 'mailto:')):
            return None

        source_dir = posixpath.dirname(source_html)
        resolved = posixpath.join(source_dir, href)
        return posixpath.normpath(resolved)

    modified_count = 0

    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split frontmatter and body
            parts = content.split('---\n', 2)
            if len(parts) < 3:
                continue

            # Parse frontmatter
            frontmatter_str = parts[1]
            body = parts[2]
            fm = yaml.safe_load(frontmatter_str)

            if not fm:
                continue

            source_html = fm.get('source_url')
            if not source_html:
                continue

            # Extract relationships from the body's "Relationships" section
            relationships_section = re.search(
                r'Relationships\s*\n\n(.*?)(?:\n---|\n##|\Z)',
                body,
                re.DOTALL
            )

            if not relationships_section:
                continue

            rel_content = relationships_section.group(1)

            # Extract all markdown links from relationships section
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', rel_content)

            # Categorize links
            related = {}
            for link_text, href in links:
                # Skip external links and anchors
                if href.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue

                # Only process markdown links (already converted by fix_internal_links)
                if not href.endswith('.md'):
                    continue

                # Extract slug from the markdown path
                slug = P(href).stem

                # Categorize by path
                href_lower = href.lower()
                if '/roles/' in href_lower or 'role_def' in href_lower or '/rolesets/' in href_lower:
                    related.setdefault('roles', []).append(slug)
                elif '/tasks/' in href_lower:
                    related.setdefault('tasks', []).append(slug)
                elif '/workproducts/' in href_lower:
                    related.setdefault('workproducts', []).append(slug)
                elif '/concepts/' in href_lower or '/guidances/concepts/' in href_lower or '/customcategories/' in href_lower:
                    related.setdefault('concepts', []).append(slug)
                elif '/guidelines/' in href_lower or '/guidances/guidelines/' in href_lower:
                    related.setdefault('guidelines', []).append(slug)
                elif '/checklists/' in href_lower or '/guidances/checklists/' in href_lower:
                    related.setdefault('checklists', []).append(slug)
                elif '/examples/' in href_lower or '/guidances/examples/' in href_lower:
                    related.setdefault('examples', []).append(slug)
                elif '/templates/' in href_lower or '/guidances/templates/' in href_lower:
                    related.setdefault('templates', []).append(slug)
                elif '/disciplines/' in href_lower:
                    related.setdefault('disciplines', []).append(slug)
                elif '/practices/' in href_lower:
                    related.setdefault('practices', []).append(slug)
                else:
                    related.setdefault('other', []).append(slug)

            # Remove duplicates
            for key in related:
                related[key] = list(dict.fromkeys(related[key]))

            # Only add if we found relationships
            if related:
                # Add to frontmatter (insert after page_guid or at end)
                fm['related'] = related

                # Regenerate frontmatter
                new_frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
                new_content = f"---\n{new_frontmatter}---\n\n{body}"

                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                modified_count += 1

        except Exception as e:
            logger.error(f"Error populating related metadata in {md_file}: {e}")
            continue

    return modified_count


def generate_manifest(output_dir: Path) -> Dict:
    """
    Generate manifest.json data structure.

    Returns:
        Dict containing manifest data
    """
    import datetime

    manifest = {
        "version": "1.0",
        "generated": datetime.datetime.now().strftime("%Y-%m-%d"),
        "title": "OpenUP Knowledge Base",
        "description": "Open Unified Process methodology documentation",
        "total_files": 0,
        "content_types": {},
        "files": [],
        "index": {
            "by_type": {},
            "by_keyword": {},
            "by_slug": {}
        }
    }

    # Scan all markdown files
    for md_file in sorted(output_dir.glob("**/*.md")):
        if md_file.name == "README.md":
            continue

        try:
            # Read and parse frontmatter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            parts = content.split('---\n', 2)
            if len(parts) < 3:
                continue

            fm = yaml.safe_load(parts[1])
            if not fm:
                continue

            # Build file entry
            rel_path = str(md_file.relative_to(output_dir))
            slug = md_file.stem

            file_entry = {
                "path": rel_path,
                "slug": slug,
                "title": fm.get('title', 'Untitled'),
                "type": fm.get('type', 'Unknown'),
                "uma_name": fm.get('uma_name'),
                "page_guid": fm.get('page_guid'),
                "keywords": fm.get('keywords', []),
                "related": fm.get('related', {})
            }

            manifest["files"].append(file_entry)
            manifest["total_files"] += 1

            # Index by type
            content_type = fm.get('type', 'Unknown')
            manifest["content_types"][content_type] = manifest["content_types"].get(content_type, 0) + 1

            if content_type not in manifest["index"]["by_type"]:
                manifest["index"]["by_type"][content_type] = []
            manifest["index"]["by_type"][content_type].append({
                "slug": slug,
                "title": fm.get('title'),
                "path": rel_path
            })

            # Index by keyword
            for keyword in fm.get('keywords', []):
                if keyword not in manifest["index"]["by_keyword"]:
                    manifest["index"]["by_keyword"][keyword] = []
                manifest["index"]["by_keyword"][keyword].append({
                    "slug": slug,
                    "title": fm.get('title'),
                    "path": rel_path,
                    "type": content_type
                })

            # Index by slug
            manifest["index"]["by_slug"][slug] = {
                "title": fm.get('title'),
                "path": rel_path,
                "type": content_type,
                "keywords": fm.get('keywords', []),
                "related": fm.get('related', {})
            }

        except Exception as e:
            logger.error(f"Error processing {md_file} for manifest: {e}")
            continue

    return manifest


def fix_image_references(output_dir: Path, image_mapping: Dict[str, str], path_mapper: PathMapper) -> int:
    """
    Fix all image references to point to /images/ directory.
    Handles both inline images and standalone image files.

    Args:
        output_dir: Output directory containing markdown files
        image_mapping: Dict of source_path -> images/filename
        path_mapper: PathMapper to resolve original HTML paths

    Returns:
        Number of files modified
    """
    import re
    import posixpath

    modified_count = 0

    # Build reverse mapping: original_html_path -> source_image_path
    html_to_images = {}
    for source_img_path, dest_img_path in image_mapping.items():
        # Get the HTML file this image belongs to (same directory)
        img_dir = posixpath.dirname(source_img_path)
        html_to_images.setdefault(img_dir, []).append((source_img_path, dest_img_path))

    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Get source HTML path from frontmatter
            source_match = re.search(r'^source_url:\s*(.+)$', content, re.MULTILINE)
            if not source_match:
                continue

            source_html = source_match.group(1).strip()
            source_dir = posixpath.dirname(source_html)

            # Calculate correct relative path to /images/
            rel_path = md_file.relative_to(output_dir)
            depth = len(rel_path.parts) - 1
            images_path = '../' * depth + 'images/'

            # Find and replace all image references
            def replace_image(match):
                alt_text = match.group(1)
                img_ref = match.group(2)

                # Remove .gif extension, will be .png
                img_ref_no_ext = img_ref.replace('.gif', '')

                # Resolve relative image path from source HTML
                if img_ref.startswith(('http://', 'https://')):
                    return match.group(0)  # Keep external images

                # Resolve relative path
                resolved = posixpath.join(source_dir, img_ref)
                resolved = posixpath.normpath(resolved)

                # Look up in image mapping
                if resolved in image_mapping:
                    new_ref = images_path + image_mapping[resolved].replace('images/', '')
                    return f'![{alt_text}]({new_ref})'

                # Try with .png extension (for converted GIFs)
                resolved_png = resolved.replace('.gif', '.png')
                if resolved_png in image_mapping:
                    new_ref = images_path + image_mapping[resolved_png].replace('images/', '')
                    return f'![{alt_text}]({new_ref})'

                # Try looking by filename only
                img_filename = posixpath.basename(img_ref).replace('.gif', '.png')
                for src_path, dest_path in image_mapping.items():
                    if dest_path.endswith(img_filename):
                        new_ref = images_path + dest_path.replace('images/', '')
                        return f'![{alt_text}]({new_ref})'

                # Keep original if not found
                return match.group(0)

            # Replace all image references
            content = re.sub(r'!\[(.*?)\]\(([^)]+)\)', replace_image, content)

            if content != original_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_count += 1

        except Exception as e:
            logger.error(f"Error fixing image references in {md_file}: {e}")
            continue

    return modified_count


def add_image_sidecar_links(output_dir: Path) -> int:
    """
    Add footnotes/descriptions with links to sidecar files for all images.

    Returns:
        Number of files modified
    """
    import re
    import posixpath

    modified_count = 0
    sidecars_dir = output_dir / "images" / "descriptions"

    if not sidecars_dir.exists():
        logger.warning("No sidecar directory found, skipping sidecar link generation")
        return 0

    # Get list of available sidecar files
    sidecar_files = {f.stem: f for f in sidecars_dir.glob("*.md")}

    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue
        if "images/descriptions" in str(md_file):
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            modifications = []

            # Calculate relative path to sidecars directory
            rel_path = md_file.relative_to(output_dir)
            depth = len(rel_path.parts) - 1
            sidecars_rel_path = '../' * depth + 'images/descriptions/'

            # Find all image references
            img_pattern = r'!\[(.*?)\]\(([^)]+)\)'

            def add_sidecar_link(match):
                alt_text = match.group(1)
                img_path = match.group(2)

                # Extract image filename from path
                img_filename = posixpath.basename(img_path)
                img_stem = img_filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '')

                # Check if sidecar exists
                if img_stem in sidecar_files:
                    sidecar_link = sidecars_rel_path + img_stem + '.md'
                    # Return image with sidecar link annotation
                    return f'![{alt_text}]({img_path}) [📄]({sidecar_link} "Image description")'

                return match.group(0)

            # Replace image references with sidecar links
            content = re.sub(img_pattern, add_sidecar_link, content)

            if content != original_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_count += 1

        except Exception as e:
            logger.error(f"Error adding sidecar links in {md_file}: {e}")
            continue

    return modified_count


def fix_internal_links(output_dir: Path, path_mapper: PathMapper) -> int:
    """
    Fix internal links in all markdown files.

    Returns:
        Number of files modified
    """
    import re
    import posixpath

    # Build reverse mapping: source_url → md_path
    source_to_md = {}
    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract source_url
            match = re.search(r'^source_url:\s*(.+)$', content, re.MULTILINE)
            if match:
                source_url = match.group(1).strip()
                rel_md_path = str(md_file.relative_to(output_dir))
                source_to_md[source_url] = rel_md_path
        except:
            continue

    def resolve_html_link(source_html: str, href: str) -> str:
        """Resolve a relative HTML link."""
        href = href.split('#')[0].strip()
        if not href or href.startswith(('http://', 'https://', 'mailto:')):
            return None

        source_dir = posixpath.dirname(source_html)
        resolved = posixpath.join(source_dir, href)
        return posixpath.normpath(resolved)

    def calculate_relative_path(from_path: str, to_path: str) -> str:
        """Calculate relative path between two files."""
        from_dir = posixpath.dirname(from_path)
        from_parts = from_dir.split('/') if from_dir else []
        to_parts = to_path.split('/')

        # Find common prefix
        common = 0
        for f, t in zip(from_parts, to_parts):
            if f == t:
                common += 1
            else:
                break

        # Build relative path
        ups = len(from_parts) - common
        downs = to_parts[common:]
        rel_parts = ['..'] * ups + list(downs)
        return '/'.join(rel_parts) if rel_parts else '.'

    # Fix links in each file
    modified_count = 0

    for md_file in output_dir.glob("**/*.md"):
        if md_file.name == "README.md":
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get source_url
            source_match = re.search(r'^source_url:\s*(.+)$', content, re.MULTILINE)
            if not source_match:
                continue

            source_html = source_match.group(1).strip()
            md_rel_path = str(md_file.relative_to(output_dir))
            original_content = content

            # Replace links
            def replace_link(match):
                text = match.group(1)
                href = match.group(2)

                # Skip if not HTML or already fixed
                if not '.html' in href or href.startswith(('http://', 'https://', 'mailto:', '#')) or href.endswith('.md'):
                    return match.group(0)

                # Resolve HTML path
                resolved_html = resolve_html_link(source_html, href)
                if not resolved_html:
                    return match.group(0)

                # Look up target MD file
                if resolved_html in source_to_md:
                    target_md = source_to_md[resolved_html]
                    rel_link = calculate_relative_path(md_rel_path, target_md)
                    return f'[{text}]({rel_link})'

                return match.group(0)

            content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, content)

            # Write if changed
            if content != original_content:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                modified_count += 1

        except Exception as e:
            logger.error(f"Error fixing links in {md_file}: {e}")
            continue

    return modified_count


def main():
    """Main conversion pipeline."""
    start_time = time.time()

    logger.info("="*60)
    logger.info("OpenUP HTML to Markdown Converter")
    logger.info("="*60)

    # Initialize path mapper
    logger.info("Initializing path mapper...")
    path_mapper = PathMapper()

    # Phase 1: Discovery (find all HTML files)
    logger.info("\nPhase 1: Discovery")
    logger.info("-" * 40)

    # Find all HTML files
    logger.info("Finding all HTML files...")
    html_files = list(SOURCE_DIR.glob("**/*.html"))

    # Filter out index and navigation files
    discovered_files = {}
    for html_path in html_files:
        rel_path = str(html_path.relative_to(SOURCE_DIR))

        # Skip index files, navigation, and utility folders
        rel_path_lower = rel_path.lower()
        skip_patterns = ['index.htm', 'logs/', 'noapplet/', 'applet/', 'nav_view']
        if any(rel_path_lower.startswith(pattern) or f'/{pattern}' in rel_path_lower or pattern in rel_path_lower
               for pattern in skip_patterns):
            continue

        discovered_files[rel_path] = html_path

        # Parse and register with path mapper
        try:
            from converter.parser import HTMLParser
            parser = HTMLParser(html_path)
            metadata = parser.extract_metadata()
            title = metadata.get('presentationName') or metadata.get('page_title') or metadata.get('title', 'Untitled')
            uma_type = metadata.get('type', 'Unknown')
            path_mapper.register_file(rel_path, title, uma_type)
        except Exception as e:
            logger.debug(f"Error registering {rel_path}: {e}")

    if not discovered_files:
        logger.error("No files discovered! Check source directory.")
        return 1

    logger.info(f"Discovered {len(discovered_files)} HTML files")

    # Phase 2: Conversion (parallel)
    logger.info("\nPhase 2: Conversion")
    logger.info("-" * 40)

    converter = MarkdownConverter(path_mapper)

    # Prepare tasks
    tasks = [(rel_path, abs_path, converter) for rel_path, abs_path in discovered_files.items()]

    # Process in parallel
    successful = 0
    failed = 0
    results = []

    logger.info(f"Converting {len(tasks)} files using {PARALLEL_WORKERS} workers...")

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = [executor.submit(convert_single_file, task) for task in tasks]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result[1]:  # Success
                successful += 1
                if successful % 50 == 0:
                    logger.info(f"Progress: {successful}/{len(tasks)} files converted")
            else:
                failed += 1

    # Phase 3: Write files
    logger.info("\nPhase 3: Writing files")
    logger.info("-" * 40)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    written_files = {}  # Track for link fixing
    for result in results:
        if result[1]:  # Success
            rel_path, success, new_path, content = result
            write_markdown_file(OUTPUT_DIR, new_path, content)
            written_files[rel_path] = (new_path, content)
            written += 1

    # Phase 4: Fix internal links
    logger.info("\nPhase 4: Fixing internal links")
    logger.info("-" * 40)

    fixed_count = fix_internal_links(OUTPUT_DIR, path_mapper)
    logger.info(f"Fixed links in {fixed_count} files")

    # Phase 4.5: Populate related metadata
    logger.info("\nPhase 4.5: Populating related metadata")
    logger.info("-" * 40)

    related_count = populate_related_metadata(OUTPUT_DIR, path_mapper)
    logger.info(f"Populated related metadata in {related_count} files")

    # Phase 5: Generate manifest
    logger.info("\nPhase 5: Generating manifest")
    logger.info("-" * 40)

    manifest_data = generate_manifest(OUTPUT_DIR)

    # Write manifest.json
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated manifest with {manifest_data['total_files']} files")
    logger.info(f"Content types: {len(manifest_data['content_types'])}")
    logger.info(f"Keywords indexed: {len(manifest_data['index']['by_keyword'])}")

    # Phase 6: Extract referenced images and copy only those
    logger.info("\nPhase 6: Extracting image references")
    logger.info("-" * 40)

    referenced_images = extract_referenced_images(SOURCE_DIR)
    logger.info(f"Found {len(referenced_images)} image references in HTML source files")

    logger.info("\nPhase 6.5: Copying referenced images")
    logger.info("-" * 40)

    image_mapping = copy_images(SOURCE_DIR, OUTPUT_DIR, referenced_images)
    logger.info(f"Copied/converted {len(image_mapping)} image files to /images/")

    # Phase 7: Fix image references
    logger.info("\nPhase 7: Fixing image references")
    logger.info("-" * 40)

    img_refs_fixed = fix_image_references(OUTPUT_DIR, image_mapping, path_mapper)
    logger.info(f"Fixed image references in {img_refs_fixed} files")

    # Phase 7.5: Generate image sidecar files
    logger.info("\nPhase 7.5: Generating image sidecar descriptions")
    logger.info("-" * 40)

    sidecars_generated = generate_image_sidecars(SOURCE_DIR, OUTPUT_DIR, image_mapping)
    logger.info(f"Generated {sidecars_generated} image sidecar files")

    # Phase 8: Add sidecar links to markdown files
    logger.info("\nPhase 8: Adding sidecar links to documents")
    logger.info("-" * 40)

    sidecar_links_added = add_image_sidecar_links(OUTPUT_DIR)
    logger.info(f"Added sidecar links in {sidecar_links_added} files")

    # Summary
    elapsed = time.time() - start_time

    logger.info("\n" + "="*60)
    logger.info("Conversion Complete!")
    logger.info("="*60)
    logger.info(f"Total files:     {len(discovered_files)}")
    logger.info(f"Successful:      {successful}")
    logger.info(f"Failed:          {failed}")
    logger.info(f"Written:         {written}")
    logger.info(f"Time elapsed:    {elapsed:.2f}s")
    logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")

    if failed > 0:
        logger.warning(f"\n{failed} files failed to convert. Check logs for details.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
