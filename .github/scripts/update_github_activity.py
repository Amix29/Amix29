#!/usr/bin/env python3
"""Update GitHub Activity stats in the profile README."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date
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


def contribution_days(year: int) -> list[tuple[str, bool]]:
    url = (
        f"https://github.com/users/{USERNAME}/contributions"
        f"?from={year}-01-01&to={year}-12-31"
    )

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "github-profile-readme-stats"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")

    matches = re.findall(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="([0-4])"',
        html,
    )

    return [(day, int(level) > 0) for day, level in matches]


def longest_streak() -> int:
    all_days: dict[str, bool] = {}

    # GitHub account created in 2023.
    for year in range(2023, date.today().year + 1):
        for day, active in contribution_days(year):
            all_days[day] = active

    days = sorted(all_days.items())

    longest = 0
    current = 0
    previous = None

    for day_string, active in days:
        current_date = date.fromisoformat(day_string)

        if not active:
            current = 0
            previous = current_date
            continue

        if previous is not None and (current_date - previous).days == 1:
            current += 1
        else:
            current = 1

        longest = max(longest, current)
        previous = current_date

    return longest


def main() -> None:
    streak = longest_streak()
    merged = search_count(f"is:pr is:merged author:{USERNAME}")

    activity = f'''{START}
<table>
  <tr>
    <td width="425" align="center">
      <h2>🔥 {streak}</h2>
      <p>Longest Streak</p>
    </td>
    <td width="425" align="center">
      <h2>✅ {merged}</h2>
      <p>Pull Requests merged</p>
    </td>
  </tr>
</table>
{END}'''

    text = README.read_text(encoding="utf-8")

    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )

    if not pattern.search(text):
        raise RuntimeError(
            "GitHub Activity markers were not found in README.md"
        )

    updated = pattern.sub(activity, text, count=1)

    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f"Updated: {streak}-day longest streak, {merged} merged PRs")
    else:
        print(f"Already current: {streak}-day longest streak, {merged} merged PRs")


if __name__ == "__main__":
    main()
