from pprint import pprint

from ..app import *

def test_landing_page(client):
    response = client.get("/")
    assert response.get_json()["hello"] == "world"

def test_conformance(client):
    response = client.get("/conformance")

def test_collections(client):
    response = client.get("/collections")

def test_collections_pand(client):
    response = client.get("/collections/pand")

def test_collections_pand_items(client):
    response = client.get("/collections/pand/items")

def test_collections_pand_one(client):
    response = client.get("/collections/pand/items/0851100000000564")

def test_collections_pand_addresses(client):
    response = client.get("/collections/pand/items/0851100000000564/addresses")

def test_collections_pand_surfaces(client):
    response = client.get("/collections/pand/items/0851100000000564/surfaces")

def test_load_cityjsonfeature():
    featureId = "NL.IMBAG.Pand.1655100000548444"
    promise = load_cityjsonfeature(featureId)
    pprint(promise)