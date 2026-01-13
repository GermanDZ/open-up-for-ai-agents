#!/bin/bash
# bootstrap-project.sh - Bootstrap a new project from this template

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect template root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Function to print error and exit
error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Function to print warning
warn() {
    echo -e "${YELLOW}Warning: $1${NC}" >&2
}

# Function to print success
success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] <project_name>

Bootstrap a new project from the OpenUP template.

Arguments:
  project_name          Name of the project (folder name)

Options:
  --base-dir DIR        Target directory where to create the project (default: ./)
  -h, --help           Show this help message

Examples:
  $0 my-project
  $0 my-project --base-dir ~/projects
  $0 my-project --base-dir /path/to/projects

EOF
}

# Parse command-line arguments
BASE_DIR="./"
PROJECT_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --base-dir)
            BASE_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            error_exit "Unknown option: $1. Use --help for usage information."
            ;;
        *)
            if [ -z "$PROJECT_NAME" ]; then
                PROJECT_NAME="$1"
            else
                error_exit "Multiple project names provided. Use --help for usage information."
            fi
            shift
            ;;
    esac
done

# Validate project name was provided
if [ -z "$PROJECT_NAME" ]; then
    error_exit "Project name is required. Use --help for usage information."
fi

# Expand ~ to home directory and normalize path
TARGET_DIR="${BASE_DIR/#\~/$HOME}"
TARGET_DIR="$(echo "$TARGET_DIR" | sed 's:/*$::')"  # Remove trailing slashes

# Validate target directory
if [ -z "$TARGET_DIR" ]; then
    error_exit "Target directory cannot be empty"
fi

# Create target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR" || error_exit "Failed to create target directory: $TARGET_DIR"
fi

# Validate project name
if [ -z "$PROJECT_NAME" ]; then
    error_exit "Project name cannot be empty"
fi

# Check for invalid characters in project name
if [[ "$PROJECT_NAME" =~ [/\\] ]]; then
    error_exit "Project name cannot contain slashes: $PROJECT_NAME"
fi

# Check for invalid characters in project name
if [[ "$PROJECT_NAME" =~ [/\\] ]]; then
    error_exit "Project name cannot contain slashes: $PROJECT_NAME"
fi

# Full path to new project
PROJECT_PATH="$TARGET_DIR/$PROJECT_NAME"

# Check if project directory already exists
if [ -d "$PROJECT_PATH" ]; then
    echo ""
    warn "Project directory already exists: $PROJECT_PATH"
    read -p "Overwrite existing directory? (y/n): " OVERWRITE
    if [ "$OVERWRITE" = "y" ] || [ "$OVERWRITE" = "Y" ]; then
        echo "Removing existing directory..."
        rm -rf "$PROJECT_PATH" || error_exit "Failed to remove existing directory"
    else
        echo "Aborted. Exiting."
        exit 0
    fi
fi

# Create project directory
echo ""
echo "Creating project directory..."
mkdir -p "$PROJECT_PATH" || error_exit "Failed to create project directory: $PROJECT_PATH"

# Copy essential files
echo "Copying essential files..."

# Copy docs-eng-process/ directory
if [ ! -d "$TEMPLATE_ROOT/docs-eng-process" ]; then
    error_exit "Template directory docs-eng-process/ not found in $TEMPLATE_ROOT"
fi
cp -r "$TEMPLATE_ROOT/docs-eng-process" "$PROJECT_PATH/" || error_exit "Failed to copy docs-eng-process/"

# Copy entrypoint files
for file in AGENTS.md README.md .gitignore .gitattributes; do
    if [ -f "$TEMPLATE_ROOT/$file" ]; then
        cp "$TEMPLATE_ROOT/$file" "$PROJECT_PATH/" || error_exit "Failed to copy $file"
    else
        warn "File $file not found in template, skipping"
    fi
done

# Create docs/ directory and copy .gitkeep
mkdir -p "$PROJECT_PATH/docs"
if [ -f "$TEMPLATE_ROOT/docs/.gitkeep" ]; then
    cp "$TEMPLATE_ROOT/docs/.gitkeep" "$PROJECT_PATH/docs/" || error_exit "Failed to copy docs/.gitkeep"
else
    # Create .gitkeep if it doesn't exist
    touch "$PROJECT_PATH/docs/.gitkeep"
fi

# Initialize git and create initial commit
echo "Initializing git repository..."
if command -v git >/dev/null 2>&1; then
    cd "$PROJECT_PATH" || error_exit "Failed to change to project directory"
    if git init >/dev/null 2>&1; then
        success "Git repository initialized"
        
        # Stage all files
        echo "Staging files..."
        git add . >/dev/null 2>&1 || warn "Failed to stage files"
        
        # Create initial commit
        echo "Creating initial commit..."
        if git commit -m "Initial commit: Bootstrap project from OpenUP template" >/dev/null 2>&1; then
            success "Initial commit created"
            
            # Verify clean working directory
            if [ -z "$(git status --porcelain)" ]; then
                success "Working directory is clean"
            else
                warn "Working directory has uncommitted changes"
            fi
        else
            warn "Failed to create initial commit, but continuing..."
        fi
    else
        warn "Git init failed, but continuing..."
    fi
    cd - >/dev/null 2>&1 || true  # Ignore cd - failure
else
    warn "Git not found. Skipping git initialization."
fi

# Print success message
echo ""
success "✅ Project '$PROJECT_NAME' initialized at $PROJECT_PATH"
echo ""
echo "Next steps:"
echo "1. cd $PROJECT_PATH"
echo "2. Review docs-eng-process/init-prompts.md"
echo "3. Copy Prompt A and run it with your AI agent"
echo "4. After setup completes, run Prompt B for Vision Q&A"
echo ""
echo "For manual setup, see: docs-eng-process/getting-started.md"
echo ""
