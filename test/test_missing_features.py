"""Missing features must fail a request without terminating its worker."""

import json
from unittest.mock import MagicMock

import pytest

from app import loading, views

FEATURE_ID = "NL.IMBAG.Pand.0718100000001411"


@pytest.fixture()
def export_request(monkeypatch):
    connection = MagicMock()
    cursor = connection.conn.cursor.return_value.__enter__.return_value
    cursor.mogrify.return_value = b"SELECT 'test-id' AS object_id"
    monkeypatch.setattr(views.db, "Db", lambda: connection)
    exporter = MagicMock()
    factory = MagicMock()
    factory.return_value.__enter__.return_value = exporter
    monkeypatch.setattr(loading, "Exporter", factory)
    return connection, cursor, exporter


def test_missing_building_returns_404_and_application_keeps_running(
    client, export_request
):
    connection, _, exporter = export_request
    exporter.get_data.side_effect = SystemExit(1)

    for _ in range(3):
        response = client.get(f"/collections/pand/items/{FEATURE_ID}")
        assert response.status_code == 404
        assert response.json["code"] == 404
        assert client.get("/").status_code == 200

    assert connection.conn.close.call_count == 3
    exporter.get_features.assert_not_called()


def test_existing_building_is_exported_and_connection_closed(client, export_request):
    connection, _, exporter = export_request
    feature = {
        "id": FEATURE_ID,
        "CityObjects": {FEATURE_ID: {"children": []}},
    }
    exporter.get_features.return_value = [json.dumps(feature)]
    exporter.get_metadata.return_value = json.dumps({"type": "CityJSON"})

    response = client.get(f"/collections/pand/items/{FEATURE_ID}")

    assert response.status_code == 200
    assert response.json["id"] == FEATURE_ID
    assert response.json["feature"] == feature
    connection.conn.close.assert_called_once()


def test_empty_export_returns_404(client, export_request):
    connection, _, exporter = export_request
    exporter.get_features.return_value = []

    assert client.get(f"/collections/pand/items/{FEATURE_ID}").status_code == 404
    connection.conn.close.assert_called_once()


@pytest.mark.parametrize("error", [RuntimeError("database failed"), SystemExit(2)])
def test_other_export_failures_return_500_and_close_connection(
    client, export_request, error
):
    connection, _, exporter = export_request
    exporter.get_data.side_effect = error

    response = client.get(f"/collections/pand/items/{FEATURE_ID}")

    assert response.status_code == 500
    connection.conn.close.assert_called_once()
    assert client.get("/").status_code == 200


def test_requested_id_is_quoted_as_a_sql_value(client, export_request):
    _, cursor, exporter = export_request
    exporter.get_data.side_effect = SystemExit(1)
    feature_id = "missing' OR 1=1 --"

    response = client.get(f"/collections/pand/items/{feature_id}")

    assert response.status_code == 404
    cursor.mogrify.assert_called_once_with("SELECT %s AS object_id", (feature_id,))


def test_no_exportable_features_in_a_batch_does_not_exit(export_request):
    connection, _, exporter = export_request
    exporter.get_data.side_effect = SystemExit(1)

    assert loading.load_cityjsonfeatures([FEATURE_ID], connection) == ({}, [])


def test_empty_id_list_skips_exporter(export_request):
    connection, _, _ = export_request

    assert loading.load_cityjsonfeatures([], connection) == ({}, [])
    loading.Exporter.assert_not_called()


@pytest.mark.parametrize("offset", [2, 601])
@pytest.mark.parametrize("bbox", [None, "1,2,3,4"])
def test_offset_beyond_results_returns_empty_page(
    client, export_request, monkeypatch, offset, bbox
):
    connection, _, _ = export_request
    monkeypatch.setattr(views, "_get_default_feature_set", lambda: [FEATURE_ID])
    monkeypatch.setattr(views.bbox_cache, "get", lambda conn, bounds: [FEATURE_ID])
    query = {"offset": offset, "limit": 50}
    if bbox is not None:
        query["bbox"] = bbox

    response = client.get("/collections/pand/items", query_string=query)

    assert response.status_code == 200
    assert response.json["type"] == "FeatureCollection"
    assert response.json["numberMatched"] == 1
    assert response.json["numberReturned"] == 0
    assert response.json["features"] == []
    assert not any(link["rel"] == "next" for link in response.json["links"])
    loading.Exporter.assert_not_called()
    connection.conn.close.assert_called_once()


def test_missing_batch_returns_empty_page_and_keeps_application_running(
    client, export_request, monkeypatch
):
    connection, _, exporter = export_request
    exporter.get_data.side_effect = SystemExit(1)
    monkeypatch.setattr(views.bbox_cache, "get", lambda conn, bbox: [FEATURE_ID])

    response = client.get("/collections/pand/items?bbox=1,2,3,4")

    assert response.status_code == 200
    assert response.json["features"] == []
    assert response.json["numberReturned"] == 0
    connection.conn.close.assert_called_once()
    assert client.get("/").status_code == 200
