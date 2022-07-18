import csv
import json
from pathlib import Path


def feature_index():
    """Returns the feature-tile index of the 3D BAG."""
    p = "/data/3DBAGplus/bag_index_997.json"
    with open(p, "r") as fo:
        return dict((d["identificatie"], d["tile_id"]) for d in json.load(fo))


def find_surfaces_csv_path(featureId, feature_index):
    """Return the file path of the CSV file containing the surfaces record for
    feature with featureId.

    :returns: Absolute path to CSV file.
    """
    base = Path("/data/3DBAGplus").resolve()
    try:
        tile_id = feature_index[featureId]
        return base.joinpath(f"{tile_id}_lod2_surface_areas.csv")
    except KeyError:
        return None



def parse_surfaces_csv(path: Path):
    """Parse a CSV file containing the surfaces data.

    :returns: A collection with the surfaces data.
    """
    if not path.exists:
        raise FileNotFoundError
    with path.open("r") as fo:
        for row in csv.DictReader(fo):
            yield row["id"], row



def get_feature_surfaces(featureId, surfaces_gen):
    """Get the surfaces record of the feature with featureId."""
    for rec_id, rec in surfaces_gen:
        if rec_id == featureId:
            return rec