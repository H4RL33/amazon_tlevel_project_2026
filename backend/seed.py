"""
Idempotent seed script. Run via:
  poetry run python seed.py

Uses ON CONFLICT DO NOTHING for topics (slug is unique) and
WHERE NOT EXISTS for t_levels (no unique constraint on name).
Designed to be invoked as a one-off ECS task in production.
"""

import asyncio
import sys
from datetime import datetime

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
    # ── Getting Started ──────────────────────────────────────────────────────
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
        "title": "Cloud Service Models: IaaS, PaaS, SaaS",
        "body": "Infrastructure as a Service (IaaS) rents raw virtual machines "
        "and networking. Platform as a Service (PaaS) goes further, managing "
        "the operating system and runtime so you just deploy code. Software "
        "as a Service (SaaS) hands you a finished application — think Gmail "
        "or Netflix — with nothing to install or manage at all.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Public, Private, and Hybrid Cloud",
        "body": "A public cloud (like AWS or Azure) shares physical hardware "
        "between many customers, kept isolated from each other. A private "
        "cloud is dedicated to one organisation, often for stricter compliance "
        "needs. A hybrid cloud combines both, letting a business keep "
        "sensitive workloads private while bursting into public cloud "
        "capacity when demand spikes.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    # ── Compute & Virtualisation ──────────────────────────────────────────────
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
        "title": "Servers vs Serverless",
        "body": "Traditional servers run continuously and you pay for them "
        "whether or not they're handling requests. Serverless computing runs "
        "your code only when triggered, and you pay only for the compute time "
        "actually used.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Containers and Docker Basics",
        "body": "A container packages an application together with everything "
        "it needs to run — code, libraries, settings — so it behaves "
        "identically on any machine. Docker is the most widely used tool for "
        "building and running containers, and container orchestrators like "
        "Kubernetes or AWS ECS manage many containers running across a "
        "cluster of servers.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Understanding Auto Scaling",
        "body": "Auto scaling automatically adds or removes compute capacity "
        "to match demand. If traffic spikes, more instances launch to share "
        "the load; when traffic drops, idle instances are terminated to save "
        "cost. This is one of the main reasons cloud computing can be cheaper "
        "than buying fixed hardware for peak demand you rarely hit.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    # ── Networking & Security ─────────────────────────────────────────────────
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
        "title": "How DNS Works",
        "body": "The Domain Name System (DNS) translates human-readable "
        "domain names like example.com into the numeric IP addresses "
        "computers actually use to find each other. Without it, you'd have "
        "to remember a string of numbers for every website you wanted to "
        "visit.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Load Balancers Explained",
        "body": "A load balancer sits in front of a group of servers and "
        "distributes incoming requests across them, so no single server gets "
        "overwhelmed. It also detects unhealthy servers and stops sending "
        "them traffic, which is a major reason cloud applications can stay "
        "online even when individual servers fail.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Cloud Security Fundamentals",
        "body": "Cloud providers secure the physical infrastructure, but "
        "customers are responsible for securing what they build on top of "
        "it — this split is called the 'shared responsibility model'. Common "
        "practices include encrypting data, tightly scoping permissions so "
        "accounts can only access what they need, and never exposing "
        "databases directly to the public internet.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    # ── Storage & Databases ───────────────────────────────────────────────────
    {
        "title": "Object Storage vs Block Storage",
        "body": "Block storage splits data into fixed-size chunks and is "
        "typically attached to a single virtual machine, much like a hard "
        "drive. Object storage (like Amazon S3) stores whole files as "
        "objects with metadata, accessible over the internet from anywhere, "
        "and is what most cloud applications use for images, videos, and "
        "backups.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Relational vs NoSQL Databases",
        "body": "Relational databases (like PostgreSQL) store data in tables "
        "with strict, predefined relationships between them, enforced by a "
        "schema. NoSQL databases trade some of that structure for "
        "flexibility and scale, storing data as documents, key-value pairs, "
        "or graphs instead — useful when your data doesn't fit neatly into "
        "rows and columns.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "Data Backups and Disaster Recovery",
        "body": "A backup is a copy of your data kept somewhere separate, so "
        "it can be restored if the original is lost or corrupted. Disaster "
        "recovery goes further, planning for how an entire service recovers "
        "from a major outage — for example, automatically failing over to a "
        "backup region in a different part of the world.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    # ── Careers in Cloud Computing ─────────────────────────────────────────────
    {
        "title": "Day in the Life of a Cloud Engineer",
        "body": "A cloud engineer designs, builds, and maintains the "
        "infrastructure applications run on. A typical day might involve "
        "writing infrastructure-as-code to provision new resources, "
        "investigating why a service is running slowly, and reviewing "
        "security permissions before a new feature goes live.",
        "content_type": "article",
        "topic_slug": "digital-infrastructure",
    },
    {
        "title": "AWS, Azure, and Google Cloud: An Overview",
        "body": "Amazon Web Services (AWS), Microsoft Azure, and Google Cloud "
        "Platform (GCP) are the three largest cloud providers, each offering "
        "broadly similar services — compute, storage, databases, "
        "networking — under different names and pricing. Most cloud "
        "engineering roles specialise in one provider, though the underlying "
        "concepts transfer well between them.",
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
            "snippet_titles": [
                "What is Cloud Computing?",
                "Cloud Service Models: IaaS, PaaS, SaaS",
                "Public, Private, and Hybrid Cloud",
            ],
        },
        {
            "title": "Compute & Virtualisation",
            "snippet_titles": [
                "Virtual Private Servers Explained",
                "Servers vs Serverless",
                "Containers and Docker Basics",
                "Understanding Auto Scaling",
            ],
        },
        {
            "title": "Networking & Security",
            "snippet_titles": [
                "Intro to Virtual Private Networks",
                "How DNS Works",
                "Load Balancers Explained",
                "Cloud Security Fundamentals",
            ],
        },
        {
            "title": "Storage & Databases",
            "snippet_titles": [
                "Object Storage vs Block Storage",
                "Relational vs NoSQL Databases",
                "Data Backups and Disaster Recovery",
            ],
        },
        {
            "title": "Careers in Cloud Computing",
            "snippet_titles": [
                "Day in the Life of a Cloud Engineer",
                "AWS, Azure, and Google Cloud: An Overview",
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
            result = await session.execute(
                text("SELECT 1 FROM t_levels WHERE topic_id = :topic_id AND name = :name"),
                {"topic_id": topic_id, "name": tl["name"]},
            )
            if result.scalar_one_or_none() is None:
                await session.execute(
                    text("""
                        INSERT INTO t_levels (topic_id, name, entry_requirements, how_to_apply)
                        VALUES (:topic_id, :name, :entry_requirements, :how_to_apply)
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

    # Sides/SideContent are upserted individually so re-running this script
    # against a DB that already has this Album adds newly-introduced Sides
    # and Snippets instead of silently skipping them.
    for position, side in enumerate(ALBUM["sides"]):
        result = await session.execute(
            text("SELECT id FROM sides WHERE album_id = :album_id AND title = :title"),
            {"album_id": album_id, "title": side["title"]},
        )
        side_id = result.scalar_one_or_none()

        if side_id is None:
            await session.execute(
                text("""
                    INSERT INTO sides (album_id, title, position)
                    VALUES (:album_id, :title, :position)
                """),
                {"album_id": album_id, "title": side["title"], "position": position},
            )
            await session.flush()

            result = await session.execute(
                text("SELECT id FROM sides WHERE album_id = :album_id AND title = :title"),
                {"album_id": album_id, "title": side["title"]},
            )
            side_id = result.scalar_one()

        for snippet_position, title in enumerate(side["snippet_titles"]):
            result = await session.execute(
                text(
                    "SELECT 1 FROM side_content WHERE side_id = :side_id AND content_id = :content_id"
                ),
                {"side_id": side_id, "content_id": content_ids[title]},
            )
            if result.scalar_one_or_none() is None:
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


async def embed_content() -> None:
    settings = get_settings()
    if settings.SKIP_EMBEDDINGS:
        print("SKIP_EMBEDDINGS=true, skipping embedding phase.")
        return

    from app.services.embedding_service import embed_text

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(
            text("SELECT id, title, body FROM content WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} snippet(s)...")
        for row in rows:
            input_text = f"{row.title}\n\n{row.body or ''}"
            vec = embed_text(input_text)
            await session.execute(
                text(
                    "UPDATE content SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.utcnow(), "id": row.id},
            )
        await session.commit()
        print("Snippets embedded.")

        result = await session.execute(
            text("SELECT id, title, description FROM albums WHERE embedding_generated_at IS NULL")
        )
        rows = result.fetchall()
        print(f"Embedding {len(rows)} album(s)...")
        for row in rows:
            input_text = f"{row.title}\n\n{row.description}"
            vec = embed_text(input_text)
            await session.execute(
                text(
                    "UPDATE albums SET embedding = :vec, embedding_generated_at = :now "
                    "WHERE id = :id"
                ),
                {"vec": str(vec), "now": datetime.utcnow(), "id": row.id},
            )
        await session.commit()
        print("Albums embedded.")

    await engine.dispose()


if __name__ == "__main__":
    if "--embed-only" in sys.argv:
        asyncio.run(embed_content())
    else:
        asyncio.run(seed())
        asyncio.run(embed_content())
