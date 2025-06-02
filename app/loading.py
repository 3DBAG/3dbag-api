"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""

import json
import logging
from typing import List, Tuple

from cjdb.modules.exporter import Exporter
from flask import request

from app.parameters import Parameters


def load_cityjsonfeature(featureId: List[str],
                         connection) -> \
        Tuple[str, str]:
    """Loads a single feature."""
    with Exporter(
        connection=connection.conn,
        schema="cjdb",
        sqlquery=f"SELECT '{featureId}' as object_id",
        output=None,
    ) as exporter:
        logging.info(exporter.sqlquery)
        exporter.get_data()
        feature = exporter.get_features()
        metadata = exporter.get_metadata()
    return (json.loads(metadata), json.loads(feature[0]))


def load_cityjsonfeatures(featureIds: List[str],
                          connection) -> \
        Tuple[str, List[str]]:
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
        metadata = exporter.get_metadata()
    return (json.loads(metadata),
            [json.loads(feature) for feature in features])


def get_paginated_features(features: List[str],
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
    if not all(features) or len(features) == 0:
        obj["numberReturned"] = 0
        obj["features"] = []
    else:
        
        res = features[
            (parameters.offset - 1):(parameters.offset - 1 + parameters.limit)
        ]
        metadata, cityjsonfeatures = load_cityjsonfeatures(res, connection)
        obj["metadata"] = metadata
        obj["numberReturned"] = len(res)
        obj["features"] = cityjsonfeatures
    return obj
