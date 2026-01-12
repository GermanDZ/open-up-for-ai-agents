"""Convert HTML content to Markdown."""

import html2text
import re
import yaml
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List

from .config import MARKDOWN_CONFIG
from .parser import HTMLParser
from .path_mapper import PathMapper


class MarkdownConverter:
    """Convert HTML content to Markdown with frontmatter."""

    def __init__(self, path_mapper: PathMapper):
        """Initialize converter."""
        self.path_mapper = path_mapper
        self.h2t = html2text.HTML2Text()

        # Configure html2text
        self.h2t.body_width = MARKDOWN_CONFIG['body_width']
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.skip_internal_links = False
        self.h2t.inline_links = True
        self.h2t.wrap_links = False
        self.h2t.unicode_snob = True
        self.h2t.escape_snob = True

    def convert_file(self, html_path: Path, original_rel_path: str) -> str:
        """
        Convert an HTML file to Markdown with frontmatter.

        Args:
            html_path: Absolute path to HTML file
            original_rel_path: Original relative path (for mapping)

        Returns:
            Complete markdown content with frontmatter
        """
        # Parse HTML
        parser = HTMLParser(html_path)

        # Extract metadata
        metadata = parser.extract_metadata()
        relationships = parser.extract_relationships()
        keywords = parser.extract_keywords()

        # Extract content
        content_soup = parser.extract_content()

        # Convert to markdown
        markdown_body = self._html_to_markdown(content_soup, original_rel_path)

        # Build frontmatter
        frontmatter = self._build_frontmatter(
            metadata, relationships, keywords, original_rel_path
        )

        # Combine
        full_content = f"---\n{frontmatter}---\n\n{markdown_body}"

        return full_content

    def _build_frontmatter(
        self,
        metadata: Dict[str, str],
        relationships: Dict[str, List[tuple]],
        keywords: List[str],
        original_path: str
    ) -> str:
        """Build YAML frontmatter."""
        # Determine title
        title = metadata.get('presentationName') or metadata.get('page_title') or metadata.get('title', 'Untitled')
        # Remove type prefix
        title = re.sub(r'^[^:]+:\s*', '', title)

        # Build frontmatter dict
        fm = {
            'title': title,
            'source_url': original_path,
            'type': metadata.get('type', 'Unknown'),
        }

        # Add optional metadata
        if 'name' in metadata:
            fm['uma_name'] = metadata['name']
        if 'page_guid' in metadata:
            fm['page_guid'] = metadata['page_guid']

        # Add related items (slugify the hrefs to match new filenames)
        related = {}
        for rel_type, items in relationships.items():
            if items and rel_type != 'other':
                # Extract slugs from links
                slugs = []
                for title, href in items:
                    # Try to find the mapped path
                    target_path = self._resolve_relative_path(original_path, href)
                    new_path = self.path_mapper.get_new_path(target_path)

                    if new_path:
                        # Extract filename without extension
                        slug = Path(new_path).stem
                        slugs.append(slug)

                if slugs:
                    related[rel_type] = slugs

        if related:
            fm['related'] = related

        # Add keywords
        if keywords:
            fm['keywords'] = keywords

        # Convert to YAML
        return yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _html_to_markdown(self, soup: BeautifulSoup, source_path: str) -> str:
        """Convert HTML soup to Markdown, transforming links."""
        # Transform internal links before conversion
        for a_tag in soup.find_all('a', href=True):
            original_href = a_tag['href']

            # Skip anchors and external links
            if original_href.startswith(('http://', 'https://', 'mailto:', '#')):
                continue

            # Transform the link
            resolved = self._resolve_relative_path(source_path, original_href)
            new_href = self.path_mapper.transform_link(source_path, original_href)

            if new_href:
                a_tag['href'] = new_href

        # Convert to markdown
        html_str = str(soup)
        markdown = self.h2t.handle(html_str)

        # Clean up markdown
        markdown = self._clean_markdown(markdown)

        return markdown

    def _resolve_relative_path(self, source: str, href: str) -> str:
        """Resolve a relative href from source file."""
        from pathlib import PurePosixPath

        # Remove anchor
        href = href.split('#')[0]

        # Resolve relative path
        source_dir = str(PurePosixPath(source).parent)
        resolved = str(PurePosixPath(source_dir) / href)

        # Normalize
        return str(PurePosixPath(resolved))

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown output."""
        # Remove decorative table-leading images
        # Pattern: ![](path/to/image.png)|  | content or ![](path/to/image.png)|  |\n---
        # These are from HTML table structures where first cell (50px width) has decorative icon
        # The "|  |" (pipe-spaces-pipe) indicates empty first column in converted table
        # This pattern is consistent across all OpenUP HTML: role.gif, task.gif, guidance.gif, etc.
        # Match ANY image path (not just those with /images/) followed by |  |
        markdown = re.sub(
            r'!\[\]\([^)]+\)\s*\|\s*\|',
            '',
            markdown
        )

        # Remove decorative inline type indicator icons
        # Pattern: ![](images/role.gif)[Link Text] or ![](../images/task.gif)[Link]
        # These are small icons next to links indicating content type
        type_icons = [
            'role', 'task', 'artifact', 'concept', 'guideline', 'guidance', 'practice',
            'checklist', 'template', 'report', 'example', 'tool', 'technique',
            'roadmap', 'whitepaper', 'deliverable', 'workproduct', 'outcome',
            'discipline', 'phase', 'iteration', 'activity',
            'true', 'false'  # Checkmark/boolean decorative icons
        ]
        for icon_type in type_icons:
            # Match: ![](path/icon.gif) or ![alt text](path/icon.png)
            # Handles both empty alt text and descriptive alt text like ![Yes] or ![Artifact]
            markdown = re.sub(
                rf'!\[[^\]]*\]\([^)]*/{icon_type}\.(?:gif|png)\)',
                '',
                markdown,
                flags=re.IGNORECASE
            )

        # Remove excessive blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Clean up list formatting
        markdown = re.sub(r'\n\s*\n(\s*[-*])', r'\n\1', markdown)

        # Remove trailing whitespace
        lines = [line.rstrip() for line in markdown.split('\n')]
        markdown = '\n'.join(lines)

        # Ensure single trailing newline
        markdown = markdown.rstrip() + '\n'

        return markdown
