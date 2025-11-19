#!/usr/bin/env python3
"""
Update README.md with the latest blog posts from amanhimself.dev.
"""

from datetime import datetime
import re

import feedparser

RSS_FEED_URL = "https://amanhimself.dev/rss.xml"
README_PATH = "README.md"
MAX_POSTS = 10

POSTS_START_MARKER = "<!-- BLOG-POSTS:START -->"
POSTS_END_MARKER = "<!-- BLOG-POSTS:END -->"

# RSS feeds can provide dates with numeric offsets or timezone abbreviations (GMT)
RSS_DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S %Z",
]


def fetch_latest_posts(feed_url, max_posts):
    """Fetch the latest posts from the RSS feed and format their dates."""
    feed = feedparser.parse(feed_url)

    if feed.bozo:
        print(f"Warning: RSS parsing issue -> {feed.bozo_exception}")

    posts = []
    for entry in feed.entries[:max_posts]:
        title = entry.get("title", "Untitled")
        link = entry.get("link", "")
        pub_date = entry.get("published", "")

        formatted_date = pub_date or ""
        for fmt in RSS_DATE_FORMATS:
            try:
                date_obj = datetime.strptime(pub_date, fmt)
                formatted_date = date_obj.strftime("%a, %b %d %Y")
                break
            except (ValueError, TypeError):
                continue

        posts.append({"title": title, "link": link, "date": formatted_date})

    return posts


def generate_posts_markdown(posts):
    """Render the posts list between the README markers."""
    lines = [POSTS_START_MARKER]
    if not posts:
        lines.append("- _No posts found_")
    else:
        for post in posts:
            lines.append(f"- [{post['title']}]({post['link']}) - {post['date']}")
    lines.append(POSTS_END_MARKER)
    return "\n".join(lines)


def update_readme_section(content, start_marker, end_marker, new_content):
    pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    return re.sub(pattern, new_content, content, flags=re.DOTALL)


def update_readme(readme_path, posts_md):
    with open(readme_path, "r", encoding="utf-8") as fh:
        content = fh.read()

    content = update_readme_section(content, POSTS_START_MARKER, POSTS_END_MARKER, posts_md)

    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(content)

    print("README updated")


def main():
    print(f"Fetching latest {MAX_POSTS} posts from {RSS_FEED_URL}")
    posts = fetch_latest_posts(RSS_FEED_URL, MAX_POSTS)
    print(f"Found {len(posts)} posts")

    posts_md = generate_posts_markdown(posts)
    update_readme(README_PATH, posts_md)
    print("Done")


if __name__ == "__main__":
    main()

