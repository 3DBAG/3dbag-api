"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""


from pathlib import Path

from app import views


class TestDev:
    def test_landing_page(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_conformance(self, client):
        response = client.get("/conformance")
        assert response.status_code == 200

    def test_collections(self, client):
        response = client.get("/collections")
        assert response.status_code == 200

    def test_collections_pand(self, client):
        response = client.get("/collections/pand")
        assert response.status_code == 200

    def test_collections_pand_items(self, client, authorization):
        response = client.get("/collections/pand/items", headers=authorization)
        assert response.status_code == 200

    def test_collections_pand_items_bbox_997(self, app, authorization):
        bbox = "89828.16,398684.9392,91912.899,400333.2867"
        with app.test_request_context("/collections/pand/items",
                                      headers=authorization,
                                      query_string={"bbox": bbox}):
            response = views.pand_items()
            assert response.status_code == 200
            print(len(response.get_json()["features"]))

    def test_collections_pand_one(self, app, authorization):
        feature_id = "NL.IMBAG.Pand.1655100000500573"
        with app.test_request_context(f"/collections/pand/items/{feature_id}",
                                      headers=authorization):
            response = views.get_feature(feature_id)
            assert response.status_code == 200

    def test_load_cityjsonfeature(self):
        feature_id = "NL.IMBAG.Pand.1655100000548444"
        promise = views.load_cityjsonfeature(feature_id)
        assert feature_id in dict(promise)["CityObjects"]


class TestOnPodzilla:
    def test_collections_pand_items_bbox(self, app, authorization):
        bbox = "68194.423,395606.054,68608.839,396076.441"
        with app.test_request_context("/collections/pand/items",
                                      headers=authorization,
                                      query_string={"bbox": bbox}):
            response = views.pand_items()
            assert response.status_code == 200
            print(len(response.get_json()["features"]))

    def test_collections_pand_items_bbox_large(self, app, authorization):
        """Large area in Den Haag, 44755451m2, 94912 features"""
        bbox = "77797.577,450905.086,85494.901,456719.503"
        with app.test_request_context("/collections/pand/items",
                                      headers=authorization,
                                      query_string={"bbox": bbox}):
            response = views.pand_items()
            assert response.status_code == 200
            print(len(response.get_json()["features"]))

    def test_collections_pand_items_bbox_verylarge(self, app, authorization):
        """Very large area in Den Haag, 234117167m2, 284462 features"""
        bbox = "75877.011,446130.034,92446.593,460259.369"
        with app.test_request_context("/collections/pand/items",
                                      headers=authorization,
                                      query_string={"bbox": bbox}):
            response = views.pand_items()
            assert response.status_code == 200
            print(len(response.get_json()["features"]))

