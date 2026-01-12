"""Path mapping and transformation utilities."""

import re
from pathlib import Path, PurePosixPath
from typing import Dict, Optional
from urllib.parse import unquote, urlparse

from .config import PATH_MAPPINGS, REMOVE_SUFFIXES


def slugify(text: str) -> str:
    """Convert text to slug format."""
    # Remove special characters
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace whitespace with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


class PathMapper:
    """Maps original HTML paths to new markdown paths."""

    def __init__(self):
        self.mapping: Dict[str, str] = {}  # original_path -> new_path
        self.reverse_mapping: Dict[str, str] = {}  # new_path -> original_path
        self.title_cache: Dict[str, str] = {}  # original_path -> title
        self.slug_counts: Dict[str, int] = {}  # slug -> count (for deduplication)

    def register_file(self, original_path: str, title: str, uma_type: str) -> str:
        """
        Register a file and return its new path.

        Args:
            original_path: Original HTML file path
            title: Page title
            uma_type: UMA content type (Role, Task, etc.)

        Returns:
            New markdown file path
        """
        if original_path in self.mapping:
            return self.mapping[original_path]

        # Parse the original path
        path = PurePosixPath(original_path)
        parts = list(path.parts)

        # Transform directory structure
        new_parts = []
        i = 0
        while i < len(parts) - 1:  # Exclude filename
            part = parts[i]

            # Apply path mappings
            transformed = False
            for pattern, replacement in PATH_MAPPINGS.items():
                if re.match(pattern, part):
                    # Extract the component after the prefix
                    component = re.sub(pattern, "", part)

                    # Remove suffixes
                    for suffix in REMOVE_SUFFIXES:
                        component = component.replace(suffix, "")

                    # Add the base mapping
                    base = replacement.rstrip("/")
                    if base and base not in new_parts:
                        new_parts.append(base)

                    # Add the component if not empty
                    if component:
                        component_slug = slugify(component)
                        if component_slug:
                            new_parts.append(component_slug)

                    transformed = True
                    break

            if not transformed:
                # Keep the part as-is but slugified
                slugified = slugify(part)
                if slugified:
                    new_parts.append(slugified)

            i += 1

        # Add content type directory if not already present
        # (roles, tasks, workproducts, etc.)
        if len(parts) >= 2:
            parent_dir = parts[-2]
            if parent_dir not in new_parts:
                slugified_parent = slugify(parent_dir)
                if slugified_parent and slugified_parent not in new_parts:
                    new_parts.append(slugified_parent)

        # Generate filename from title
        base_slug = slugify(title)

        # Handle duplicates
        slug = base_slug
        if slug in self.slug_counts:
            self.slug_counts[slug] += 1
            slug = f"{base_slug}-{self.slug_counts[slug]}"
        else:
            self.slug_counts[slug] = 0

        filename = f"{slug}.md"

        # Construct new path
        new_path = "/".join(new_parts + [filename])

        # Store mappings
        self.mapping[original_path] = new_path
        self.reverse_mapping[new_path] = original_path
        self.title_cache[original_path] = title

        return new_path

    def transform_link(self, source_file: str, target_link: str) -> Optional[str]:
        """
        Transform an HTML link to markdown format.

        Args:
            source_file: Original path of the file containing the link
            target_link: The href value to transform

        Returns:
            Transformed markdown link, or None if not internal
        """
        # Skip external links
        if target_link.startswith(('http://', 'https://', 'mailto:', '#')):
            return None

        # Resolve relative path
        source_dir = str(PurePosixPath(source_file).parent)
        target_path = str(PurePosixPath(source_dir) / target_link)

        # Normalize path
        target_path = str(PurePosixPath(target_path))

        # Remove .html extension
        if target_path.endswith('.html'):
            target_path = target_path[:-5] + '.html'  # Keep for lookup

        # Look up in mapping
        if target_path not in self.mapping:
            # File not discovered yet - return None for now
            return None

        new_target = self.mapping[target_path]
        new_source = self.mapping.get(source_file)

        if not new_source:
            return new_target

        # Calculate relative path
        new_source_dir = str(PurePosixPath(new_source).parent)
        try:
            rel_path = PurePosixPath(new_target).relative_to(new_source_dir)
            return str(rel_path)
        except ValueError:
            # Not relative - calculate using common base
            source_parts = PurePosixPath(new_source_dir).parts
            target_parts = PurePosixPath(new_target).parts

            # Find common prefix
            common = 0
            for s, t in zip(source_parts, target_parts):
                if s == t:
                    common += 1
                else:
                    break

            # Build relative path
            ups = len(source_parts) - common
            downs = target_parts[common:]

            rel_parts = ['..'] * ups + list(downs)
            return '/'.join(rel_parts)

    def get_new_path(self, original_path: str) -> Optional[str]:
        """Get the new path for an original path."""
        return self.mapping.get(original_path)

    def get_original_path(self, new_path: str) -> Optional[str]:
        """Get the original path for a new path."""
        return self.reverse_mapping.get(new_path)
