import re
import sys
from datetime import datetime
from pathlib import Path
import csv


def reduce_nginx_wfs(logfile):
    regex_date = re.compile(r"(?<=\[).*(?=\])")
    regex_wfs = re.compile(r"GetFeature")
    regex_tiles = re.compile(r"bag_tiles_3k")

    with logfile.open("r") as fo:
        date_current = None
        sum_current = 0
        bytes_sent_current = 0
        reader = csv.reader(fo, delimiter=" ", quotechar='"')
        for line in reader:
            request = line[5]
            bytes_sent_new = int(line[7])
            date_str = line[3][1:] # eg 17/Jul/2022:20:56:06
            if regex_wfs.search(request) is not None:
                # we exclude the queries to the tile index
                if regex_tiles.search(request) is None:
                    try:
                        date_new = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
                    except ValueError as e:
                        print(e)
                        continue
                    if date_current is not None:
                        if date_new.strftime("%Y-%m") == date_current.strftime("%Y-%m"):
                            sum_current += 1
                            bytes_sent_current += bytes_sent_new
                        elif date_current is not None and date_new.strftime("%Y-%m") != date_current.strftime("%Y-%m"):
                            yield date_current.strftime("%Y-%m"), sum_current, bytes_sent_current
                            sum_current = 1
                            bytes_sent_current = bytes_sent_new
                            date_current = date_new
                    else:
                        date_current = date_new
                        sum_current += 1
                        bytes_sent_current = bytes_sent_new
        yield date_current.strftime("%Y-%m"), sum_current, bytes_sent_current


def map_nginx_wfs(logdir):
    for fpath in Path(logdir).resolve().iterdir():
        if "data-download" in fpath.name:
            yield reduce_nginx_wfs(fpath)


def aggregate_nginx_wfs(logdir):
    month_count = {}
    for res in map_nginx_wfs(logdir):
        for month, count, bytes in res:
            if month in month_count:
                month_count[month][0] += count
                month_count[month][1] += bytes
            else:
                month_count[month] = [count, bytes]
    return month_count


if __name__ == "__main__":
    logdir = sys.argv[1]
    outdir = sys.argv[2]
    res = aggregate_nginx_wfs(logdir)
    with (Path(outdir).resolve() / "wfs_monthly.csv").open("w") as fo:
        writer = csv.writer(fo)
        writer.writerow(["month", "GetFeature_count", "bytes_sent_total"])
        for m in sorted(res):
            writer.writerow([m, res[m][0], res[m][1]])