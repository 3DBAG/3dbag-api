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
        ip_counts = {}
        reader = csv.reader(fo, delimiter=" ", quotechar='"')
        for line in reader:
            ip_addr = line[0]
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
                            if ip_addr not in ip_counts:
                                ip_counts[ip_addr] = [1, bytes_sent_new]
                            else:
                                ip_counts[ip_addr][0] += 1
                                ip_counts[ip_addr][1] += bytes_sent_new
                        elif date_current is not None and date_new.strftime("%Y-%m") != date_current.strftime("%Y-%m"):
                            for ip, ipcnt in ip_counts.items():
                                yield date_current.strftime("%Y-%m"), ip, ipcnt[0], ipcnt[1]
                            ip_counts = {}
                            date_current = date_new
                    else:
                        date_current = date_new
                        ip_counts[ip_addr] = [1, bytes_sent_new]
        for ip, ipcnt in ip_counts.items():
            yield date_current.strftime("%Y-%m"), ip, ipcnt[0], ipcnt[1]


def map_nginx_wfs(logdir):
    for fpath in Path(logdir).resolve().iterdir():
        if "data-download" in fpath.name:
            yield reduce_nginx_wfs(fpath)


def aggregate_nginx_wfs(logdir):
    month_count = []
    return [(month, ip, count, bytes) for res in map_nginx_wfs(logdir) for month, ip, count, bytes in res]
    #     for month, count, bytes, ip, ipcnt in res:
    #         if month in month_count:
    #             month_count[month][0] += count
    #             month_count[month][1] += bytes
    #             month_count[month][2] += bytes
    #             month_count[month][1] += bytes
    #         else:
    #             month_count[month] = [count, bytes, ip, ipcnt]
    # return month_count


if __name__ == "__main__":
    logdir = sys.argv[1]
    outdir = sys.argv[2]
    res = aggregate_nginx_wfs(logdir)
    with (Path(outdir).resolve() / "wfs_monthly.csv").open("w") as fo:
        writer = csv.writer(fo, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(["month", "ip", "GetFeature_count", "bytes_sent_total"])
        for m in res:
            writer.writerow(m)