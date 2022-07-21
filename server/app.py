import logging
from pathlib import Path
import json

from flask import (Flask, render_template, abort, request, url_for, jsonify,
                   send_from_directory)


from server import parser, index, db


logging.basicConfig(level=logging.DEBUG)
FEATURE_IDX = parser.feature_index() # feature index of (featureId : tile_id)
FEATURE_IDS = list(FEATURE_IDX.keys()) # featureID list
tiles_json = "/data/3DBAGplus/bag_tiles_3k.geojson"
TILES_SHAPELY= index.read_tiles_to_shapely(tiles_json)
TILES_RTREE = index.tiles_rtree(TILES_SHAPELY)
DBFILE = "/data/3DBAGplus/bag_centroid_index.gpkg"
app = Flask(__name__)


def load_cityjsonfeature(featureId):
    """Loads a single feature."""
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    json_path = parser.find_co_path(parent_id, tile_id)
    if not json_path.exists():
        logging.debug(f"CityJSON file {json_path} not found ")
        abort(404)
    else:
        with json_path.open("r") as fo:
            return json.load(fo, encoding='utf-8-sig')


def get_paginated_features(features, url, offset, limit):
    """From https://stackoverflow.com/a/55546722"""
    offset = int(offset)
    limit = int(limit)
    nr_matched = len(features)
    if nr_matched < offset or limit < 0:
        abort(404)
    # make response
    links = []
    obj = {"numberMatched": nr_matched}
    # make URLs
    links.append({
        "href": request.url,
        "rel": "self",
        "type": "application/city+json",
        "title": "this document"
    })
    # make previous URL
    if offset > 1:
        offset_copy = max(1, offset - limit)
        limit_copy = offset - 1
        links.append({
            "href": f"{url}?offset={offset_copy:d}&limit={limit_copy:d}",
            "rel": "prev",
            "type": "application/city+json",
        })
    # make next URL
    if offset + limit < nr_matched:
        offset_copy = offset + limit
        links.append({
            "href": f"{url}?offset={offset_copy:d}&limit={limit:d}",
            "rel": "next",
            "type": "application/city+json",
        })
    obj["links"] = links
    # get features according to bounds
    res = features[(offset - 1):(offset - 1 + limit)]
    obj["numberReturned"] = len(res)
    obj["features"] = [load_cityjsonfeature(featureId) for featureId in res]
    return obj


@app.get('/')
def landing_page():
    return {
        "title": "3D BAG plus",
        "description": "3D BAG plus is an extended version of the 3D BAG data set. It contains additional information that is either derived from the 3D BAG, or integrated from other data sources.",
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
                "title": "OGC API conformance classes implemented by this server"
            },
            {
                "href": url_for("collections", _external=True),
                "rel": "collections",
                "type": "data",
                "title": "Information about the feature collections"
            },
        ]
    }


@app.get('/api')
def api():
    # TODO: need to send JSON instead of YAML
    return send_from_directory(Path(app.root_path).parent, '3dbag_api_merged.yaml')


@app.get('/api.html')
def api_html():
    return render_template("swagger_ui.html")


@app.get('/conformance')
def conformance():
    return {
        "conformsTo": [
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30",
            "https://www.cityjson.org/specs/1.1.1"
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
        ]
    }


@app.get('/collections/pand')
def pand():
    return {
        "id": "pand",
        "title": "3D pand",
        "description": "the 3d bag pand layer",
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
                "crs": "https://www.opengis.net/def/crs/EPSG/0/7415"
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
            "https://www.opengis.net/def/crs/EPSG/0/7415"
        ],
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
                "type": "application/city+json",
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
def pand_items():
    re_bbox = request.args.get("bbox", None)
    if re_bbox is not None:
        r = re_bbox.split(',')
        if len(r) != 4:
            abort(400)
        try:
            bbox = list(map(float, r))
        except TypeError as e:
            logging.debug(e)
            abort(400)
        # tiles_matches = [TILES_SHAPELY[id(tile)][1] for tile in TILES_RTREE.query(bbox)]
        logging.debug(f"query with bbox {bbox}")
        conn = db.Db(dbfile=DBFILE)
        feature_subset = index.features_in_bbox(conn, bbox)
        conn.conn.close()
    else:
        feature_subset = FEATURE_IDS
    print(feature_subset)
    return jsonify(get_paginated_features(feature_subset,
                                          url_for("pand_items", _external=True),
                                          offset=request.args.get("offset", 1),
                                          limit=request.args.get("limit", 10)))


@app.get('/collections/pand/items/<featureId>')
def get_feature(featureId):
    logging.debug(f"requesting {featureId}")
    cityjsonfeature = load_cityjsonfeature(featureId)

    links = [
        {
            "href": request.url,
            "rel": "self",
            "type": "application/city+json",
            "title": "this document"
        },
        {
            "href": url_for("pand", _external=True),
            "rel": "collection",
            "type": "application/city+json"
        },
        {
            "href": f'{url_for("pand", _external=True)}/items/{cityjsonfeature["id"]}',
            "rel": "parent",
            "type": "application/city+json"
        },
    ]
    for coid in cityjsonfeature["CityObjects"][cityjsonfeature["id"]]["children"]:
        links.append({
            "href": f'{url_for("pand", _external=True)}/items/{coid}',
            "rel": "child",
            "type": "application/city+json"
        })

    return {
        "id": cityjsonfeature["id"],
        "cityjsonfeature": cityjsonfeature,
        "links": links
    }



@app.get('/collections/pand/items/<featureId>/addresses')
def get_addresses(featureId):
    logging.debug(f"requesting {featureId} addresses")
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    try:
        csv_path = parser.find_addresses_csv_path(tile_id)
        addresses_gen = parser.parse_addresses_csv(csv_path)
        # FIXME: here we need the BAG identifiactie, but for the surfaces records we need the 3D BAG building part identificatie
        addresses_record = parser.get_feature_record(parent_id, addresses_gen)
    except BaseException as e:
        logging.exception(e)
        abort(500)

    if addresses_record is None:
        logging.debug(f"featureId {featureId} not found in the addresses records")
        abort(404)

    addresses_record["links"] = [
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
    ]

    return addresses_record


@app.get('/collections/pand/items/<featureId>/surfaces')
def get_surfaces(featureId):
    logging.debug(f"requesting {featureId} surfaces")
    parent_id = parser.get_parent_id(featureId)
    tile_id = parser.get_tile_id(parent_id, FEATURE_IDX)
    if tile_id is None:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    try:
        csv_path = parser.find_surfaces_csv_path(tile_id)
        surfaces_gen = parser.parse_surfaces_csv(csv_path)
        surfaces_record = parser.get_feature_record(featureId, surfaces_gen)
    except BaseException as e:
        logging.exception(e)
        abort(500)

    if surfaces_record is None:
        logging.debug(f"featureId {featureId} not found in the surfaces records")
        abort(404)

    surfaces_record["links"] = [
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
    ]

    return surfaces_record


if __name__ == '__main__':
    app.run(debug=True)
