import json
import logging
from typing import List

from cjdb.modules.exporter import Exporter
from flask import request

from app.parameters import Parameters


def load_metadata(connection):
    """Loads the metadata - same for all features."""
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery="SELECT object_id from cjdb.city_object limit 1",
        output=None,
    ) as exporter:
        exporter.get_data()
        metadata = exporter.get_metadata()
    return json.loads(metadata)


def load_cityjsonfeature(featureId, connection) -> str:
    """Loads a single feature."""
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery=f"SELECT '{featureId}' as object_id",
        output=None,
    ) as exporter:
        exporter.get_data()
        feature = exporter.get_features()
    return json.loads(feature[0])


def load_cityjsonfeatures(featureIds: List[str], connection) -> str:
    """Loads a group of features."""
    feature_ids_str = (
        str(
            [[x] for x in featureIds])[1:-1].replace(
                "[", "(").replace("]", ")")
    )
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery=f"""VALUES {feature_ids_str}""",
        output=None,
    ) as exporter:
        exporter.get_data()
        features = exporter.get_features()
    return [json.loads(feature) for feature in features]


def get_paginated_features(features,
                           url: str,
                           connection,
                           parameters: Parameters):
    """From https://stackoverflow.com/a/55546722"""
    logging.debug(
        f"""Pagination started with limit {parameters.limit}
        and offset {parameters.offset}"""
    )
    if parameters.bbox is not None:
        bbox = \
        f"{parameters.bbox[0]},{parameters.bbox[1]},{parameters.bbox[2]},{parameters.bbox[3]}"  # noqa
    nr_matched = len(features)
    # make response
    links = []
    obj = {"numberMatched": nr_matched}
    # make URLs
    links.append(
        {
            "href": request.url,
            "rel": "self",
            "type": "application/city+json",
            "title": "this document",
        }
    )
    url_prev = url_next = f"{url}?"
    # make previous URL
    if parameters.offset > 1:
        offset_copy = max(1, parameters.offset - parameters.limit)
        limit_copy = parameters.offset - 1
        ol = f"offset={offset_copy:d}&limit={limit_copy:d}"
        if parameters.bbox is None:
            url_prev += ol
        else:
            url_prev += f"bbox={bbox}&" + ol
        links.append(
            {
                "href": url_prev,
                "rel": "prev",
                "type": "application/city+json",
            }
        )
    # make next URL
    if parameters.offset + parameters.limit < nr_matched:
        offset_copy = parameters.offset + parameters.limit
        ol = f"offset={offset_copy:d}&limit={parameters.limit:d}"
        if parameters.bbox is None:
            url_next += ol
        else:
            url_next += f"bbox={bbox}&" + ol
        links.append(
            {
                "href": url_next,
                "rel": "next",
                "type": "application/city+json",
            }
        )
    obj["type"] = "FeatureCollection"
    obj["links"] = links
    if not all(features):
        obj["numberReturned"] = 0
        obj["features"] = []
    else:
        obj["metadata"] = load_metadata(connection=connection)
        res = features[
            (parameters.offset - 1):(parameters.offset - 1 + parameters.limit)
        ]
        obj["numberReturned"] = len(res)
        obj["features"] = load_cityjsonfeatures(res, connection)
    return obj
