#!/usr/bin/env python3
"""
Token Usage Tracker for OpenUP

Tracks token usage per skill, tier, and operation to provide visibility
into consumption patterns and identify optimization opportunities.

Usage data is stored in .claude/token-usage.jsonl
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict


class TokenTracker:
    """Track and analyze token usage for OpenUP operations."""

    def __init__(self, log_file: str = ".claude/token-usage.jsonl"):
        """
        Initialize token tracker.

        Args:
            log_file: Path to the usage log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_usage(
        self,
        skill: str,
        tokens_in: int,
        tokens_out: int,
        tier: str = "standard",
        operation: str = "run",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log token usage for a skill operation.

        Args:
            skill: Name of the skill being run
            tokens_in: Input tokens consumed
            tokens_out: Output tokens generated
            tier: Context tier used (minimal, standard, full)
            operation: Type of operation (run, init, complete, etc.)
            metadata: Additional context (task_id, phase, etc.)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill,
            "tokens": {
                "in": tokens_in,
                "out": tokens_out,
                "total": tokens_in + tokens_out
            },
            "tier": tier,
            "operation": operation,
            "metadata": metadata or {}
        }

        # Append to log file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def get_usage_stats(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get usage statistics from the log.

        Args:
            limit: Maximum number of entries to analyze

        Returns:
            Dict with usage statistics
        """
        if not self.log_file.exists():
            return {"error": "No usage data found"}

        entries = []
        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        entries = entries[-limit:]  # Last N entries

        if not entries:
            return {"error": "No valid usage entries"}

        # Calculate statistics
        stats = {
            "total_entries": len(entries),
            "total_tokens": 0,
            "by_skill": defaultdict(lambda: {"count": 0, "tokens": 0}),
            "by_tier": defaultdict(lambda: {"count": 0, "tokens": 0}),
            "average_tokens": 0,
            "min_tokens": float("inf"),
            "max_tokens": 0,
            "recent_entries": entries[-5:]
        }

        for entry in entries:
            tokens = entry["tokens"]["total"]
            stats["total_tokens"] += tokens
            stats["by_skill"][entry["skill"]]["count"] += 1
            stats["by_skill"][entry["skill"]]["tokens"] += tokens
            stats["by_tier"][entry["tier"]]["count"] += 1
            stats["by_tier"][entry["tier"]]["tokens"] += tokens
            stats["min_tokens"] = min(stats["min_tokens"], tokens)
            stats["max_tokens"] = max(stats["max_tokens"], tokens)

        stats["average_tokens"] = stats["total_tokens"] / len(entries)

        # Convert defaultdicts to regular dicts
        stats["by_skill"] = dict(stats["by_skill"])
        stats["by_tier"] = dict(stats["by_tier"])

        return stats

    def get_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Calculate efficiency metrics comparing tiers.

        Returns:
            Dict with efficiency comparisons
        """
        stats = self.get_usage_stats()
        if "error" in stats:
            return stats

        efficiency = {
            "tier_comparison": {},
            "most_expensive_skills": [],
            "recommendations": []
        }

        # Compare tiers
        for tier, data in stats["by_tier"].items():
            if data["count"] > 0:
                efficiency["tier_comparison"][tier] = {
                    "avg_tokens": data["tokens"] / data["count"],
                    "total_tokens": data["tokens"],
                    "usage_count": data["count"]
                }

        # Most expensive skills
        skill_costs = [
            (skill, data["tokens"] / data["count"])
            for skill, data in stats["by_skill"].items()
        ]
        skill_costs.sort(key=lambda x: x[1], reverse=True)
        efficiency["most_expensive_skills"] = [
            {"skill": skill, "avg_tokens": tokens}
            for skill, tokens in skill_costs[:5]
        ]

        # Recommendations
        if stats["average_tokens"] > 8000:
            efficiency["recommendations"].append(
                "High average token usage. Consider using minimal tier for quick tasks."
            )
        if "minimal" not in stats["by_tier"]:
            efficiency["recommendations"].append(
                "No minimal tier usage detected. Use quick-task for small changes."
            )
        if stats["total_tokens"] > 50000:
            efficiency["recommendations"].append(
                "High total usage. Consider enabling caching with batch-context.py"
            )

        return efficiency

    def clear_logs(self) -> None:
        """Clear all usage logs."""
        if self.log_file.exists():
            self.log_file.unlink()

    def export_summary(self, output_file: str = None) -> str:
        """
        Export a summary of usage statistics.

        Args:
            output_file: Optional file to write summary to

        Returns:
            JSON string of summary
        """
        stats = self.get_usage_stats()
        efficiency = self.get_efficiency_metrics()

        summary = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "efficiency": efficiency
        }

        json_str = json.dumps(summary, indent=2)

        if output_file:
            Path(output_file).write_text(json_str)

        return json_str


def main():
    """CLI entry point for token tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Track OpenUP token usage")
    parser.add_argument("command", choices=["log", "stats", "efficiency", "clear", "export"],
                       help="Command to run")
    parser.add_argument("--skill", help="Skill name (for log command)")
    parser.add_argument("--tokens-in", type=int, help="Input tokens (for log command)")
    parser.add_argument("--tokens-out", type=int, help="Output tokens (for log command)")
    parser.add_argument("--tier", default="standard", help="Context tier (for log command)")
    parser.add_argument("--operation", default="run", help="Operation type (for log command)")
    parser.add_argument("--output", help="Output file (for export command)")

    args = parser.parse_args()

    tracker = TokenTracker()

    if args.command == "log":
        if not args.skill or args.tokens_in is None or args.tokens_out is None:
            print("Error: log command requires --skill, --tokens-in, and --tokens-out")
            sys.exit(1)

        tracker.log_usage(
            skill=args.skill,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
            tier=args.tier,
            operation=args.operation
        )
        print(f"Logged usage for {args.skill}")

    elif args.command == "stats":
        stats = tracker.get_usage_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "efficiency":
        efficiency = tracker.get_efficiency_metrics()
        print(json.dumps(efficiency, indent=2))

    elif args.command == "clear":
        tracker.clear_logs()
        print("Usage logs cleared")

    elif args.command == "export":
        summary = tracker.export_summary(args.output)
        print(summary)


if __name__ == "__main__":
    main()
