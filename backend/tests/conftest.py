import os
import tempfile

import pytest


@pytest.fixture(scope="session")
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["SAF_DB_PATH"] = path
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c

    os.remove(path)
