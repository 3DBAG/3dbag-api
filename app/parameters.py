from dataclasses import dataclass
from typing import Optional, Tuple
from flask import Request, abort
import logging

DEFAULT_CRS = "http://www.opengis.net/def/crs/OGC/0/CRS84h"
STORAGE_CRS = "http://www.opengis.net/def/crs/EPSG/0/7415"


@dataclass
class Parameters:
    """ Class for holding feature parameters"""
    offset: int
    limit: int
    crs: str
    bbox_crs: str
    bbox: Optional[Tuple[float, float, float, float]] = None

    def __post_init__(self):
        if self.crs.lower() == STORAGE_CRS.lower():
            self.crs = STORAGE_CRS
        elif self.crs.lower() == DEFAULT_CRS.lower():
            self.crs = DEFAULT_CRS
        else:
            logging.error(
                "Unknown crs %s. Must be either %s or %s",
                self.crs,
                DEFAULT_CRS,
                STORAGE_CRS)
            abort(400)

        if self.bbox_crs.lower() == STORAGE_CRS.lower():
            self.bbox_crs = STORAGE_CRS
        elif self.bbox_crs.lower() == DEFAULT_CRS.lower():
            self.bbox_crs = DEFAULT_CRS
        else:
            logging.error(
                "Unknown bbox-crs %s. Must be either %s or %s",
                self.bbox_crs,
                DEFAULT_CRS,
                STORAGE_CRS)
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
        except ValueError as error:
            logging.error("Invalid parameter value")
            logging.error(error)
            abort(400)