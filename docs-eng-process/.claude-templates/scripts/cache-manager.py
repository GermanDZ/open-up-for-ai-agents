#!/usr/bin/env python3
"""
Context Cache Manager for OpenUP

This module provides caching functionality for parsed documents to reduce
token usage by avoiding re-reading and re-parsing unchanged files.

Expected token savings: 30-50% per iteration
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ContextCache:
    """
    Cache manager for parsed document data.

    Uses content-based hashing to invalidate cache when files change.
    """

    def __init__(self, cache_dir: str = ".claude/cache", ttl_hours: int = 24):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_file_hash(self, file_path: str) -> str:
        """Generate MD5 hash of file content."""
        try:
            content = Path(file_path).read_text()
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""

    def _get_cache_path(self, file_path: str) -> Path:
        """Generate cache file path based on original file name."""
        # Use filename-based cache to avoid conflicts
        filename = Path(file_path).name
        cache_name = f"{filename}.cache.json"
        return self.cache_dir / cache_name

    def get_cached(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Return cached parsed data if file hasn't changed and cache is valid.

        Args:
            file_path: Path to the original file

        Returns:
            Cached data dict or None if cache miss/invalid
        """
        cache_file = self._get_cache_path(file_path)

        if not cache_file.exists():
            return None

        try:
            cache_data = json.loads(cache_file.read_text())

            # Check if cache is expired
            cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
            if datetime.now() - cached_at > self.ttl:
                return None

            # Check if file has changed
            current_hash = self._get_file_hash(file_path)
            if current_hash != cache_data.get("file_hash"):
                return None

            # Return cached content
            return cache_data.get("content")

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def set_cache(self, file_path: str, data: Dict[str, Any]) -> None:
        """
        Cache parsed data with metadata.

        Args:
            file_path: Path to the original file
            data: Parsed data to cache
        """
        cache_file = self._get_cache_path(file_path)

        cache_data = {
            "file_hash": self._get_file_hash(file_path),
            "cached_at": datetime.now().isoformat(),
            "file_path": str(file_path),
            "content": data
        }

        try:
            cache_file.write_text(json.dumps(cache_data, indent=2))
        except Exception:
            pass  # Fail silently - caching is optional

    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """
        Clear cache for a specific file or all caches.

        Args:
            file_path: Specific file to clear, or None to clear all
        """
        if file_path:
            cache_file = self._get_cache_path(file_path)
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.cache.json"):
                cache_file.unlink()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cache usage.

        Returns:
            Dict with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.cache.json"))

        total_size = sum(f.stat().st_size for f in cache_files)
        valid_count = 0
        expired_count = 0

        for cache_file in cache_files:
            try:
                cache_data = json.loads(cache_file.read_text())
                cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
                if datetime.now() - cached_at > self.ttl:
                    expired_count += 1
                else:
                    valid_count += 1
            except Exception:
                pass

        return {
            "total_entries": len(cache_files),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir)
        }


def main():
    """CLI entry point for cache management."""
    import sys

    cache = ContextCache()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "clear":
            file_path = sys.argv[2] if len(sys.argv) > 2 else None
            cache.clear_cache(file_path)
            print(f"Cache cleared for: {file_path or 'all files'}")

        elif command == "stats":
            stats = cache.get_cache_stats()
            print(json.dumps(stats, indent=2))

        elif command == "get":
            if len(sys.argv) > 2:
                data = cache.get_cached(sys.argv[2])
                if data:
                    print(json.dumps(data, indent=2))
                else:
                    print("Cache miss")

        elif command == "set":
            if len(sys.argv) > 2:
                # Read JSON from stdin
                data = json.loads(sys.stdin.read())
                cache.set_cache(sys.argv[2], data)
                print("Cache set")

        else:
            print("Usage: cache-manager.py {clear|stats|get|set} [args]")
            sys.exit(1)
    else:
        # Default: show stats
        stats = cache.get_cache_stats()
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
