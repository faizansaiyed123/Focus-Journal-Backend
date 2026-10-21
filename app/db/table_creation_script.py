import re
from pathlib import Path

import asyncpg

from core.config import settings

DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://",
    "postgresql://",
)


def extract_version(filename: str) -> int:
    match = re.match(r"^[vV](\d+)", filename)
    return int(match.group(1)) if match else 2**31 - 1


async def execute_sql_files() -> None:
    database_dir = Path(__file__).resolve().parent.parent / "database"
    if not database_dir.is_dir():
        raise FileNotFoundError(f"Database migration directory not found: {database_dir}")

    sql_files = sorted(
        (
            path for path in database_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".sql"
        ),
        key=lambda path: (extract_version(path.name), path.name.lower()),
    )

    conn = await asyncpg.connect(DATABASE_URL, timeout=10)
    try:
        await conn.fetchval("SELECT pg_advisory_lock(734821609)")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                file_name VARCHAR(255) NOT NULL UNIQUE,
                executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        rows = await conn.fetch("SELECT file_name FROM migrations")
        executed_files = {row["file_name"] for row in rows}

        for migration_path in sql_files:
            if migration_path.name in executed_files:
                continue

            sql = migration_path.read_text(encoding="utf-8").strip()
            if not sql:
                continue

            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO migrations (file_name) VALUES ($1)",
                    migration_path.name,
                )
    finally:
        await conn.close()
