#!/bin/bash
# test-scripts.sh - Test all framework scripts
# Usage: ./tests/test-scripts.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test functions
test_start() {
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${BLUE}Test $TESTS_RUN: $1${NC}"
}

test_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

test_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo "  $2"
}

# Cleanup function
cleanup() {
    rm -rf /tmp/openup-test-* 2>/dev/null || true
}

# Set trap for cleanup
trap cleanup EXIT

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}=== OpenUP Framework Script Tests ===${NC}"
echo ""
echo "Project root: $PROJECT_ROOT"
echo ""

# Test 1: Check all scripts exist and are executable
test_start "Script files exist and are executable"
REQUIRED_SCRIPTS=(
    "scripts/bootstrap-project.sh"
    "scripts/setup-agent-teams.sh"
    "scripts/update-from-template.sh"
    "scripts/update-openup.sh"
    "scripts/update-openup-simple.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$script" ]; then
        test_fail "Script exists" "$script not found"
    elif [ ! -x "$PROJECT_ROOT/$script" ]; then
        test_fail "Script executable" "$script is not executable"
    else
        echo "  ✓ $script"
    fi
done
test_pass "All required scripts exist and are executable"

# Test 2: Bootstrap script creates valid project
test_start "Bootstrap script creates valid project"
TEST_DIR="/tmp/openup-test-bootstrap"
mkdir -p "$TEST_DIR"

if bash "$PROJECT_ROOT/scripts/bootstrap-project.sh" --base-dir "$TEST_DIR" test-project >/dev/null 2>&1; then
    if [ -d "$TEST_DIR/test-project" ]; then
        # Check required files
        REQUIRED_FILES=(
            "docs-eng-process"
            "docs-eng-process/agent-workflow.md"
            "docs-eng-process/how-to-work.md"
            "docs"
            ".gitignore"
        )

        MISSING=0
        for file in "${REQUIRED_FILES[@]}"; do
            if [ ! -e "$TEST_DIR/test-project/$file" ]; then
                test_fail "Bootstrap output" "Missing: $file"
                MISSING=1
            fi
        done

        if [ $MISSING -eq 0 ]; then
            test_pass "Bootstrap creates valid project structure"
        fi
    else
        test_fail "Bootstrap output" "Project directory not created"
    fi
else
    test_fail "Bootstrap execution" "Script returned non-zero exit code"
fi

# Test 3: Bootstrap script creates agent team templates
test_start "Bootstrap script installs agent team templates"
if [ -d "$TEST_DIR/test-project/.claude" ]; then
    AGENT_FILES=(
        ".claude/teammates/analyst.md"
        ".claude/teammates/architect.md"
        ".claude/teammates/developer.md"
        ".claude/teammates/project-manager.md"
        ".claude/teammates/tester.md"
        ".claude/CLAUDE.md"
    )

    MISSING=0
    for file in "${AGENT_FILES[@]}"; do
        if [ ! -f "$TEST_DIR/test-project/$file" ]; then
            test_fail "Agent team files" "Missing: $file"
            MISSING=1
        fi
    done

    if [ $MISSING -eq 0 ]; then
        test_pass "Agent team templates installed"
    fi
else
    test_fail "Agent templates" ".claude directory not created"
fi

# Test 4: Setup agent teams script
test_start "Setup agent teams script"
SETUP_TEST_DIR="/tmp/openup-test-setup"
rm -rf "$SETUP_TEST_DIR"
mkdir -p "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teammates"
mkdir -p "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teams"
mkdir -p "$SETUP_TEST_DIR/docs"

# Copy template files to test directory
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/teammates/"*.md "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teammates/" 2>/dev/null || true
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/teams/"*.md "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teams/" 2>/dev/null || true
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/CLAUDE.md" "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/" 2>/dev/null || true

cd "$SETUP_TEST_DIR"
if bash "$PROJECT_ROOT/scripts/setup-agent-teams.sh" >/dev/null 2>&1; then
    if [ -d "$SETUP_TEST_DIR/.claude/teammates" ]; then
        test_pass "Setup script creates .claude directory"
    else
        test_fail "Setup output" ".claude/teammates not created"
    fi
else
    test_fail "Setup execution" "Script returned non-zero exit code"
fi
cd "$PROJECT_ROOT"

# Test 5: Update script dry-run
test_start "Update script dry-run mode"
UPDATE_TEST_DIR="/tmp/openup-test-update"
mkdir -p "$UPDATE_TEST_DIR/docs-eng-process"
cp -r "$PROJECT_ROOT/docs-eng-process/"* "$UPDATE_TEST_DIR/docs-eng-process/" 2>/dev/null || true

cd "$UPDATE_TEST_DIR"
if bash "$PROJECT_ROOT/scripts/update-from-template.sh" --dry-run --template-dir "$PROJECT_ROOT" >/dev/null 2>&1; then
    test_pass "Update script dry-run works"
else
    test_fail "Update dry-run" "Script returned non-zero exit code"
fi
cd "$PROJECT_ROOT"

# Test 6: Update script what-new mode
test_start "Update script what-new mode"
cd "$UPDATE_TEST_DIR"
OUTPUT=$(bash "$PROJECT_ROOT/scripts/update-from-template.sh" --what-new --template-dir "$PROJECT_ROOT" 2>&1 || true)
if echo "$OUTPUT" | grep -q "What's New"; then
    test_pass "Update script what-new works"
else
    test_fail "Update what-new" "Expected output not found"
fi
cd "$PROJECT_ROOT"

# Test 7: Simple update script
test_start "Simple update script"
SIMPLE_UPDATE_DIR="/tmp/openup-test-simple"
mkdir -p "$SIMPLE_UPDATE_DIR/docs-eng-process"

cd "$SIMPLE_UPDATE_DIR"
if bash "$PROJECT_ROOT/scripts/update-openup-simple.sh" --template-dir "$PROJECT_ROOT" >/dev/null 2>&1; then
    if [ -f "$SIMPLE_UPDATE_DIR/docs-eng-process/.template-version" ]; then
        test_pass "Simple update script works"
    else
        test_fail "Simple update" "Version file not created"
    fi
else
    test_fail "Simple update execution" "Script returned non-zero exit code"
fi
cd "$PROJECT_ROOT"

# Test 8: Check template files have proper structure
test_start "Template files have proper frontmatter"
TEAMMATE_FILES=(
    "docs-eng-process/.claude-templates/teammates/analyst.md"
    "docs-eng-process/.claude-templates/teammates/architect.md"
    "docs-eng-process/.claude-templates/teammates/developer.md"
    "docs-eng-process/.claude-templates/teammates/project-manager.md"
    "docs-eng-process/.claude-templates/teammates/tester.md"
)

VALID=0
for file in "${TEAMMATE_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        # Check for required sections
        if grep -q "# Role Definition" "$PROJECT_ROOT/$file" && \
           grep -q "## Key Responsibilities" "$PROJECT_ROOT/$file" && \
           grep -q "## Work Products" "$PROJECT_ROOT/$file"; then
            VALID=$((VALID + 1))
        fi
    fi
done

if [ $VALID -eq ${#TEAMMATE_FILES[@]} ]; then
    test_pass "All teammate templates have proper structure"
else
    test_fail "Template structure" "$VALID/${#TEAMMATE_FILES[@]} files are valid"
fi

# Test 9: Check documentation files
test_start "Documentation files exist"
DOCS=(
    "docs-eng-process/README.md"
    "docs-eng-process/agent-workflow.md"
    "docs-eng-process/agent-teams-setup.md"
    "docs-eng-process/updating.md"
    "README.md"
)

MISSING=0
for doc in "${DOCS[@]}"; do
    if [ ! -f "$PROJECT_ROOT/$doc" ]; then
        test_fail "Documentation" "Missing: $doc"
        MISSING=1
    fi
done

if [ $MISSING -eq 0 ]; then
    test_pass "All documentation files exist"
fi

# Test 10: Version file exists
test_start "Version tracking file exists"
if [ -f "$PROJECT_ROOT/docs-eng-process/.template-version" ]; then
    VERSION=$(cat "$PROJECT_ROOT/docs-eng-process/.template-version")
    if [ -n "$VERSION" ]; then
        test_pass "Version file exists with content: $VERSION"
    else
        test_fail "Version file" "Version file is empty"
    fi
else
    test_fail "Version file" "Version file not found"
fi

# Summary
echo ""
echo -e "${BLUE}=== Test Summary ===${NC}"
echo ""
echo "Tests run:    $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
