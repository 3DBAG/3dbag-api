import re
import sys
from datetime import datetime
from pathlib import Path
import csv
import concurrent.futures


def reduce_nginx_wfs(logfile):
    regex_date = re.compile(r"(?<=\[).*(?=\])")
    regex_wfs = re.compile(r"GetFeature")
    regex_tiles = re.compile(r"bag_tiles_3k")

    with logfile.open("r") as fo:
        date_current = None
        sum_current = 0
        for line in fo:
            if regex_wfs.search(line) is not None:
                # we exclude the queries to the tile index
                if regex_tiles.search(line) is None:
                    # remove the timezone because we just need the month anyway
                    date_str = regex_date.search(line)[0].split()[0]
                    try:
                        date_new = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
                    except ValueError as e:
                        print(e)
                        continue
                    if date_current is not None:
                        if date_new.strftime("%Y-%m") == date_current.strftime("%Y-%m"):
                            sum_current += 1
                        elif date_current is not None and date_new.strftime("%Y-%m") != date_current.strftime("%Y-%m"):
                            yield date_current.strftime("%Y-%m"), sum_current
                            sum_current = 1
                            date_current = date_new
                    else:
                        date_current = date_new
                        sum_current += 1
        yield date_current.strftime("%Y-%m"), sum_current


def map_nginx_wfs(logdir):
    for fpath in Path(logdir).resolve().iterdir():
        if "data-download" in fpath.name:
            yield reduce_nginx_wfs(fpath)


def aggregate_nginx_wfs(logdir):
    month_count = {}
    for res in map_nginx_wfs(logdir):
        for month, count in res:
            try:
                month_count[month] += count
            except KeyError:
                month_count[month] = count
    return month_count


if __name__ == "__main__":
    logdir = sys.argv[1]
    outdir = sys.argv[2]
    res = aggregate_nginx_wfs(logdir)
    with (Path(outdir).resolve() / "wfs_monthly.csv").open("w") as fo:
        writer = csv.writer(fo)
        writer.writerow(["month", "count"])
        for m in sorted(res):
            writer.writerow([m, res[m]])