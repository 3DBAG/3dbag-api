from dataclasses import dataclass
from typing import Optional, Tuple, Union
from flask import abort
import logging

DEFAULT_CRS = "http://www.opengis.net/def/crs/OGC/0/CRS84h"
STORAGE_CRS = "http://www.opengis.net/def/crs/EPSG/0/7415"

DEFAULT_BBOX = [
    3.3335406283191253,
    50.72794948839276,
    7.391791169364946,
    53.58254841348389
]


@dataclass
class Parameters:
    """ Class for holding feature parameters"""
    offset: Union[int, str]
    limit: Union[int, str]
    crs: str
    bbox_crs: str
    bbox: Optional[Tuple[float, float, float, float]] = None

    def __post_init__(self):
        try:
            self.limit = int(self.limit)
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

        if self.crs.lower() == STORAGE_CRS.lower():
            self.crs = STORAGE_CRS
        elif self.crs.lower() == DEFAULT_CRS.lower():
            self.crs = DEFAULT_CRS
        else:
            error_msg = (
                "Unknown crs %s. Must be either %s or %s",
                self.crs,
                DEFAULT_CRS,
                STORAGE_CRS)
            logging.error(error_msg)
            abort(400)

        if self.bbox_crs.lower() == STORAGE_CRS.lower():
            self.bbox_crs = STORAGE_CRS
        elif self.bbox_crs.lower() == DEFAULT_CRS.lower():
            self.bbox_crs = DEFAULT_CRS
        else:
            error_msg = (
                "Unknown bbox-crs %s. Must be either %s or %s",
                self.bbox_crs,
                DEFAULT_CRS,
                STORAGE_CRS)
            logging.error(error_msg)
            abort(400)

        try:
            if self.limit < 0:
                logging.error("Limit must be an positive integer.")
                abort(400)

            if self.bbox is not None:
                r = self.bbox.strip().strip("[]").split(',')
                if len(r) != 4:
                    logging.error("BBox needs 4 parameters.")
                    abort(400)
                self.bbox = tuple(list(map(float, r)))
            else:
                self.bbox = tuple(DEFAULT_BBOX)
        except ValueError as error:
            logging.error("Invalid parameter value: %s ", error)
            abort(400)
