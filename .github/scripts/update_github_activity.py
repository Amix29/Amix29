#!/usr/bin/env python3
"""Update the GitHub Activity numbers in the profile README."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_STATS_USER", "Amix29")
README = Path(os.environ.get("README_PATH", "README.md"))
TOKEN = os.environ.get("GITHUB_TOKEN", "")

START = "<!-- GITHUB_ACTIVITY:START -->"
END = "<!-- GITHUB_ACTIVITY:END -->"


def search_count(query: str) -> int:
    params = urllib.parse.urlencode({"q": query, "per_page": 1})
    request = urllib.request.Request(
        f"https://api.github.com/search/issues?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "github-profile-readme-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return int(payload["total_count"])


def main() -> None:
    opened = search_count(f"is:pr author:{USERNAME}")
    merged = search_count(f"is:pr is:merged author:{USERNAME}")

    activity = f'''{START}
<table>
  <tr>
    <td width="425" align="center">
      <h2>🔀 {opened}</h2>
      <p>Pull Requests opened</p>
    </td>
    <td width="425" align="center">
      <h2>✅ {merged}</h2>
      <p>Pull Requests merged</p>
    </td>
  </tr>
</table>
{END}'''

    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError("GitHub Activity markers were not found in README.md")

    updated = pattern.sub(activity, text, count=1)
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated: {opened} opened, {merged} merged")
    else:
        print(f"Already current: {opened} opened, {merged} merged")


if __name__ == "__main__":
    main()
