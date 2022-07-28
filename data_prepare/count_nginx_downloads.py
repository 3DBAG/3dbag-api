import re
import sys
from datetime import datetime
from pathlib import Path
import csv
import json


def reduce_nginx_downloads(logfile, tile_count, fformat):
    if fformat == "cityjson":
        fformat_extension = ".json"
    elif fformat == "gpkg":
        fformat_extension = ".gpkg"
    elif fformat == "obj":
        fformat_extension = ".zip"
    elif fformat == "postgres":
        fformat_extension = ".zip"
    else:
        raise ValueError(f"Unknown file format {fformat}")

    regex_fformat = re.compile(fr"GET /{fformat}")
    regex_tile = re.compile(f"\\d{{1,4}}(?=\\{fformat_extension})")

    with logfile.open("r") as fo:
        date_current = None
        sum_current = 0
        sum_features_current = 0
        bytes_sent_current = 0
        reader = csv.reader(fo, delimiter=" ", quotechar='"')
        for line in reader:
            request = line[5]
            bytes_sent_new = int(line[7])
            date_str = line[3][1:] # eg 17/Jul/2022:20:56:06
            fformat_match = regex_fformat.search(request)
            if fformat_match is not None:
                tile_match = regex_tile.search(request)
                # only count the features in a tile for cityjson files
                if fformat == "cityjson":
                    if tile_match is None:
                        print(f"Didn't get a tile match on {request}")
                        continue
                    else:
                        try:
                            features_in_tile = tile_count[tile_match[0]]
                        except KeyError:
                            print(f"Didn't find tile {tile_match[0]} in the tile counts")
                            continue
                else:
                    features_in_tile = 0
                try:
                    date_new = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
                except ValueError as e:
                    print(e)
                    continue
                if date_current is not None:
                    if date_new.strftime("%Y-%m") == date_current.strftime("%Y-%m"):
                        sum_current += 1
                        bytes_sent_current += bytes_sent_new
                        sum_features_current += features_in_tile
                    elif date_current is not None and date_new.strftime("%Y-%m") != date_current.strftime("%Y-%m"):
                        yield date_current.strftime("%Y-%m"), sum_current, bytes_sent_current, sum_features_current
                        sum_current = 1
                        date_current = date_new
                        bytes_sent_current = bytes_sent_new
                        sum_features_current = features_in_tile
                else:
                    date_current = date_new
                    sum_current += 1
                    bytes_sent_current = bytes_sent_new
                    sum_features_current = features_in_tile
        if date_current is not None:
            yield date_current.strftime("%Y-%m"), sum_current, bytes_sent_current, sum_features_current


def map_nginx_downloads(logdir, tile_count, fformat):
    for fpath in Path(logdir).resolve().iterdir():
        if "data-download" in fpath.name:
            yield reduce_nginx_downloads(fpath, tile_count, fformat)


def aggregate_nginx_downloads(logdir, tile_count, fformat):
    month_count = {}
    for res in map_nginx_downloads(logdir, tile_count, fformat):
        for month, count, bytes, features in res:
            if month in month_count:
                month_count[month][0] += count
                month_count[month][1] += bytes
                month_count[month][2] += features
            else:
                month_count[month] = [count, bytes, features]
    return month_count


if __name__ == "__main__":
    logdir = sys.argv[1]
    outdir = sys.argv[2]
    tcpath = sys.argv[3]
    fformat = sys.argv[4]

    # database query dump of tile_id: feature_cnt in json format
    with Path(tcpath).resolve().open("r") as fo:
        tilecount = {i["tile_id"]: i["cnt"] for i in json.load(fo)}

    res = aggregate_nginx_downloads(logdir, tilecount, fformat)
    with (Path(outdir).resolve() / f"{fformat}_monthly.csv").open("w") as fo:
        writer = csv.writer(fo)
        if fformat == "cityjson":
            writer.writerow(["month", "3dtiles_count", "bytes_sent_total", "features_total"])
            for m in sorted(res):
                writer.writerow([m, res[m][0], res[m][1], res[m][2]])
        else:
            writer.writerow(["month", "3dtiles_count", "bytes_sent_total"])
            for m in sorted(res):
                writer.writerow([m, res[m][0], res[m][1]])