import logging

from flask import Flask, jsonify, abort, request, url_for

from server import parser

app = Flask(__name__)
FEATURE_IDX = parser.feature_index()


@app.get('/')
def landing_page():
    return jsonify({"hello": "world"})


@app.get('/conformance')
def conformance():
    raise NotImplementedError


@app.get('/collections')
def collections():
    raise NotImplementedError


@app.get('/collections/pand')
def pand():
    raise NotImplementedError


@app.get('/collections/pand/items')
def pand_items():
    raise NotImplementedError


@app.get('/collections/pand/items/<featureId>')
def get_feature(featureId):
    print(f"requesting {featureId}")
    raise NotImplementedError


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
