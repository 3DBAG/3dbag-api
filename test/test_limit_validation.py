"""Invalid page sizes must be rejected before accessing the database."""

from unittest.mock import MagicMock

import pytest

from app import views


@pytest.mark.parametrize("limit", ["0", "-1", "invalid"])
@pytest.mark.parametrize("bbox", [None, "1,2,3,4"])
def test_invalid_limit_returns_400_without_database_access(
    client, monkeypatch, limit, bbox
):
    database = MagicMock(side_effect=AssertionError("Database must not be accessed"))
    monkeypatch.setattr(views.db, "Db", database)
    query = {"limit": limit}
    if bbox is not None:
        query["bbox"] = bbox

    response = client.get("/collections/pand/items", query_string=query)

    assert response.status_code == 400
    assert response.json["code"] == 400
    database.assert_not_called()
    assert client.get("/").status_code == 200
