#!/bin/bash
# install-updater.sh — shared helper that ships the OpenUP updater scripts into a
# target project's scripts/ so a bootstrapped project can update itself WITHOUT
# hand-copying sync-from-framework.sh first.
#
# Sibling of install-process-clis.sh: same .bak safeguard, dry-run, and chmod,
# reused by every install/update path (bootstrap-project.sh, setup-agent-teams.sh,
# sync-from-framework.sh, update-from-template.sh). Source this file, then call:
#
#   install_updater <framework_scripts_dir> <target_scripts_dir> [dry_run] [force]
#
#   framework_scripts_dir  directory holding the canonical updater scripts
#   target_scripts_dir     project scripts/ to install into
#   dry_run                "true" prints the plan without writing (default false)
#   force                  "true" overwrites without a .bak (default false)
#
# The list is intentionally tiny and stable, so it lives here rather than in a
# manifest. Writes go through a same-dir temp + atomic rename: this lets the
# running updater refresh its OWN copy safely (the live process keeps the old
# inode; mv swaps in the new one) instead of truncating the script mid-run.

OPENUP_UPDATER_SCRIPTS=(
    "sync-from-framework.sh"
    "update-from-template.sh"
)

install_updater() {
    local src_dir="$1"
    local dest_dir="$2"
    local dry_run="${3:-false}"
    local force="${4:-false}"

    local copied=0 skipped=0 missing=0
    local f src dest
    for f in "${OPENUP_UPDATER_SCRIPTS[@]}"; do
        src="$src_dir/$f"
        dest="$dest_dir/$f"
        if [ ! -f "$src" ]; then
            echo "Warning: updater script missing from framework: $src" >&2
            missing=$((missing + 1))
            continue
        fi
        if [ "$dry_run" = "true" ]; then
            echo "Would install updater: scripts/$f"
            copied=$((copied + 1))
            continue
        fi
        mkdir -p "$dest_dir"
        if [ -f "$dest" ]; then
            if cmp -s "$src" "$dest"; then
                skipped=$((skipped + 1))
                continue
            fi
            if [ "$force" != "true" ]; then
                cp "$dest" "$dest.bak"
            fi
        fi
        # Same-dir temp + atomic rename — safe even when refreshing the running
        # script's own file.
        cp "$src" "$dest.tmp.$$"
        chmod +x "$dest.tmp.$$" 2>/dev/null || true
        mv -f "$dest.tmp.$$" "$dest"
        copied=$((copied + 1))
    done

    if [ "$dry_run" = "true" ]; then
        echo "Updater scripts: $copied would be installed into $dest_dir"
    else
        echo "Updater scripts: $copied installed, $skipped unchanged in $dest_dir"
    fi
    [ "$missing" -eq 0 ]
}
