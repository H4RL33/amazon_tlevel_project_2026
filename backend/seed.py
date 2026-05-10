"""
Seed script — populates Topics, TLevels, Tags, and Content from source data.

Run from the backend/ directory:
    python seed.py

Prerequisites:
    - DATABASE_URL must point to a running Postgres instance
    - Run after `alembic upgrade head` (or equivalent table creation)

Structure:
    - Topics and TLevels are hardcoded below — edit this file to change them.
    - Content items should be added as entries in CONTENT_ITEMS below.
      Set body to a Markdown string for articles; set media_url to an S3 key
      for audio/video.

TODO (implement this script):
    1. Create an async engine from DATABASE_URL
    2. For each entry in TOPICS: upsert a Topic row (insert or update by slug)
    3. For each entry in T_LEVELS: upsert a TLevel row
    4. For each entry in TAGS: upsert a Tag row
    5. For each entry in CONTENT_ITEMS: upsert a Content row and its ContentTag rows
    6. Commit and print a summary
"""

import asyncio

TOPICS = [
    {"slug": "digital", "name": "Digital", "description": "# Digital\n\nTODO", "accent_colour": "#3b82f6"},
    {"slug": "business", "name": "Business", "description": "# Business\n\nTODO", "accent_colour": "#10b981"},
    {"slug": "media", "name": "Media", "description": "# Media\n\nTODO", "accent_colour": "#f59e0b"},
    {"slug": "finance", "name": "Finance", "description": "# Finance\n\nTODO", "accent_colour": "#6366f1"},
    {"slug": "engineering", "name": "Engineering", "description": "# Engineering\n\nTODO", "accent_colour": "#ef4444"},
]

T_LEVELS: list[dict] = [
    # {"topic_slug": "digital", "name": "...", "entry_requirements": "...", "how_to_apply": "..."},
]

TAGS: list[dict] = [
    # {"name": "cloud"},
    # {"name": "networking"},
]

CONTENT_ITEMS: list[dict] = [
    # {
    #     "title": "Introduction to Cloud Computing",
    #     "body": "# Introduction\n\nTODO",
    #     "content_type": "article",
    #     "media_url": None,
    #     "topic_slug": "digital",
    #     "t_level_name": None,
    #     "tags": ["cloud"],
    # },
]


async def main() -> None:
    # TODO: implement seed logic (see module docstring)
    raise NotImplementedError("Implement seed.py before running")


if __name__ == "__main__":
    asyncio.run(main())
