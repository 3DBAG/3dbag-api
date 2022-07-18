from flask import Flask, jsonify

app = Flask(__name__)

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
    print(f"requesting {featureId} surfaces")
    raise NotImplementedError


if __name__ == '__main__':
    app.run(debug=True)
