from typing import Tuple
from pyproj import Transformer

DEFAULT = 'OGC:CRS84'
STORAGE = 'epsg:28992'


def transform_bbox(bbox: Tuple[float, float, float, float],
                   from_crs: str,
                   to_crs: str) -> Tuple[float, float, float, float]:
    """ Transform a bbox [BL, TR coordinates] from one CRS to another"""
    if from_crs == to_crs:
        return bbox
    transformer = Transformer.from_crs(from_crs, to_crs)
    x1, y1 = transformer.transform(bbox[0], bbox[1])
    x2, y2 = transformer.transform(bbox[2], bbox[3])
    
    return (x1, y1, x2, y2)


def transform_bbox_from_default_to_storage(bbox):
    """Transform bbox from CRS84 to 28992"""
    return transform_bbox(bbox=bbox, from_crs=DEFAULT, to_crs=STORAGE)


def transform_bbox_from_storage_to_default(bbox):
    """Transform bbox from 28992 to CRS84"""
    return transform_bbox(bbox=bbox, from_crs=STORAGE, to_crs=DEFAULT)
