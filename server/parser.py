import csv
import json
from pathlib import Path


def get_parent_id(featureId):
    # Get the ID of the parent feature if it is a BuildinPart,
    # like NL.IMBAG.Pand.1655100000488643-0, because the feature_index only
    # contains the parent IDs.
    return featureId.rsplit("-")[0]


def get_tile_id(parent_id, feature_index):
    """Get the tile_id for a feature."""
    try:
        return feature_index[parent_id]
    except KeyError:
        return None


def feature_index():
    """Returns the feature-tile index of the 3D BAG."""
    p = "/data/3DBAGplus/bag_index_997.json"
    with open(p, "r") as fo:
        return dict((d["identificatie"], d["tile_id"]) for d in json.load(fo))


def find_surfaces_csv_path(tile_id):
    """Return the file path of the CSV file containing the surfaces record for tile_id.

    :returns: Absolute path to CSV file.
    """
    base = Path("/data/3DBAGplus").resolve()
    return base.joinpath(f"{tile_id}_lod2_surface_areas.csv")


def find_addresses_csv_path(tile_id):
    """Return the file path of the CSV file containing the addresses record for tile_id.

    :returns: Absolute path to CSV file.
    """
    base = Path("/data/3DBAGplus").resolve()
    return base.joinpath(f"{tile_id}_lod2_surface_areas_addr.csv")


def parse_surfaces_csv(path: Path):
    """Parse a CSV file containing the surfaces data.

    :returns: A generator over the surfaces data.
    """
    if not path.exists:
        raise FileNotFoundError
    with path.open("r") as fo:
        for row in csv.DictReader(fo):
            yield row["id"], row


def parse_addresses_csv(path: Path):
    """Parse a CSV file containing the addresses data.

    :returns: A generator over the addresses data.
    """
    if not path.exists:
        raise FileNotFoundError
    with path.open("r") as fo:
        for row in csv.DictReader(fo):
            yield row["identificatie_pand"], row


def get_feature_record(featureId, record_gen):
    """Get the record of the feature with featureId."""
    for rec_id, rec in record_gen:
        if rec_id == featureId:
            return rec
