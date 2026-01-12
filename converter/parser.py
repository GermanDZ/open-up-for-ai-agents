"""HTML parsing and content extraction."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from bs4 import BeautifulSoup, Tag

from .config import SKIP_SELECTORS, CONTENT_SELECTORS


class HTMLParser:
    """Parse OpenUP HTML files and extract content."""

    def __init__(self, html_path: Path):
        """Initialize parser with HTML file."""
        self.path = html_path
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.soup = BeautifulSoup(f.read(), 'lxml')

    def extract_metadata(self) -> Dict[str, str]:
        """Extract UMA metadata from HTML head."""
        metadata = {}

        # Extract from meta tags
        for meta in self.soup.find_all('meta'):
            name = meta.get('name', '')
            content = meta.get('content', '')

            if name.startswith('uma.'):
                key = name.replace('uma.', '')
                metadata[key] = content
            elif name in ['element_type', 'filetype', 'role']:
                metadata[name] = content

        # Extract title
        title_tag = self.soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()

        # Extract from page structure
        page_title = self.soup.find('td', class_='pageTitle')
        if page_title:
            metadata['page_title'] = page_title.get_text().strip()

        # Extract page GUID
        guid_div = self.soup.find('div', id='page-guid')
        if guid_div:
            metadata['page_guid'] = guid_div.get('value', '')

        return metadata

    def extract_overview(self) -> str:
        """Extract overview/summary text."""
        overview_div = self.soup.find('div', class_='overview')
        if not overview_div:
            return ""

        # Get text content, clean up
        text = overview_div.get_text(separator='\n', strip=True)
        return text

    def extract_links(self) -> Set[str]:
        """Extract all internal HTML links."""
        links = set()

        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip external links, anchors, and non-HTML
            if href.startswith(('http://', 'https://', 'mailto:', '#')):
                continue

            # Only process .html links
            if not href.endswith('.html') and '.html#' not in href:
                continue

            # Remove anchor fragments
            href = href.split('#')[0]

            links.add(href)

        return links

    def extract_relationships(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Extract relationship links categorized by type.

        Returns:
            Dict mapping relationship type to list of (title, href) tuples
        """
        relationships = {
            'roles': [],
            'tasks': [],
            'workproducts': [],
            'concepts': [],
            'guidelines': [],
            'examples': [],
            'templates': [],
            'other': []
        }

        # Find the Relationships section
        rel_heading = self.soup.find('div', class_='sectionHeading', string=re.compile(r'Relationships?', re.I))
        if not rel_heading:
            return relationships

        # Get the content div that follows
        rel_content = rel_heading.find_next_sibling('div', class_='sectionContent')
        if not rel_content:
            return relationships

        # Extract all links from the relationships section
        for a_tag in rel_content.find_all('a', href=True):
            href = a_tag['href']
            title = a_tag.get_text(strip=True)

            # Skip external links
            if href.startswith(('http://', 'https://', 'mailto:', '#')):
                continue

            # Remove anchor
            href = href.split('#')[0]

            # Categorize by path or title
            category = self._categorize_link(href, title)
            relationships[category].append((title, href))

        return relationships

    def _categorize_link(self, href: str, title: str) -> str:
        """Categorize a link by its path or title."""
        href_lower = href.lower()
        title_lower = title.lower()

        # Check path components
        if '/roles/' in href_lower or 'role_def' in href_lower:
            return 'roles'
        elif '/tasks/' in href_lower:
            return 'tasks'
        elif '/workproducts/' in href_lower or 'artifact' in href_lower:
            return 'workproducts'
        elif '/concepts/' in href_lower or 'concept' in href_lower:
            return 'concepts'
        elif '/guidelines/' in href_lower or 'guideline' in href_lower:
            return 'guidelines'
        elif '/examples/' in href_lower:
            return 'examples'
        elif '/templates/' in href_lower:
            return 'templates'

        # Check title prefixes
        if title_lower.startswith('role:'):
            return 'roles'
        elif title_lower.startswith('task:'):
            return 'tasks'
        elif title_lower.startswith(('artifact:', 'work product:')):
            return 'workproducts'
        elif title_lower.startswith('concept:'):
            return 'concepts'
        elif title_lower.startswith('guideline:'):
            return 'guidelines'
        elif title_lower.startswith('example:'):
            return 'examples'
        elif title_lower.startswith('template:'):
            return 'templates'

        return 'other'

    def extract_content(self) -> BeautifulSoup:
        """
        Extract main content, removing navigation and boilerplate.

        Returns:
            BeautifulSoup object with cleaned content
        """
        # Clone the soup to avoid modifying the original
        content = BeautifulSoup(str(self.soup), 'lxml')

        # Remove skip elements
        for selector in SKIP_SELECTORS:
            for element in content.select(selector):
                element.decompose()

        # Remove image shims
        for img in content.find_all('img', src=re.compile(r'shim\.gif')):
            img.decompose()

        # Remove empty script tags
        for script in content.find_all('script'):
            script.decompose()

        # Extract only the main content area
        main_content = content.find('td', valign='top')
        if not main_content:
            return content

        # Create new soup with just the content
        clean_soup = BeautifulSoup('<div class="content"></div>', 'lxml')
        content_div = clean_soup.find('div', class_='content')

        # Add overview
        overview = main_content.find('div', class_='overview')
        if overview:
            content_div.append(BeautifulSoup(str(overview), 'lxml'))

        # Add all section content divs
        for section in main_content.find_all('div', class_='sectionHeading'):
            # Add the heading
            content_div.append(BeautifulSoup(str(section), 'lxml'))

            # Add the following content
            section_content = section.find_next_sibling('div', class_='sectionContent')
            if section_content:
                content_div.append(BeautifulSoup(str(section_content), 'lxml'))

        return clean_soup

    def extract_keywords(self) -> List[str]:
        """Extract keywords from title and overview."""
        keywords = set()

        metadata = self.extract_metadata()
        title = metadata.get('page_title', metadata.get('title', ''))

        # Remove type prefix (e.g., "Role: Architect" -> "Architect")
        title = re.sub(r'^[^:]+:\s*', '', title)

        # Extract words from title
        words = re.findall(r'\b[a-z]{4,}\b', title.lower())
        keywords.update(words)

        # Extract from overview
        overview = self.extract_overview()
        overview_words = re.findall(r'\b[a-z]{4,}\b', overview.lower()[:500])  # First 500 chars
        # Take most common words (simple heuristic)
        from collections import Counter
        common_words = Counter(overview_words).most_common(10)
        keywords.update(word for word, count in common_words if count >= 2)

        # Remove common stop words
        stop_words = {'this', 'that', 'with', 'from', 'have', 'will', 'been', 'were', 'they', 'their', 'what', 'when', 'where', 'which', 'while', 'about', 'should', 'could', 'would', 'these', 'those', 'there'}
        keywords = keywords - stop_words

        return sorted(list(keywords))[:10]  # Max 10 keywords
