import pytest

from app import app as flask_app


@pytest.fixture()
def app():
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture()
def authorization():
    # balazs:1234 in base64
    return {"Authorization": "Basic YmFsYXpzOjEyMzQ="}