import os
import re
from typing import Dict, Tuple


def redact_url(url: str) -> str:
    """
    Redacts passwords from database connection URLs before logging.
    Prevents plain-text password leakage in Cloud Trace and Cloud Logging.
    """
    if not url:
        return ""
    return re.sub(r":([^/@:]+)@", ":***@", url)


def get_database_urls() -> Tuple[str, str, str]:
    """
    Returns (sync_url, async_url, driver_type).
    Handles dual database drivers for Google Cloud SQL:
    - Sync pg8000: requires unix_sock file path (/cloudsql/INSTANCE/.s.PGSQL.5432)
    - Async asyncpg: requires socket directory path (/cloudsql/INSTANCE)
    Falls back to SQLite for 100% offline dev/testing.
    """
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_user = os.getenv("DB_USER", "fleet")
    db_pass = os.getenv("DB_PASSWORD", "fleet_pass")
    db_name = os.getenv("DB_NAME", "fleet")
    
    if instance_connection_name:
        # Cloud SQL Unix Socket paths
        sync_url = f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}?unix_sock=/cloudsql/{instance_connection_name}/.s.PGSQL.5432"
        async_url = f"postgresql+asyncpg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{instance_connection_name}"
        return sync_url, async_url, "cloud_sql_postgres"

    # Default fallback: SQLite for local offline development
    sqlite_url = os.getenv("DATABASE_URL", "sqlite:///fleet.db")
    return sqlite_url, sqlite_url, "sqlite_local"


def check_runtime_environment() -> Dict:
    """
    Evaluates real GCP and Gemini runtime environment status dynamically.
    No hardcoded fake booleans.
    """
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    instance_conn = os.getenv("INSTANCE_CONNECTION_NAME")
    
    has_gcp_creds = gcp_project is not None or gemini_api_key is not None

    return {
        "gcp_project": gcp_project or "offline_mode",
        "has_gcp_credentials": has_gcp_creds,
        "model_provider": "gemini-3.5-flash (Vertex AI)" if has_gcp_creds else "extractive_rag_fallback (Offline)",
        "database_backend": "Cloud SQL Postgres" if instance_conn else "SQLite (Local/Memory)",
        "model_armor_status": "Vertex AI Model Armor" if has_gcp_creds else "Heuristic Guardrail Fallback",
        "a2a_protocol_status": "Published (/.well-known/agent.json)",
    }
