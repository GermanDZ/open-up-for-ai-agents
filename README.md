# OpenUP HTML to Markdown Converter

A Python-based converter that transforms Eclipse Process Framework (EPF) OpenUP HTML documentation into a clean, well-structured Markdown knowledge base with AI-agent-friendly indexing.

## Features

✨ **Complete Conversion Pipeline**
- Discovers and converts 960+ HTML files to Markdown
- Preserves UMA (Unified Method Architecture) metadata
- Extracts and structures relationships between documents
- Converts images (GIF → PNG)
- Generates comprehensive `manifest.json` index

✨ **Clean Output**
- Humanized folder structure (removes Java-style package naming)
- Working internal links (transformed to relative `.md` paths)
- YAML frontmatter with complete metadata
- Proper image path resolution

✨ **AI-Optimized**
- `manifest.json` with 3 indexes (by_type, by_keyword, by_slug)
- Structured relationship data in frontmatter
- 347 indexed keywords
- 31 content types categorized

## Quick Start

### Prerequisites

- Python 3.10+
- `curl` or `wget` (for downloading source files)
- `unzip` utility

### Installation

```bash
# Clone or download this repository
cd open-up-for-ai-agents

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Download Source Files

The OpenUP source files are not included in the repository. Download them first:

```bash
# Download and extract OpenUP source files (~15 MB)
bash scripts/download_openup.sh
```

This will:
- Download from Eclipse archive: https://archive.eclipse.org/epf/downloads/OpenUP/published/openup_published_1.5.1.5_20121212.zip
- Extract to `.tmp/openup/` directory
- Verify ~961 HTML files are present

### Usage

**Single command converts everything:**

```bash
python3 scripts/convert.py
```

**Output:**
- `openup-knowledge-base/` - 960 markdown files
- `openup-knowledge-base/manifest.json` - Complete index
- `openup-knowledge-base/images/` - Converted images

**Processing time:** ~15 seconds

## Conversion Pipeline

The converter runs 7 phases automatically:

1. **Discovery** - Find all HTML files (glob-based)
2. **Conversion** - HTML → Markdown (parallel, 8 workers)
3. **Write Files** - Save markdown files with frontmatter
4. **Fix Internal Links** - Transform `.html` → `.md` links
5. **Populate Related Metadata** - Extract relationships
6. **Generate Manifest** - Create `manifest.json` index
7. **Copy Images** - Copy/convert images (GIF → PNG)
8. **Fix Image References** - Update image paths

## Project Structure

```
open-up-for-ai-agents/
├── converter/              # Core conversion modules
│   ├── config.py          # Configuration and path mappings
│   ├── parser.py          # HTML parsing and metadata extraction
│   ├── path_mapper.py     # Path transformation logic
│   └── markdown_converter.py  # HTML to Markdown conversion
├── scripts/
│   └── convert.py         # Main conversion script (single entry point)
├── requirements.txt       # Python dependencies
├── .tmp/
│   └── openup/           # Source HTML files (not in repo)
└── openup-knowledge-base/ # Generated output (not in repo)
    ├── manifest.json     # AI-friendly index
    ├── images/           # Converted images
    ├── core/             # Core roles, disciplines, concepts
    ├── practice-management/   # Management practices
    ├── practice-technical/    # Technical practices
    ├── practice-general/      # General practices
    ├── guides/           # Supporting materials
    └── process/          # Delivery processes
```

## Output Structure

### Markdown Files

Each file includes YAML frontmatter:

```yaml
---
title: "Page Title"
source_url: "original/html/path.html"
type: "Role|Task|Artifact|Concept|Guideline..."
uma_name: "internal_name"
page_guid: "_uniqueGUID"
keywords:
  - keyword1
  - keyword2
related:
  roles:
    - role-slug
  tasks:
    - task-slug
  workproducts:
    - artifact-slug
---
```

### Manifest.json

AI-friendly index with:

```json
{
  "version": "1.0",
  "generated": "2026-01-12",
  "title": "OpenUP Knowledge Base",
  "total_files": 960,
  "content_types": {...},
  "files": [...],
  "index": {
    "by_type": {...},
    "by_keyword": {...},
    "by_slug": {...}
  }
}
```

**Use cases:**
- Quick lookup by slug
- Filter by content type
- Search by keyword
- Traverse relationships
- Get statistics

## Configuration

Edit `converter/config.py` to customize:

- `SOURCE_DIR` - Input HTML directory
- `OUTPUT_DIR` - Output markdown directory
- `PARALLEL_WORKERS` - Number of parallel workers (default: 8)
- `PATH_MAPPINGS` - Path transformation rules
- Content type mappings and parsing selectors

## Dependencies

```
beautifulsoup4==4.12.3  # HTML parsing
lxml==5.1.0             # XML/HTML processing
html2text==2024.2.26    # HTML to Markdown conversion
PyYAML==6.0.1           # YAML frontmatter generation
Pillow>=12.0.0          # Image conversion (GIF to PNG)
```

## Results

**Conversion Statistics:**
- ✅ 960/961 files converted (99.9% success)
- ✅ 740 files with fixed internal links
- ✅ 473 files with populated related metadata
- ✅ 233 images copied/converted
- ✅ 916 files with fixed image references
- ✅ 31 content types categorized
- ✅ 347 unique keywords indexed

**Content Types:**
- WorkProductDescriptor (154)
- Activity (130)
- CapabilityPattern (85)
- Guideline (55)
- Concept (52)
- And 26 more types...

## Advanced Usage

### Query Manifest Programmatically

```python
import json

# Load manifest
manifest = json.load(open('openup-knowledge-base/manifest.json'))

# Get all Roles
roles = manifest['index']['by_type']['Role']

# Find by keyword
iterations = manifest['index']['by_keyword']['iteration']

# Lookup specific page
architect = manifest['index']['by_slug']['architect-6']
print(f"{architect['title']}: {architect['path']}")
```

### Customize Path Mappings

Edit `PATH_MAPPINGS` in `converter/config.py`:

```python
PATH_MAPPINGS = {
    r"practice\.mgmt\.": "practice-management/",
    r"practice\.tech\.": "practice-technical/",
    # Add your own mappings...
}
```

## Development

The codebase is organized into modular components:

- **parser.py** - Extracts content and metadata from HTML
- **path_mapper.py** - Transforms paths and manages slug generation
- **markdown_converter.py** - Converts HTML to Markdown with frontmatter
- **convert.py** - Orchestrates the complete pipeline

All post-processing (link fixing, metadata population, manifest generation) is integrated into the main script for single-command execution.

## Troubleshooting

**Issue:** `No such file or directory: .tmp/openup`
- **Solution:** Place source HTML files in `.tmp/openup/` directory

**Issue:** Import errors
- **Solution:** Ensure virtual environment is activated and dependencies installed

**Issue:** Permission errors
- **Solution:** Check file permissions on source and output directories

## License

This converter tool is provided as-is. The OpenUP content it processes is made available under the Eclipse Public License V1.0.

## Credits

Converts Eclipse Process Framework (EPF) OpenUP documentation.

**Conversion Tool:**
- BeautifulSoup4 for HTML parsing
- html2text for Markdown generation
- Pillow for image conversion
- Custom Python pipeline for complete transformation
