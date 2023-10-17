"""3DBAG Features API backed by CityJSON

Copyright 2022 3DGI <info@3dgi.nl>
"""

import logging
from pathlib import Path

import yaml

from flask import (abort, jsonify, make_response, render_template,
                   request, url_for)

from app import app, auth, db, db_users, index, loading
from app.parameters import Parameters, STORAGE_CRS
from app.authentication import UserAuth, Permission

DEFAULT_LIMIT = 10
DEFAULT_MAX_LIMIT = 10000
DEFAULT_OFFSET = 1

bbox_cache = index.BBOXCache()

conn = db.Db()
logging.debug("Collecting all available object ids.")
DEFAULT_FEATURE_SET = index.get_all_object_ids(conn)
conn.conn.close()


@app.get('/')
def landing_page():
    return {
        "title": "3DBAG API",
        "description": "3DBAG is an extended version of the 3DBAG data set. It contains additional information that is either derived from the 3DBAG, or integrated from other data sources.", # noqa
        "links": [
            {
                "href": request.url,
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
            {
                "href": url_for("api", _external=True),
                "rel": "service-desc",
                "type": "application/vnd.oai.openapi+json;version=3.0",
                "title": "the API definition"
            },
            {
                "href": url_for("api_html", _external=True),
                "rel": "service-doc",
                "type": "text/html",
                "title": "the API documentation"
            },
            {
                "href": url_for("conformance", _external=True),
                "rel": "conformance",
                "type": "application/json",
                "title": "Conformance classes implemented by this server" # noqa
            },
            {
                "href": url_for("collections", _external=True),
                "rel": "data",
                "type": "application/json",
                "title": "Information about the feature collections"
            },
        ]
    }


@app.get('/api')
def api():
    rdir = Path(app.root_path) / "schemas"
    with (rdir / "3dbagapi_spec.yaml").open("r") as fo:
        f = yaml.full_load(fo)
    return jsonify(f)


@app.get('/api.html')
def api_html():
    return render_template("redoc_ui.html")


@app.get('/conformance')
def conformance():
    return {
        "conformsTo": [
            "https://cityjson.org/specs/2.0.0/"
        ]
    }


@app.get('/collections')
def collections():
    return {
        "collections": [
            pand(),
        ],
        "links": [
            {
                "href": url_for("collections", _external=True),
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
        ],
        "crs": [
            STORAGE_CRS
        ]
    }


@app.get('/collections/pand')
def pand():
    return {
        "id": "pand",
        "title": "Pand",
        "description": "3D building models based on the 'pand' layer of the BAG dataset.",
        "extent": {
            "spatial": {
                "bbox": [
                    [
                           10000,
                            306250,
                            287760,
                            623690
                    ]
                ],
                "crs": STORAGE_CRS
            },
            "temporal": {
                "interval": [
                    None,
                    "2019-12-31T24:59:59Z"
                ]
            }
        },
        "itemType": "feature",
        "crs": [
            STORAGE_CRS
        ],
        "storageCrs": STORAGE_CRS,
        "version": {
            "collection": "v2023.08.09",
            "api": "0.1"
        },
        "links": [
            {
                "href": url_for("pand", _external=True),
                "rel": "self",
                "type": "application/json",
                "title": "this document"
            },
            {
                "href": url_for("pand_items", _external=True),
                "rel": "items",
                "type": "application/geo+json",
                "title": "Pand items"
            },
            {
                "href": "https://creativecommons.org/licenses/by/4.0/",
                "rel": "license",
                "type": "text/html",
                "title": "CC BY 4.0"
            },
            {
                "href": "https://creativecommons.org/licenses/by/4.0/rdf",
                "rel": "license",
                "type": "application/rdf+xml",
                "title": "CC BY 4.0"
            }
        ]
    }


@app.get('/collections/pand/items')
# @auth.login_required
def pand_items():
    # Validation
    for key in request.args.keys():
        if key not in ["bbox", "offset", "limit", "crs", "bbox-crs"]:
            error_msg = "Unknown parameter %s", key
            logging.error(error_msg)
            abort(400)

    query_params = Parameters(
        offset=request.args.get("offset", DEFAULT_OFFSET),
        limit=request.args.get("limit", DEFAULT_LIMIT),
        crs=request.args.get("crs", STORAGE_CRS),
        bbox_crs=request.args.get("bbox-crs", STORAGE_CRS),
        bbox=request.args.get("bbox", None)
    )
    conn = db.Db()

    if query_params.bbox:
        feature_subset = bbox_cache.get(conn, query_params.bbox)

    else:
        feature_subset = DEFAULT_FEATURE_SET

    logging.debug(f" Selection of {len(feature_subset)}  features.")
    response = make_response(jsonify(loading.get_paginated_features(
        feature_subset,
        url_for("pand_items", _external=True), conn,
        query_params)), 200)
    response.headers["Content-Crs"] = f"<{query_params.crs}>"
    conn.conn.close()
    return response


@app.get('/collections/pand/items/<featureId>')
# @auth.login_required
def get_feature(featureId):
    logging.debug(f"Requesting {featureId}")
    for key in request.args.keys():
        if key not in ["crs"]:
            error_msg = """Unknown parameter %s.
                            For GET requests for specifics features
                            (/collections/pand/items/<featureId>)
                            only 'crs' is available.""", key
            logging.error(error_msg)
            abort(400)

    query_params = Parameters(
        offset=request.args.get("offset", DEFAULT_OFFSET),
        limit=request.args.get("limit", DEFAULT_LIMIT),
        crs=request.args.get("crs", STORAGE_CRS),
        bbox_crs=request.args.get("bbox-crs", STORAGE_CRS),
        bbox=request.args.get("bbox", None)
    )
    conn = db.Db()
    metadata, cityjsonfeature = loading.load_cityjsonfeature(featureId, conn)
    conn.conn.close()

    links = [
        {
            "href": request.url,
            "rel": "self",
            "type": "application/json",
            "title": "this document"
        },
        {
            "href": url_for("pand", _external=True),
            "rel": "collection",
            "type": "application/json"
        },
        {
            "href": f'{url_for("pand", _external=True)}/items/{cityjsonfeature["id"]}',# noqa
            "rel": "parent",
            "type": "application/city+json"
        },
    ]
    for coid in cityjsonfeature["CityObjects"][cityjsonfeature["id"]]["children"]: # noqa
        links.append({
            "href": f'{url_for("pand", _external=True)}/items/{coid}',
            "rel": "child",
            "type": "application/city+json"
        })
    response = make_response(jsonify({
        "id": cityjsonfeature["id"],
        "metadata": metadata,
        "feature": cityjsonfeature,
        "links": links
    }), 200)
    response.headers["Content-Crs"] = f"<{query_params.crs}>"

    return response


@app.route("/register", methods=["GET", "POST"])
# @auth.login_required(role=Permission.ADMINISTRATOR)
def register():
    user = UserAuth(**request.json)
    db_users.session.add(user)
    db_users.session.commit()
    return jsonify({"message": f"Registered user: {user.username}"})


if __name__ == '__main__':
    app.run(debug=True)
