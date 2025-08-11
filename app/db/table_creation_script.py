# app/db/table_creation_script.py
import asyncpg

import os
import re

from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL  # Use sync URL like: postgresql://...


def table_exists(cursor, table_name):
    cursor.execute(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);",
        (table_name,),
    )
    return cursor.fetchone()[0]


def extract_version(filename):
    # Use regex to find the numeric part of the filename
    match = re.search(r"V(\d+)", filename)
    return (
        int(match.group(1)) if match else float("inf")
    )  # Return a large number if no match


DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+asyncpg", "postgresql"
)  # required for asyncpg


async def table_exists(conn, table_name: str) -> bool:
    result = await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = $1
        );
    """,
        table_name,
    )
    return result


def extract_version(filename):
    match = re.search(r"V(\d+)", filename)
    return int(match.group(1)) if match else float("inf")


async def execute_sql_files():
    conn = await asyncpg.connect(DATABASE_URL)

    # Ensure the migrations table exists
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            file_name VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    )

    # Get list of already executed files
    rows = await conn.fetch("SELECT file_name FROM migrations;")
    executed_files = {row["file_name"] for row in rows}

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")

    if not os.path.exists(DATABASE_DIR):
        raise FileNotFoundError(f"Database directory not found: {DATABASE_DIR}")

    sql_files = sorted(os.listdir(DATABASE_DIR), key=extract_version)

    for file_name in sql_files:
        if file_name in executed_files:
            continue

        file_path = os.path.join(DATABASE_DIR, file_name)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        with open(file_path, "r") as f:
            sql = f.read()

        first_line = sql.strip().split("\n")[0].strip().lower()
        if first_line.startswith("create table"):
            table_name = first_line.split(" ")[2]
            table_name = table_name.replace("if not exists", "").strip("();")
            if await table_exists(conn, table_name):
                print(f"Skipping {file_name}: Table {table_name} already exists.")
                continue

        print(f"Executing: {file_name}")
        await conn.execute(sql)
        await conn.execute("INSERT INTO migrations (file_name) VALUES ($1);", file_name)
        print(f"Executed: {file_name}")

    await conn.close()
