from app.transformations import (transform_bbox_from_default_to_storage,
                                 transform_bbox_from_storage_to_default)
from pytest import approx
from typing import Tuple

BBOX_28992: Tuple[float, float, float, float] = (13593.338,
                                                 562890.404,
                                                 269593.338,
                                                 562890.404)

BBOX_CRS84: Tuple[float, float, float, float] = (3.27902416128228,
                                                 53.03432339517632,
                                                 7.095830412113795,
                                                 53.040692378552535)


def test_transform_bbox_from_default_to_storage():
    new_box = transform_bbox_from_default_to_storage(BBOX_CRS84)
    assert new_box == approx(BBOX_28992)


def test_transform_bbox_from_storage_to_default():
    new_box = transform_bbox_from_storage_to_default(BBOX_28992)
    assert new_box == approx(BBOX_CRS84)
