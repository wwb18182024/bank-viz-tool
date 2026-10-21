"""Create GitLab issues from the markdown files in docs/issues/.

Usage:
  1. Generate a Personal Access Token on your GitLab (scopes: api).
     GitLab -> User Settings -> Access Tokens.
  2. Set environment variables:
       GITLAB_URL    (default: https://stgit.dcs.gla.ac.uk)
       GITLAB_PROJECT  e.g. msc-project-for-information-technology/2025/it-project-XXXXXXX/XXXXXXX-development-project
       GITLAB_TOKEN  your token
  3. Run:  python scripts/create_issues.py

Each file's YAML front-matter provides the title and labels; the body is the description.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ISSUES_DIR = Path(__file__).resolve().parent.parent / "docs" / "issues"
BASE_URL = os.environ.get("GITLAB_URL", "https://stgit.dcs.gla.ac.uk").rstrip("/")
PROJECT_PATH = os.environ.get("GITLAB_PROJECT", "")
TOKEN = os.environ.get("GITLAB_TOKEN", "")


def parse_issue_file(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError(f"No front-matter in {path.name}")
    fm, body = m.group(1), m.group(2)
    title = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE).group(1)
    labels_m = re.search(r'^labels:\s*(.+)$', fm, re.MULTILINE)
    labels = [l.strip() for l in labels_m.group(1).split(",")] if labels_m else []
    return title, labels, body.strip()


def api_call(url: str, data: dict):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"PRIVATE-TOKEN": TOKEN, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    if not PROJECT_PATH or not TOKEN:
        sys.exit("Please set GITLAB_PROJECT and GITLAB_TOKEN environment variables first (see the file header comments).")
    project_id = urllib.parse.quote(PROJECT_PATH, safe="")
    endpoint = f"{BASE_URL}/api/v4/projects/{project_id}/issues"
    files = sorted(ISSUES_DIR.glob("*.md"))
    if not files:
        sys.exit(f"No markdown files found in {ISSUES_DIR}")
    for f in files:
        title, labels, body = parse_issue_file(f)
        payload = {
            "title": title,
            "description": body,
            "labels": ",".join(labels),
        }
        try:
            issue = api_call(endpoint, payload)
            print(f"[OK]   #{issue['iid']} {title}")
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {title}: {exc}")


if __name__ == "__main__":
    main()
