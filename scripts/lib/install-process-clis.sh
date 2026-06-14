#!/bin/bash
# install-process-clis.sh — shared helper that ships the OpenUP process CLIs
# (the scripts/openup-*.py runtime the workflow skills invoke) into a target
# project's scripts/ directory.
#
# The list of files to ship is the single source of truth in
# scripts/process-manifest.txt; this helper is the single copy mechanism every
# install/update path reuses. Source this file, then call:
#
#   install_process_clis <framework_scripts_dir> <target_scripts_dir> [dry_run] [force]
#
#   framework_scripts_dir  directory holding the canonical CLIs + manifest
#   target_scripts_dir     project scripts/ to install into
#   dry_run                "true" prints the plan without writing (default false)
#   force                  "true" overwrites without a .bak (default false)
#
# Safeguard: an existing, locally-modified target file is backed up to
# <file>.bak before being overwritten (unless force=true), and dry_run never
# writes — so project-owned edits are never silently lost.

# Print the manifest's CLI filenames (strips #-comments and blank lines).
_process_cli_manifest() {
    local src_dir="$1"
    local manifest="$src_dir/process-manifest.txt"
    [ -f "$manifest" ] || return 0
    sed -e 's/#.*//' "$manifest" | while IFS= read -r line; do
        # Trim surrounding whitespace.
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [ -n "$line" ] && echo "$line"
    done
}

install_process_clis() {
    local src_dir="$1"
    local dest_dir="$2"
    local dry_run="${3:-false}"
    local force="${4:-false}"

    if [ ! -f "$src_dir/process-manifest.txt" ]; then
        echo "Warning: process-manifest.txt not found in $src_dir — no process CLIs shipped" >&2
        return 0
    fi

    local copied=0 skipped=0 missing=0
    local f src dest
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        src="$src_dir/$f"
        dest="$dest_dir/$f"
        if [ ! -f "$src" ]; then
            echo "Warning: process CLI listed in manifest but missing from framework: $src" >&2
            missing=$((missing + 1))
            continue
        fi
        if [ "$dry_run" = "true" ]; then
            echo "Would install process CLI: scripts/$f"
            copied=$((copied + 1))
            continue
        fi
        mkdir -p "$(dirname "$dest")"
        if [ -f "$dest" ]; then
            if cmp -s "$src" "$dest"; then
                skipped=$((skipped + 1))
                continue
            fi
            if [ "$force" != "true" ]; then
                cp "$dest" "$dest.bak"
            fi
        fi
        cp "$src" "$dest"
        case "$f" in
            *.py) chmod +x "$dest" 2>/dev/null || true ;;
        esac
        copied=$((copied + 1))
    done < <(_process_cli_manifest "$src_dir")

    if [ "$dry_run" = "true" ]; then
        echo "Process CLIs: $copied would be installed into $dest_dir"
    else
        echo "Process CLIs: $copied installed, $skipped unchanged in $dest_dir"
    fi
    [ "$missing" -eq 0 ]
}
