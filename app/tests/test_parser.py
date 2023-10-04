from pprint import pprint
from ..parser import *


def test_feature_index():
    """Load and return the feature index."""
    fi = feature_index()
    assert len(fi) > 1


def test_parse_surfaces_csv():
    p = Path("/data/3DBAGplus/997_lod2_surface_areas.csv")
    res = parse_surfaces_csv(p)


def test_get_feature_surfaces():
    p = Path("/data/3DBAGplus/997_lod2_surface_areas.csv")
    surfaces_gen = parse_surfaces_csv(p)
    rec = get_feature_record("NL.IMBAG.Pand.1655100000488643-0", surfaces_gen)
    pprint(rec)


def test_find_co_path():
    res = find_co_path("NL.IMBAG.Pand.1655100000548671", "997")
    print(res)

