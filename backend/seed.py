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


async def seed() -> None:
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await _seed_topics(session)
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


if __name__ == "__main__":
    asyncio.run(seed())
