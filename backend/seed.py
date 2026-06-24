"""
Idempotent seed script. Run via:
  poetry run python seed.py

Uses ON CONFLICT DO NOTHING for topics (slug is unique) and
WHERE NOT EXISTS for t_levels (no unique constraint on name).
Designed to be invoked as a one-off ECS task in production.
"""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

TOPICS = [
    {
        "slug": "digital-production-design-development",
        "name": "Digital Production, Design and Development",
        "description": "Learn to design, build, and test digital products including software, systems, and services.",
        "accent_colour": "#0066CC",
        "t_levels": [
            {
                "name": "Digital Production, Design and Development",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-business-services",
        "name": "Digital Business Services",
        "description": "Understand how digital tools and services support modern business operations.",
        "accent_colour": "#00994C",
        "t_levels": [
            {
                "name": "Digital Business Services",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "digital-infrastructure",
        "name": "Digital Infrastructure",
        "description": "Explore the networks, cloud platforms, and systems that underpin digital services.",
        "accent_colour": "#CC3300",
        "t_levels": [
            {
                "name": "Digital Infrastructure",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English and maths.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "design-surveying-planning",
        "name": "Design, Surveying and Planning",
        "description": "Discover careers in built environment design, including architecture and civil engineering.",
        "accent_colour": "#996600",
        "t_levels": [
            {
                "name": "Design, Surveying and Planning for Construction",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and ideally a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            }
        ],
    },
    {
        "slug": "health",
        "name": "Health",
        "description": "Prepare for a career in healthcare, covering clinical environments and patient support.",
        "accent_colour": "#660099",
        "t_levels": [
            {
                "name": "Health (Nursing)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
            {
                "name": "Health (Midwifery)",
                "entry_requirements": "4 or 5 GCSEs at grade 4 or above, including English, maths, and a science.",
                "how_to_apply": "Apply through your school or college sixth form, or a local T-Level provider.",
            },
        ],
    },
]


SNIPPETS = [
    {
        "title": "What is Cloud Computing?",
        "body": "Cloud computing means renting computing power, storage, and "
        "services over the internet instead of buying and running your own "
        "physical servers. Providers like AWS offer this on demand, billed by "
        "usage, so you can scale up or down as your needs change.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Virtual Private Servers Explained",
        "body": "A Virtual Private Server (VPS) is a virtual machine sold as a "
        "service by a hosting provider. It behaves like a dedicated physical "
        "server but is actually a partitioned slice of a larger physical "
        "machine, shared with other VPS instances.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Intro to Virtual Private Networks",
        "body": "A Virtual Private Network (VLAN) logically separates devices "
        "on the same physical network into distinct broadcast domains, "
        "improving security and organisation without needing separate "
        "physical switches for each group.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Servers vs Serverless",
        "body": "Traditional servers run continuously and you pay for them "
        "whether or not they're handling requests. Serverless computing runs "
        "your code only when triggered, and you pay only for the compute time "
        "actually used.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
]

ALBUM = {
    "title": "Cloud Computing Fundamentals",
    "description": "An introduction to cloud computing, virtualisation, and "
    "the infrastructure that powers modern digital services.",
    "icon": "cloud",
    "t_level_topic_slug": "digital-infrastructure",
    "sides": [
        {
            "title": "Getting Started",
            "snippet_titles": ["What is Cloud Computing?", "Servers vs Serverless"],
        },
        {
            "title": "Networking Basics",
            "snippet_titles": [
                "Virtual Private Servers Explained",
                "Intro to Virtual Private Networks",
            ],
        },
    ],
}


async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
        await _seed_album(session)
    await engine.dispose()
    print("Seed complete.")


async def _seed_topics(session: AsyncSession) -> None:
    for topic_data in TOPICS:
        t_levels = topic_data["t_levels"]
        topic_params = {k: v for k, v in topic_data.items() if k != "t_levels"}

        await session.execute(
            text("""
                INSERT INTO topics (slug, name, description, accent_colour)
                VALUES (:slug, :name, :description, :accent_colour)
                ON CONFLICT (slug) DO NOTHING
            """),
            topic_params,
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM topics WHERE slug = :slug"),
            {"slug": topic_data["slug"]},
        )
        topic_id = result.scalar_one()

        for tl in t_levels:
            await session.execute(
                text("""
                    INSERT INTO t_levels (topic_id, name, entry_requirements, how_to_apply)
                    SELECT :topic_id, :name, :entry_requirements, :how_to_apply
                    WHERE NOT EXISTS (
                        SELECT 1 FROM t_levels WHERE topic_id = :topic_id AND name = :name
                    )
                """),
                {**tl, "topic_id": topic_id},
            )

    await session.commit()


async def _seed_album(session: AsyncSession) -> None:
    result = await session.execute(
        text(
            "SELECT id FROM t_levels WHERE topic_id = (SELECT id FROM topics WHERE slug = :slug) LIMIT 1"
        ),
        {"slug": ALBUM["t_level_topic_slug"]},
    )
    t_level_id = result.scalar_one()

    content_ids: dict[str, int] = {}
    for snippet in SNIPPETS:
        result = await session.execute(
            text("SELECT id FROM topics WHERE slug = :slug"),
            {"slug": snippet["topic_slug"]},
        )
        topic_id = result.scalar_one()

        result = await session.execute(
            text("SELECT id FROM content WHERE title = :title"),
            {"title": snippet["title"]},
        )
        existing_content_id = result.scalar_one_or_none()

        if existing_content_id is None:
            await session.execute(
                text("""
                    INSERT INTO content (title, body, content_type, topic_id)
                    VALUES (:title, :body, :content_type, :topic_id)
                """),
                {
                    "title": snippet["title"],
                    "body": snippet["body"],
                    "content_type": snippet["content_type"],
                    "topic_id": topic_id,
                },
            )
            await session.flush()

        result = await session.execute(
            text("SELECT id FROM content WHERE title = :title"),
            {"title": snippet["title"]},
        )
        content_ids[snippet["title"]] = result.scalar_one()

    result = await session.execute(
        text("SELECT id FROM albums WHERE title = :title"),
        {"title": ALBUM["title"]},
    )
    album_id = result.scalar_one_or_none()

    if album_id is None:
        await session.execute(
            text("""
                INSERT INTO albums (title, description, icon, t_level_id)
                VALUES (:title, :description, :icon, :t_level_id)
            """),
            {
                "title": ALBUM["title"],
                "description": ALBUM["description"],
                "icon": ALBUM["icon"],
                "t_level_id": t_level_id,
            },
        )
        await session.flush()

        result = await session.execute(
            text("SELECT id FROM albums WHERE title = :title"),
            {"title": ALBUM["title"]},
        )
        album_id = result.scalar_one()

        for position, side in enumerate(ALBUM["sides"]):
            await session.execute(
                text("""
                    INSERT INTO sides (album_id, title, position)
                    VALUES (:album_id, :title, :position)
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            await session.flush()

            result = await session.execute(
                text("""
                    SELECT id FROM sides
                    WHERE album_id = :album_id AND title = :title AND position = :position
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            side_id = result.scalar_one()

            for snippet_position, title in enumerate(side["snippet_titles"]):
                await session.execute(
                    text("""
                        INSERT INTO side_content (side_id, content_id, position)
                        VALUES (:side_id, :content_id, :position)
                    """),
                    {
                        "side_id": side_id,
                        "content_id": content_ids[title],
                        "position": snippet_position,
                    },
                )

    await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
