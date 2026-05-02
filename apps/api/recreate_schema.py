"""
Drops and recreates the orchestragrant database with schema derived directly
from SQLAlchemy models (no migration drift).
"""
import asyncio
import os
import sys

# ── 1. Drop & recreate the database using psycopg2 (sync, connect to postgres db)
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_USER = "orchestragrant"
DB_PASS = "localdev"
DB_NAME = "orchestragrant"
DB_HOST = "localhost"
DB_PORT = 5432

print("==> Dropping and recreating database…")
# Try postgres superuser; fall back to orchestragrant user
try:
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname="postgres",
                            user="postgres", password="postgres")
except Exception:
    # If postgres password differs, connect as orchestragrant (needs CREATEDB)
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname="postgres",
                            user=DB_USER, password=DB_PASS)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
# Terminate existing connections
cur.execute(f"""
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid()
""")
cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER} ENCODING 'UTF8'")
cur.close()
conn.close()
print("    Database recreated ✓")

# ── 2. Create schemas, extensions, enums, tables via SQLAlchemy create_all
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Add the api dir to sys.path so models can import properly
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("ENV", "development")
os.environ.setdefault("SECRET_KEY", "recreate-script-placeholder")

# Load .env before importing config
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database import Base
# Import all models to register them with Base.metadata
import models  # noqa: F401

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Extensions
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE EXTENSION IF NOT EXISTS vector;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'pgvector not available';
            END $$
        """))

        # Schemas
        for schema in ("auth", "grants", "applications", "awards", "ai", "discovery"):
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

        # Create all enum types that SQLAlchemy needs (create_all will handle these)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("    Tables created from models ✓")

        # updated_at trigger function
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN NEW.updated_at = now(); RETURN NEW; END;
            $$
        """))

        # Triggers for tables that have updated_at
        triggers = [
            ("organizations", "public"),
            ("grants", "grants"),
            ("funders", "grants"),
            ("applications", "applications"),
            ("application_sections", "applications"),
            ("users", "auth"),
        ]
        for tbl, schema in triggers:
            await conn.execute(text(f"""
                CREATE TRIGGER trg_{tbl}_updated_at
                BEFORE UPDATE ON {schema}.{tbl}
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """))
        print("    Triggers created ✓")

        # Alembic version table + stamp
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))
        await conn.execute(text("DELETE FROM alembic_version"))
        await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001_initial')"))
        print("    Alembic stamped as 0001_initial ✓")

    await engine.dispose()

asyncio.run(main())
print("\n✅ Schema recreation complete. Run seed_admin.py next.")
