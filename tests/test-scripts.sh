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
    "scripts/force-upgrade.sh"
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

# Test 4: Bootstrap script installs skills
test_start "Bootstrap script installs skills"
if [ -d "$TEST_DIR/test-project/.claude/skills" ]; then
    REQUIRED_SKILLS=(
        ".claude/skills/openup-init/SKILL.md"
        ".claude/skills/openup-start-iteration/SKILL.md"
        ".claude/skills/openup-complete-task/SKILL.md"
        ".claude/skills/openup-inception/SKILL.md"
        ".claude/skills/openup-create-vision/SKILL.md"
    )

    MISSING=0
    for file in "${REQUIRED_SKILLS[@]}"; do
        if [ ! -f "$TEST_DIR/test-project/$file" ]; then
            test_fail "Skills files" "Missing: $file"
            MISSING=1
        fi
    done

    if [ $MISSING -eq 0 ]; then
        test_pass "Skills installed with SKILL.md files"
    fi
else
    test_fail "Skills directory" ".claude/skills directory not created"
fi

# Test 4b: Bootstrap ships the process CLIs so the workflow can actually run (T-032)
test_start "Bootstrap installs the process CLIs (scripts/openup-*.py)"
MANIFEST="$PROJECT_ROOT/scripts/process-manifest.txt"
if [ ! -f "$MANIFEST" ]; then
    test_fail "Process CLI manifest" "scripts/process-manifest.txt not found"
elif [ ! -d "$TEST_DIR/test-project/scripts" ]; then
    test_fail "Process CLIs" "bootstrapped project has no scripts/ directory"
else
    MISSING=0
    # Read the manifest (strip #-comments and blank lines) so the assertion
    # tracks the single source of truth automatically.
    while IFS= read -r cli; do
        cli="$(echo "$cli" | sed -e 's/#.*//' -e 's/[[:space:]]//g')"
        [ -n "$cli" ] || continue
        if [ ! -f "$TEST_DIR/test-project/scripts/$cli" ]; then
            test_fail "Process CLI" "Missing from bootstrapped scripts/: $cli"
            MISSING=1
        fi
    done < "$MANIFEST"

    if [ $MISSING -eq 0 ]; then
        # The headline CLI must be runnable end to end.
        if python3 "$TEST_DIR/test-project/scripts/openup-state.py" --help >/dev/null 2>&1; then
            test_pass "All process CLIs shipped and openup-state.py --help exits 0"
        else
            test_fail "Process CLI runnable" "openup-state.py --help did not exit 0"
        fi
    fi
fi

# Test 5: Setup agent teams script (standalone)
test_start "Setup agent teams script"
SETUP_TEST_DIR="/tmp/openup-test-setup"
rm -rf "$SETUP_TEST_DIR"
mkdir -p "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teammates"
mkdir -p "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teams"
mkdir -p "$SETUP_TEST_DIR/docs"

# Copy template files to test directory (including skills)
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/teammates/"*.md "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teammates/" 2>/dev/null || true
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/teams/"*.md "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/teams/" 2>/dev/null || true
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/CLAUDE.md" "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/" 2>/dev/null || true
cp -r "$PROJECT_ROOT/docs-eng-process/.claude-templates/skills" "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/" 2>/dev/null || true
cp "$PROJECT_ROOT/docs-eng-process/.claude-templates/settings.json.example" "$SETUP_TEST_DIR/docs-eng-process/.claude-templates/" 2>/dev/null || true

cd "$SETUP_TEST_DIR"
if bash "$PROJECT_ROOT/scripts/setup-agent-teams.sh" >/dev/null 2>&1; then
    SETUP_OK=true
    if [ ! -d "$SETUP_TEST_DIR/.claude/teammates" ]; then
        test_fail "Setup output" ".claude/teammates not created"
        SETUP_OK=false
    fi
    if [ ! -d "$SETUP_TEST_DIR/.claude/skills" ]; then
        test_fail "Setup output" ".claude/skills not created"
        SETUP_OK=false
    fi
    if [ ! -f "$SETUP_TEST_DIR/.claude/skills/openup-init/SKILL.md" ]; then
        test_fail "Setup output" ".claude/skills/openup-init/SKILL.md not created"
        SETUP_OK=false
    fi
    if [ ! -f "$SETUP_TEST_DIR/.claude/settings.json" ]; then
        test_fail "Setup output" ".claude/settings.json not created"
        SETUP_OK=false
    fi
    if [ "$SETUP_OK" = true ]; then
        test_pass "Setup script creates .claude directory with teammates, skills, and settings"
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

# Test 7b: Force-upgrade brings an old project up to the full framework
test_start "Force-upgrade script upgrades an old project"
FU_DIR="/tmp/openup-test-force-upgrade"
rm -rf "$FU_DIR"
# Simulate a project started with an OLD version: has docs-eng-process/ on an
# old version, plus a minimal .claude/ MISSING skills, hooks, rubrics, settings,
# and a project-owned CLAUDE.md that must be preserved.
mkdir -p "$FU_DIR/docs-eng-process" "$FU_DIR/.claude/teammates" "$FU_DIR/docs"
echo "0.0.1-old" > "$FU_DIR/docs-eng-process/.template-version"
echo "# stale analyst" > "$FU_DIR/.claude/teammates/analyst.md"
printf '# My Project\n\nProject-specific stuff.\n' > "$FU_DIR/.claude/CLAUDE.md"

if bash "$PROJECT_ROOT/scripts/force-upgrade.sh" --template-dir "$PROJECT_ROOT" "$FU_DIR" >/dev/null 2>&1; then
    FU_OK=true
    # The previously-missing .claude superset must now exist.
    FU_EXPECTED=(
        ".claude/skills/openup-init/SKILL.md"
        ".claude/rubrics"
        ".claude/scripts/hooks"
        ".claude/settings.json"
        ".claude/CLAUDE.openup.md"
        "scripts/openup-state.py"
    )
    for item in "${FU_EXPECTED[@]}"; do
        if [ ! -e "$FU_DIR/$item" ]; then
            test_fail "Force-upgrade output" "Missing after upgrade: $item"
            FU_OK=false
        fi
    done
    # Version must be bumped to the framework's.
    EXPECTED_VERSION=$(cat "$PROJECT_ROOT/docs-eng-process/.template-version")
    if [ "$(cat "$FU_DIR/docs-eng-process/.template-version")" != "$EXPECTED_VERSION" ]; then
        test_fail "Force-upgrade version" "Version not bumped to $EXPECTED_VERSION"
        FU_OK=false
    fi
    # Project-owned CLAUDE.md must be preserved (not overwritten).
    if ! grep -q "Project-specific stuff" "$FU_DIR/.claude/CLAUDE.md"; then
        test_fail "Force-upgrade CLAUDE.md" "Project CLAUDE.md was not preserved"
        FU_OK=false
    fi
    if [ "$FU_OK" = true ]; then
        test_pass "Force-upgrade installs the full superset and bumps the version"
    fi
else
    test_fail "Force-upgrade execution" "Script returned non-zero exit code"
fi
cd "$PROJECT_ROOT"

# Test 7c: Force-upgrade refuses a non-OpenUP directory
test_start "Force-upgrade rejects a non-OpenUP project"
FU_BAD_DIR="/tmp/openup-test-force-upgrade-bad"
rm -rf "$FU_BAD_DIR"
mkdir -p "$FU_BAD_DIR"
if bash "$PROJECT_ROOT/scripts/force-upgrade.sh" --template-dir "$PROJECT_ROOT" "$FU_BAD_DIR" >/dev/null 2>&1; then
    test_fail "Force-upgrade guard" "Script should have failed on a directory without docs-eng-process"
else
    test_pass "Force-upgrade refuses a directory without docs-eng-process"
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

# Test 11: Sync self-commits its CLI upgrades and never sweeps unrelated work (T-052)
test_start "Sync self-commits its CLI upgrades, never sweeps unrelated work (T-052)"
SC_DIR="/tmp/openup-test-sync-commit"
rm -rf "$SC_DIR"
mkdir -p "$SC_DIR/scripts" "$SC_DIR/src"
# A consumer runs its OWN copy of the sync script, so PROJECT_ROOT resolves to it.
cp "$PROJECT_ROOT/scripts/sync-from-framework.sh" "$SC_DIR/scripts/"
# A real consumer gitignores the .claude runtime copy + .bak debris.
printf '/.claude\n.openup/\n*.bak\n' > "$SC_DIR/.gitignore"
# A tracked, STALE process CLI the sync will overwrite + unrelated user code.
cp "$PROJECT_ROOT/scripts/openup-board.py" "$SC_DIR/scripts/openup-board.py"
printf '\n# stale-marker-line\n' >> "$SC_DIR/scripts/openup-board.py"
printf 'print("v1")\n' > "$SC_DIR/src/app.py"
(
    cd "$SC_DIR"
    git init -q
    git config user.email "test@openup.local"
    git config user.name "OpenUP Test"
    git add -A
    git commit -q -m "init consumer [openup-skip]"
)
# Unrelated uncommitted edit that must survive untouched (Requirement 3).
printf 'print("v2-uncommitted")\n' > "$SC_DIR/src/app.py"

SC_OK=true
bash "$SC_DIR/scripts/sync-from-framework.sh" --framework-path "$PROJECT_ROOT" >/dev/null 2>&1 || true

# (R1) the overwritten CLI is committed — not left modified.
if [ -n "$(cd "$SC_DIR" && git status --porcelain scripts/openup-board.py)" ]; then
    test_fail "Sync self-commit R1" "scripts/openup-board.py left uncommitted after sync"
    SC_OK=false
fi
# (R2) the commit uses the canonical chore(process) + [openup-skip] subject.
SC_SUBJECT="$(cd "$SC_DIR" && git log -1 --pretty=%s)"
if ! printf '%s' "$SC_SUBJECT" | grep -q 'chore(process): sync OpenUP framework'; then
    test_fail "Sync self-commit R2" "Unexpected commit subject: $SC_SUBJECT"
    SC_OK=false
fi
if ! printf '%s' "$SC_SUBJECT" | grep -q '\[openup-skip\]'; then
    test_fail "Sync self-commit R2" "Commit subject missing [openup-skip]: $SC_SUBJECT"
    SC_OK=false
fi
# (R3) the unrelated edit is NOT in the sync commit and survives uncommitted.
if (cd "$SC_DIR" && git show --name-only --pretty=format: HEAD | grep -qx 'src/app.py'); then
    test_fail "Sync self-commit R3" "Unrelated src/app.py was swept into the sync commit"
    SC_OK=false
fi
if [ -z "$(cd "$SC_DIR" && git status --porcelain src/app.py)" ]; then
    test_fail "Sync self-commit R3" "Unrelated src/app.py edit was lost (should stay uncommitted)"
    SC_OK=false
fi
if ! grep -q 'v2-uncommitted' "$SC_DIR/src/app.py"; then
    test_fail "Sync self-commit R3" "src/app.py content was modified by the sync"
    SC_OK=false
fi
if [ "$SC_OK" = true ]; then
    test_pass "Sync commits only the CLIs it wrote; unrelated work untouched"
fi
cd "$PROJECT_ROOT"

# Test 11b: After a sync, on-stop allows a clean stop (T-052 R4).
# Reuses the Test 11 consumer: restore the unrelated edit so the ONLY changes the
# sync made (the committed CLI) remain — the tree is then clean.
test_start "After a sync, on-stop allows a clean stop (T-052 R4)"
(cd "$SC_DIR" && git checkout -q -- src/app.py 2>/dev/null || true)
set +e
echo '{"cwd":"'"$SC_DIR"'"}' | python3 "$PROJECT_ROOT/.claude/scripts/hooks/on-stop.py" >/tmp/openup-test-onstop-clean.out 2>&1
ONSTOP_RC=$?
set -e
if [ "$ONSTOP_RC" -eq 0 ]; then
    test_pass "on-stop exits 0 once the sync committed its own CLI changes"
else
    test_fail "on-stop after sync" "Expected exit 0, got $ONSTOP_RC: $(cat /tmp/openup-test-onstop-clean.out 2>/dev/null)"
fi
cd "$PROJECT_ROOT"

# Test 11c: on-stop still blocks genuinely abandoned (non-sync) CLI edits (T-052 R5).
test_start "on-stop still blocks abandoned non-sync CLI edits (T-052 R5)"
SC3_DIR="/tmp/openup-test-onstop-regress"
rm -rf "$SC3_DIR"
mkdir -p "$SC3_DIR/scripts"
cp "$PROJECT_ROOT/scripts/openup-board.py" "$SC3_DIR/scripts/openup-board.py"
printf '/.claude\n.openup/\n*.bak\n' > "$SC3_DIR/.gitignore"
(
    cd "$SC3_DIR"
    git init -q
    git config user.email "test@openup.local"
    git config user.name "OpenUP Test"
    git add -A
    git commit -q -m "init [openup-skip]"
)
# A real, hand-made (non-sync) edit left uncommitted — must still block.
printf '\n# hand edit, not a sync\n' >> "$SC3_DIR/scripts/openup-board.py"
set +e
echo '{"cwd":"'"$SC3_DIR"'"}' | python3 "$PROJECT_ROOT/.claude/scripts/hooks/on-stop.py" >/tmp/openup-test-onstop-regress.out 2>&1
ONSTOP_RC=$?
set -e
REG_OK=true
if [ "$ONSTOP_RC" -ne 2 ]; then
    test_fail "on-stop regression" "Expected exit 2 (block), got $ONSTOP_RC"
    REG_OK=false
fi
if ! grep -q 'openup-board.py' /tmp/openup-test-onstop-regress.out 2>/dev/null; then
    test_fail "on-stop regression" "Block message did not name the abandoned file"
    REG_OK=false
fi
if [ "$REG_OK" = true ]; then
    test_pass "on-stop blocks (exit 2) and names a non-sync abandoned CLI edit"
fi
cd "$PROJECT_ROOT"

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
