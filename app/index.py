"""Data indexing

Copyright 2022 3DGI <info@3dgi.nl>
"""
from typing import Tuple, List
from bisect import bisect_left
from pathlib import Path
import json

from shapely.strtree import STRtree
from shapely.geometry import shape


class BBOXCache:
    """Cached BBOX query of features.

    If a new BBOX is requested then query the index,
    store the feature subset in the
    cache and return the feature subset.

    If the previously requested BBOX is requested again,
    return the feature subset from
    the cache.
    """

    def __init__(self):
        self.feature_subset = ()
        self.bbox = ()

    def add(self, feature_subset, bbox: Tuple[str, str, str, str]):
        self.feature_subset = feature_subset
        self.bbox = bbox

    def get(self, conn, bbox: Tuple[float, float, float, float]):
        """Get the featureIDs in the `bbox`.
        BBOX comparison is string comparison of
        the coordinate values that are formatted
        to three decimal places.
        """
        # We expect that at this point we have a valid 'bbox',
        # as in a tuple of four floats.
        bbox_new = tuple(map("{:.3f}".format, bbox))
        if bbox_new == self.bbox:
            return self.feature_subset
        else:
            self.add(get_features_in_bbox(conn, bbox), bbox_new)
            return self.feature_subset

    def clear(self):
        self.feature_subset = ()
        self.bbox = ()


def get_all_object_ids(conn) -> Tuple[str]:
    """Retrieve all the object ids from the DB"""
    # TODO OPTIMIZE: we could keep the shapely.rtree in memory instead
    # of querying in sqlite, provided that there is enough RAM for it (~1.8GB).
    query = """
                SELECT co.object_id
                FROM cjdb.city_object co;
            """.replace("\n", "")
    return tuple(t[0] for t in conn.get_query(query))


def get_features_in_bbox(conn, bbox: List[float]) -> Tuple[str]:
    """
    Retrieve from the DB all the object ids of the buildings
    lying in the input bbox.
    """
    # TODO OPTIMIZE: we could keep the shapely.rtree in memory instead
    # of querying in sqlite, provided that there is enough RAM for it (~1.8GB).
    query = f"""
                SELECT co.object_id
                FROM cjdb.city_object co
                WHERE st_within(co.ground_geometry,
                ST_MakeEnvelope({bbox[0]},
                                {bbox[1]},
                                {bbox[2]},
                                {bbox[3]},  7415));
            """.replace("\n", "")
    return tuple(t[0] for t in conn.get_query(query))


def read_tiles_to_shapely(tiles_json):
    """Generator over (Polygon-id, (Polygon, tile_id))"""
    with Path(tiles_json).resolve().open("r") as fo:
        tiles_polys = json.load(fo)
    for f in tiles_polys["features"]:
        sh = shape(f["geometry"])
        yield id(sh), (sh, f["properties"]["tile_id"])


def tiles_rtree(tiles_shapely):
    """Create an STR-packed R-tree from the 3D BAG tile polygons.

    See https://shapely.readthedocs.io/en/stable/manual.html#str-packed-r-tree
    """
    return STRtree(g[0] for i, g in tiles_shapely)


def take_closest(myList, myNumber):
    """
    Assumes myList is sorted. Returns closest value to myNumber.

    If two numbers are equally close, return the smallest number.

    Reference: https://stackoverflow.com/a/12141511
    """
    pos = bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before


# Computing Morton-code. Reference: https://github.com/trevorprater/pymorton

def __part1by1_64(n):
    """64-bit mask"""
    n &= 0x00000000ffffffff                  # binary: 11111111111111111111111111111111,                                len: 32 # noqa
    n = (n | (n << 16)) & 0x0000FFFF0000FFFF # binary: 1111111111111111000000001111111111111111,                        len: 40 # noqa
    n = (n | (n << 8))  & 0x00FF00FF00FF00FF # binary: 11111111000000001111111100000000111111110000000011111111,        len: 56 # noqa
    n = (n | (n << 4))  & 0x0F0F0F0F0F0F0F0F # binary: 111100001111000011110000111100001111000011110000111100001111,    len: 60 # noqa
    n = (n | (n << 2))  & 0x3333333333333333 # binary: 11001100110011001100110011001100110011001100110011001100110011,  len: 62 # noqa
    n = (n | (n << 1))  & 0x5555555555555555 # binary: 101010101010101010101010101010101010101010101010101010101010101, len: 63 # noqa
    return n


def __unpart1by1_64(n):
    n &= 0x5555555555555555                  # binary: 101010101010101010101010101010101010101010101010101010101010101, len: 63 # noqa
    n = (n ^ (n >> 1))  & 0x3333333333333333 # binary: 11001100110011001100110011001100110011001100110011001100110011,  len: 62 # noqa
    n = (n ^ (n >> 2))  & 0x0f0f0f0f0f0f0f0f # binary: 111100001111000011110000111100001111000011110000111100001111,    len: 60 # noqa
    n = (n ^ (n >> 4))  & 0x00ff00ff00ff00ff # binary: 11111111000000001111111100000000111111110000000011111111,        len: 56 # noqa
    n = (n ^ (n >> 8))  & 0x0000ffff0000ffff # binary: 1111111111111111000000001111111111111111,                        len: 40 # noqa
    n = (n ^ (n >> 16)) & 0x00000000ffffffff # binary: 11111111111111111111111111111111,                                len: 32 # noqa
    return n


def interleave(*args):
    """Interleave two integers"""
    if len(args) != 2:
        raise ValueError('Usage: interleave2(x, y)')
    for arg in args:
        if not isinstance(arg, int):
            print('Usage: interleave2(x, y)')
            raise ValueError("Supplied arguments contain a non-integer!")

    return __part1by1_64(args[0]) | (__part1by1_64(args[1]) << 1)


def deinterleave(n):
    if not isinstance(n, int):
        print('Usage: deinterleave2(n)')
        raise ValueError("Supplied arguments contain a non-integer!")

    return __unpart1by1_64(n), __unpart1by1_64(n >> 1)


def morton_code(x: float, y: float):
    """Takes an (x,y) coordinate tuple and computes their Morton-key.

    Casts float to integers by multiplying them with
    100 (millimetre precision).
    """
    return interleave(int(x * 100), int(y * 100))


def rev_morton_code(morton_key: int) -> Tuple[float, float]:
    """Get the coordinates from a Morton-key"""
    x, y = deinterleave(morton_key)
    return float(x) / 100.0, float(y) / 100.0
