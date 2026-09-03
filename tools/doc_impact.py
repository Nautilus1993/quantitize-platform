#!/usr/bin/env python3
"""Report documentation domains affected by a Git diff without scanning prose."""

from __future__ import annotations

import argparse
import fnmatch
import subprocess


RULES = [
    (("pipeline/**",), ("performance",), ("pipeline/FLOW.md", "docs/reference/PERFORMANCE.md")),
    (("apps/api/**",), ("production", "runtime"), ("docs/agent/RUNBOOK.md",)),
    (("deploy/**",), ("production", "runtime", "hardware"), ("deploy/README.md", "docs/reference/RECOVERY.md")),
    (("rebuild/**",), ("runtime",), ("rebuild/REBUILD_GUIDE.md",)),
    (("docs/reference/RECOVERY.md",), ("storage",), ("docs/reference/RECOVERY.md",)),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD", help="diff base; default includes uncommitted changes")
    args = parser.parse_args()
    result = subprocess.run(
        ["git", "diff", "--name-only", args.base],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    paths = sorted(
        set(line for line in result.stdout.splitlines() if line)
        | set(line for line in untracked.stdout.splitlines() if line)
    )
    domains: set[str] = set()
    reads: set[str] = set()
    matched: set[str] = set()
    for path in paths:
        for patterns, rule_domains, rule_reads in RULES:
            if any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
                matched.add(path)
                domains.update(rule_domains)
                reads.update(rule_reads)
    print("changed paths:")
    for path in paths:
        print(f"  - {path}")
    print("state domains to review:")
    for domain in sorted(domains):
        print(f"  - {domain}")
    print("task-specific documents to read:")
    for path in sorted(reads):
        print(f"  - {path}")
    unmatched = sorted(set(paths) - matched)
    if unmatched:
        print("no mapped runtime domain:")
        for path in unmatched:
            print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
