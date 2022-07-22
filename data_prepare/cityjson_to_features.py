"""Split a CityJSON file into CityJSONFeatures, and write them to separate files."""
import gzip
import json
from pathlib import Path

import click
import cjio, cjio.cityjson


def export2jsonl_meta(cm):
    """Export the metadata of the file."""
    j2 = {}
    j2["type"] = "CityJSON"
    j2["version"] = "1.1"
    j2["CityObjects"] = {}
    j2["vertices"] = []
    j2["transform"] = cm.j["transform"]
    if "metadata" in cm.j:
        j2["metadata"] = cm.j["metadata"]
    if "+metadata-extended" in cm.j:
        j2["+metadata-extended"] = cm.j["+metadata-extended"]
    if "extensions" in cm.j:
        j2["extensions"] = cm.j["extensions"]
    return json.dumps(j2, separators=(',', ':'))


def co_to_jsonl(cm, theid, idsdone):
    # -- take each IDs and create on CityJSONFeature
    theallowedproperties = ["type", "id", "CityObjects", "vertices", "appearance"]
    json_str = None
    if ("parents" not in cm.j["CityObjects"][theid]) and (theid not in idsdone):
        cm2 = cm.get_subset_ids([theid])
        cm2.j["type"] = "CityJSONFeature"
        cm2.j["id"] = theid
        # allp = cm2.j
        todelete = []
        for p in cm2.j:
            if p not in theallowedproperties:
                todelete.append(p)
        for p in todelete:
            del cm2.j[p]
        json_str = json.dumps(cm2.j, separators=(',', ':'))
        for theid2 in cm2.j["CityObjects"]:
            idsdone.add(theid2)
    return json_str


@click.command()
@click.argument('filename', type=click.Path(exists=True))
@click.argument('outdir', type=click.Path(exists=True))
def run(filename, outdir):
    tile_id = filename.rsplit(".")[0].rsplit("_")[3]
    with gzip.open(filename, "r") as fo:
        cm = cjio.cityjson.reader(file=fo, ignore_duplicate_keys=True)
    cm.upgrade_version("1.1", 3)
    meta_json = export2jsonl_meta(cm)
    outdir_tile = Path(outdir) / tile_id
    outdir_tile.mkdir(exist_ok=True)
    with (outdir_tile / f"meta.json").open("w") as fo:
        fo.write(meta_json)
    idsdone = set()
    for coid in cm.j["CityObjects"]:
        json_str = co_to_jsonl(cm, coid, idsdone)
        if json_str is not None:
            with (outdir_tile / f"{coid}.json").open("w") as fo:
                fo.write(json_str)


if __name__ == "__main__":
    run()