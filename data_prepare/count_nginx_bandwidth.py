import re
import sys
from datetime import datetime
from pathlib import Path
import csv
import json


def reduce_nginx_bytes_sent(logfile):
    with logfile.open("r") as fo:
        date_current = None
        bytes_sent_current = 0
        reader = csv.reader(fo, delimiter=" ", quotechar='"')
        for line in reader:
            bytes_sent_new = int(line[7])
            date_str = line[3][1:]  # eg 17/Jul/2022:20:56:06
            try:
                date_new = datetime.strptime(date_str, "%d/%b/%Y:%H:%M:%S")
            except ValueError as e:
                print(e)
                continue
            if date_current is not None:
                if date_new.strftime("%Y-%m") == date_current.strftime("%Y-%m"):
                    bytes_sent_current += bytes_sent_new
                elif date_current is not None and date_new.strftime(
                        "%Y-%m") != date_current.strftime("%Y-%m"):
                    yield date_current.strftime(
                        "%Y-%m"), bytes_sent_current
                    date_current = date_new
                    bytes_sent_current = bytes_sent_new
            else:
                date_current = date_new
                bytes_sent_current = bytes_sent_new
        yield date_current.strftime("%Y-%m"), bytes_sent_current


def map_nginx_bytes_sent(logdir):
    for fpath in Path(logdir).resolve().iterdir():
        if "viewer" in fpath.name or "data-download" in fpath.name:
            yield reduce_nginx_bytes_sent(fpath)


def aggregate_nginx_bytes_sent(logdir):
    month_count = {}
    for res in map_nginx_bytes_sent(logdir):
        for month, bytes in res:
            if month in month_count:
                month_count[month] += bytes
            else:
                month_count[month] = bytes
    return month_count


if __name__ == "__main__":
    logdir = sys.argv[1]
    outdir = sys.argv[2]

    res = aggregate_nginx_bytes_sent(logdir)
    with (Path(outdir).resolve() / "bytes_monthly.csv").open("w") as fo:
        writer = csv.writer(fo)
        writer.writerow(["month", "bytes_sent_total"])
        for m in sorted(res):
            writer.writerow([m, res[m]])