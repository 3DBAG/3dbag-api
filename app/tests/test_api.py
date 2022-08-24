from pprint import pprint

import yappi

from app.views import load_cityjsonfeature, pand_items
def test_collections_pand_items(client, authorization):
    response = client.get("/collections/pand/items", headers=authorization)
    print(response.get_json())

def test_collections_pand_items_bbox(app, authorization):
    bbox = "68194.423,395606.054,68608.839,396076.441"
    with app.test_request_context("/collections/pand/items",
                                  headers=authorization,
                                  query_string={"bbox": bbox}):
        response = pand_items()
        print(response.get_json())

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