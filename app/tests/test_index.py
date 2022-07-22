import json
from pathlib import Path

from shapely.strtree import STRtree
from shapely.geometry import box, shape
from ..index import *
from ..db import *


def test_bbox_within_tile():
    """Should detect if a BBOX is completely within a larger tile."""
    bbox = ((68194.423, 395606.054), (68608.839, 396076.441))
    bbox_mc = (morton_code(*bbox[0]), morton_code(*bbox[1]))

    # Build a topological structure of the corner points of the tile polygons, where:
    #   morton_code_of_corner_point: {polygon1, polygon2, ...}
    morton_corner_idx = {}
    with Path("server/tests/data/bag_tiles_3k_sample.geojson").resolve().open("r") as fo:
        tiles_polys = json.load(fo)
    for f in tiles_polys["features"]:
        ring = f["geometry"]["coordinates"][0] # get exterior ring
        for p in ring[:-1]:
            mc = morton_code(*p)
            try:
                morton_corner_idx[mc].append(f["properties"]["tile_id"])
            except KeyError:
                morton_corner_idx[mc] = [f["properties"]["tile_id"], ]
    morton_order = sorted(morton_corner_idx)
    corner_1 = take_closest(morton_order, bbox_mc[0])
    corner_2 = take_closest(morton_order, bbox_mc[1])


def test_bbox_within_tile_shapely():
    """Should detect if a BBOX is completely within a larger tile."""
    bbox = box(68194.423, 395606.054, 68608.839, 396076.441)
    tiles_json = "server/tests/data/bag_tiles_3k_sample.geojson"
    tiles_shapely, tree = tiles_rtree(tiles_json)
    tiles_matched = [tiles_shapely[id(tile)][1] for tile in tree.query(bbox)]

def test_features_in_bbox():
    DB = Db(dbfile="/data/3DBAGplus/bag_centroid_index.gpkg")
    bbox = (68194.423, 395606.054, 68608.839, 396076.441)
    feature_subset = features_in_bbox(DB, bbox)
    print(len(feature_subset))
    DB.conn.close()