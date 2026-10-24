import sys
from pathlib import Path

import psycopg
import pytest

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.db import DATABASE_URL  # noqa: E402
from app.hazard.rules import load_thresholds  # noqa: E402


@pytest.fixture(scope="session")
def t():
    return load_thresholds()


@pytest.fixture(scope="session")
def db():
    """Skip DB tests with a clear message when PostGIS is not reachable at DATABASE_URL."""
    try:
        psycopg.connect(DATABASE_URL, connect_timeout=3).close()
    except psycopg.Error as e:
        pytest.skip(f"no database at DATABASE_URL ({e.__class__.__name__}); start it with "
                    "`docker compose up -d db` to run the integration tests")
