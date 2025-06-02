"""
Copyright (c) 2023 TU Delft 3D geoinformation group, Ravi Peters (3DGI), and Balázs Dukai (3DGI)
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Union

from flask import abort
from pyproj import exceptions

from app.transformations import (transform_bbox_from_default_to_storage,
                                 transform_bbox_from_storage_to_default)

STORAGE_CRS = "http://www.opengis.net/def/crs/EPSG/0/7415"

DEFAULT_BBOX = [
    10000,
    306250,
    287760,
    623690
]

DEFAULT_OFFSET = 1
DEFAULT_LIMIT = 10
DEFAULT_MAX_LIMIT = 100

@dataclass
class Parameters:
    """ Class for holding feature parameters"""
    offset: Union[int, str]
    limit: Union[int, str]
    crs: str
    bbox_crs: str
    bbox: Optional[Union[Tuple[float, float, float, float], str]] = None

    def __post_init__(self):
        try:
            self.limit = int(self.limit)
            if self.limit > DEFAULT_MAX_LIMIT:
                self.limit = DEFAULT_MAX_LIMIT
        except ValueError as error:
            logging.error(
                "Invalid parameter value. Limit must be integer. %s",
                error)
            abort(400)

        try:
            self.offset = int(self.offset)
        except ValueError as error:
            logging.error(
                "Invalid parameter value. Offset must be integer. %s",
                error)
            abort(400)

        if self.limit < 0:
            logging.error("Limit must be an positive integer.")
            abort(400)
        
        if self.offset < 0:
            logging.error("Offset must be an positive integer.")
            abort(400)

        if self.crs.lower() == STORAGE_CRS.lower():
            self.crs = STORAGE_CRS
        else:
            error_msg = (
                "Unknown crs %s. Must be either %s",
                self.crs,
                STORAGE_CRS)
            logging.error(error_msg)
            abort(400)

        if self.bbox_crs.lower() == STORAGE_CRS.lower():
            self.bbox_crs = STORAGE_CRS
        else:
            error_msg = (
                "Unknown bbox-crs %s. Must be either %s",
                self.bbox_crs,
                STORAGE_CRS)
            logging.error(error_msg)
            abort(400)

        if self.bbox is not None:
            r = self.bbox.strip().strip("[]").split(',')
            if len(r) != 4:
                logging.error("BBox needs 4 parameters.")
                abort(400)
            try:
                self.bbox = tuple(list(map(float, r)))
            except ValueError as error:
                logging.error("Invalid bbox values: %s ", error)
                abort(400)
