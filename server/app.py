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
    print(f"requesting {featureId} addresses")
    raise NotImplementedError


@app.get('/collections/pand/items/<featureId>/surfaces')
def get_surfaces(featureId):
    logging.debug(f"requesting {featureId} surfaces")
    # Get the ID of the parent feature if it is a BuildinPart,
    # like NL.IMBAG.Pand.1655100000488643-0, because the feature_index only
    # contains the parent IDs.
    parent_id = featureId.rsplit("-")[0]
    try:
        tile_id = FEATURE_IDX[parent_id]
    except KeyError:
        logging.debug(f"featureId {parent_id} not found in feature_index")
        abort(404)

    try:
        csv_path = parser.find_surfaces_csv_path(tile_id)
        surfaces_gen = parser.parse_surfaces_csv(csv_path)
        surface_record = parser.get_feature_surfaces(featureId, surfaces_gen)
    except BaseException as e:
        logging.exception(e)
        abort(500)

    surface_record["links"] = [
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

    return surface_record


if __name__ == '__main__':
    app.run(debug=True)
