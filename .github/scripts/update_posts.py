#!/usr/bin/env python3
"""
Update README.md with the latest blog posts from amanhimself.dev and public GitHub activity.
"""

from datetime import datetime, timezone
import os
import re
import feedparser
import requests

RSS_FEED_URL = "https://amanhimself.dev/rss.xml"
README_PATH = "README.md"
MAX_POSTS = 10
MAX_ACTIVITY = 5
GITHUB_USERNAME = "amandeepmittal"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EXCLUDED_REPOS = {"amandeepmittal"}  # avoid showing README repo activity

POSTS_START_MARKER = "<!-- BLOG-POSTS:START -->"
POSTS_END_MARKER = "<!-- BLOG-POSTS:END -->"
ACTIVITY_START_MARKER = "<!-- GITHUB-ACTIVITY:START -->"
ACTIVITY_END_MARKER = "<!-- GITHUB-ACTIVITY:END -->"


def fetch_latest_posts(feed_url, max_posts):
    """Fetch the latest posts from the RSS feed."""
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"Warning: RSS parsing issue -> {feed.bozo_exception}")

    posts = []
    for entry in feed.entries[:max_posts]:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        pub_date = entry.get("published", "")

        try:
            date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            formatted_date = pub_date or ""

        posts.append({"title": title, "link": link, "date": formatted_date})

    return posts


def fetch_github_activity(username, max_items):
    """Fetch recent commits and releases from public repos."""
    try:
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
            print("Using authenticated GitHub requests")

        repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&type=owner&sort=updated"
        repos_response = requests.get(repos_url, headers=headers, timeout=30)
        repos_response.raise_for_status()

        repos = [
            r for r in repos_response.json()
            if not r.get("fork", False) and r.get("name") not in EXCLUDED_REPOS
        ]

        activities = []

        for repo in repos[:20]:
            repo_name = repo["name"]
            repo_url = repo["html_url"]

            commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=3"
            commits_response = requests.get(commits_url, headers=headers, timeout=30)
            if commits_response.status_code == 200:
                for commit in commits_response.json():
                    commit_data = commit.get("commit", {})
                    commit_msg = commit_data.get("message", "").split("\n")[0]
                    commit_date = commit_data.get("author", {}).get("date", "")
                    commit_sha = commit.get("sha", "")[:7]
                    commit_url = commit.get("html_url", "")

                    if not commit_date:
                        continue

                    try:
                        date_obj = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
                        date_obj = date_obj.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                    activities.append({
                        "type": "commit",
                        "repo": repo_name,
                        "repo_url": repo_url,
                        "message": commit_msg,
                        "sha": commit_sha,
                        "url": commit_url,
                        "date": date_obj,
                    })

            releases_url = f"https://api.github.com/repos/{username}/{repo_name}/releases?per_page=3"
            releases_response = requests.get(releases_url, headers=headers, timeout=30)
            if releases_response.status_code == 200:
                for release in releases_response.json():
                    release_name = release.get("name") or release.get("tag_name", "Release")
                    release_date = release.get("published_at", "")
                    release_url = release.get("html_url", "")

                    if not release_date:
                        continue

                    try:
                        date_obj = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%SZ")
                        date_obj = date_obj.replace(tzinfo=timezone.utc)
                    except ValueError:
                        continue

                    activities.append({
                        "type": "release",
                        "repo": repo_name,
                        "repo_url": repo_url,
                        "name": release_name,
                        "url": release_url,
                        "date": date_obj,
                    })

        activities.sort(key=lambda x: x["date"], reverse=True)
        return activities[:max_items]

    except Exception as exc:
        print(f"Error fetching GitHub activity: {exc}")
        return []


def generate_posts_markdown(posts):
    lines = [POSTS_START_MARKER]
    if not posts:
        lines.append("- _No posts found_")
    else:
        for post in posts:
            lines.append(f"- [{post['title']}]({post['link']}) - {post['date']}")
    lines.append(POSTS_END_MARKER)
    return "\n".join(lines)


def generate_activity_markdown(activities):
    lines = [ACTIVITY_START_MARKER]
    if not activities:
        lines.append("- _No recent activity_")
    else:
        for activity in activities:
            formatted_date = activity["date"].strftime("%B %d, %Y")
            if activity["type"] == "commit":
                lines.append(
                    f"- **[{activity['repo']}]({activity['repo_url']})**: "
                    f"[{activity['sha']}]({activity['url']}) - {activity['message']} ({formatted_date})"
                )
            elif activity["type"] == "release":
                lines.append(
                    f"- **[{activity['repo']}]({activity['repo_url']})**: "
                    f"Released [{activity['name']}]({activity['url']}) ({formatted_date})"
                )
    lines.append(ACTIVITY_END_MARKER)
    return "\n".join(lines)


def update_readme_section(content, start_marker, end_marker, new_content):
    pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    return re.sub(pattern, new_content, content, flags=re.DOTALL)


def update_readme(readme_path, posts_md, activity_md):
    with open(readme_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    content = update_readme_section(content, POSTS_START_MARKER, POSTS_END_MARKER, posts_md)
    content = update_readme_section(content, ACTIVITY_START_MARKER, ACTIVITY_END_MARKER, activity_md)

    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print("README updated")


def main():
    print(f"Fetching latest {MAX_POSTS} posts from {RSS_FEED_URL}")
    posts = fetch_latest_posts(RSS_FEED_URL, MAX_POSTS)
    print(f"Found {len(posts)} posts")

    print(f"Fetching GitHub activity for {GITHUB_USERNAME}")
    activity = fetch_github_activity(GITHUB_USERNAME, MAX_ACTIVITY)
    print(f"Found {len(activity)} activity items")

    posts_md = generate_posts_markdown(posts)
    activity_md = generate_activity_markdown(activity)
    update_readme(README_PATH, posts_md, activity_md)
    print("Done")


if __name__ == "__main__":
    main()

