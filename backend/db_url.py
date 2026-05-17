from __future__ import annotations


def normalize_database_url(url: str) -> str:
    """Make provider URLs work with the DB driver installed by this project."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url
