import sys
from pathlib import Path

import psycopg
import pytest

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

from app.db import DATABASE_URL  # noqa: E402
from app.vision import infer  # noqa: E402


@pytest.fixture(scope="session")
def model():
    """The shipped ONNX session; skip with the reason when it has not been exported or pinned yet."""
    try:
        return infer.session()
    except infer.ModelChecksumError as e:
        pytest.skip(f"no usable model: {e}")


@pytest.fixture(scope="session")
def db():
    try:
        psycopg.connect(DATABASE_URL, connect_timeout=3).close()
    except psycopg.Error as e:
        pytest.skip(f"no database at DATABASE_URL ({e.__class__.__name__}); start it with "
                    "`docker compose up -d db` to run the DB-backed vision tests")
