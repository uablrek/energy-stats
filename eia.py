#!/usr/bin/env python
"""
Extract and plot energy and financial statistics.

Data is downloaded from:
  * U.S Energy Information Adminisration, https://www.eia.gov/
  * https://data.worldbank.org/indicator/NY.GDP.MKTP.CD

Data-files should be stored in ./data/ for offline post-processing.
"""
import sys
import getopt
import argparse
import requests
import os
import json
import slplot
import csv
dbg = lambda *arg: 0

# Constants
eia = "https://api.eia.gov/v2/"
brics=["CHN","IND","RUS","ZAF","IRN","EGY","ETH","ARE","IDN"]
# This is extracted from NY.GDP.MKTP.CD, which is downloaded as zip
world_bank_csv = "data/world-bank.csv"


def mkurl(route, start=1966):
    key = os.environ["EIA_KEY"]
    url = eia + route + f"?api_key={key}"
    url += f"&frequency=annual&data[0]=value&start={start}-01-01&end=2025-01-01"
    return url
def facets(name, *values):
    s = ""
    for v in values:
        s += f"&facets[{name}][]={v}"
    return s

def read_data(file, region="WORL", start=1966):
    with open(file, 'r') as f:
        resp = json.load(f)
    data = resp['response']['data']
    X = []
    Y = []
    for d in data:
        if d['countryRegionId'] != region:
            continue
        year = int(d['period'])
        if year < start:
            continue
        X.append(int(d['period']))
        Y.append(float(d['value']))
    return X, Y

def sum_data(file, regions, start=1966):
    with open(file, 'r') as f:
        resp = json.load(f)
    data = resp['response']['data']
    X = []
    Y = []
    # We assume that year (period) is chronological
    for d in data:
        if not d['countryRegionId'] in regions:
            continue
        year = int(d['period'])
        if not X or year > X[-1]:
            X.append(int(d['period']))
            Y.append(float(d['value']))
        else:
            Y[-1] += float(d['value'])
    return X, Y


def gdp(country, start=2000, end=2024):
    X = []
    Y = []
    val = []
    with open(world_bank_csv, newline='') as csvfile:
        rdr = csv.DictReader(csvfile)
        for row in rdr:
            if row['Series Name'] != 'GDP (current US$)':
                continue
            if row['Country Name'] != country:
                continue
            break
    for year in range(start, end+1):
        X.append(year)
        k = f"{year} [YR{year}]"
        Y.append(float(row[k]))
    return X, Y

# Normalize to the first value (which will get = 1.0)
def normalize(Y, pivot=0):
    if pivot == 0:
        pivot = Y[0]
    return [x/pivot for x in Y]

# https://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function
# for current func name, specify 0 or no argument.
# for name of caller of current func, specify 1.
# for name of caller of caller of current func, specify 2. etc.
currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name
def arg_parser():
    fn = currentFuncName(1)
    prog=fn.removeprefix("cmd_")
    doc=globals()[fn].__doc__
    return argparse.ArgumentParser(prog=prog, description=doc)

# ----------------------------------------------------------------------
# Commands;

def cmd_routes(args):
    """Print "routes" in a response from EIA"""
    parser = arg_parser()
    parser.add_argument('--file', default="-", help="File with response")
    args = parser.parse_args(args[1:])
    with open(args.file, 'r') as f:
        data = json.load(f)
    r = data['response']
    if not 'routes' in r:
        return 1
    for route in r['routes']:
        print(route['id'])
    return 0

def cmd_facets(args):
    """Print "facets" in a response from EIA"""
    parser = arg_parser()
    parser.add_argument('--file', default="-", help="File with response")
    args = parser.parse_args(args[1:])
    with open(args.file, 'r') as f:
        data = json.load(f)
    r = data['response']
    if not 'facets' in r:
        return 1
    for f in r['facets']:
        print(f"{f['id']} - {f['name']}")

def cmd_get_info(args):
    """Get info about an EIA object.

    The raw response (json) is printed. Only meta-data is downloaded
    """
    parser = arg_parser()
    parser.add_argument('--route', default="", help="Object route")
    args = parser.parse_args(args[1:])
    r = requests.get(mkurl(args.route))
    print(r.text)
    return 0

def cmd_get_energy_data(args):
    """Download energy data for a number of regions"""
    arg_parser().parse_args(args[1:])
    url = mkurl("international/data")
    url += facets(
        "countryRegionId","CHN","EU27","IND","OECD","USA","WP21","WORL")
    url += facets("activityId", "2")
    url += facets("productId", "44")
    url += facets("unit", "MTOE")
    r = requests.get(url)
    print(r.text)
    return 0

def cmd_get_energy_data_brics(args):
    """Download energy data for the BRICS+ countries"""
    arg_parser().parse_args(args[1:])
    url = mkurl("international/data", 2000)
    url += facets("countryRegionId", *brics)
    url += facets("activityId", "2")
    url += facets("productId", "44")
    url += facets("unit", "MTOE")
    r = requests.get(url)
    print(r.text)
    return 0

def cmd_plot_energy_regions(args):
    """Plot Consumption of Primary energy for regions"""
    arg_parser().parse_args(args[1:])
    lim=(0,7000)
    X, Y = read_data("data/energyConsumption", "CHN")
    CHN =  slplot.Axis("China", "MToe", Y, lim)
    _, Y = read_data("data/energyConsumption", "USA")
    USA =  slplot.Axis("USA", "MToe", Y, lim)
    _, Y = read_data("data/energyConsumption", "WP21")
    WP21 = slplot.Axis("Western Europe", "MToe", Y, lim)
    _, Y = read_data("data/energyConsumption", "OECD")
    OECD = slplot.Axis("OECD", "MToe", Y, lim)
    X, Y = read_data("data/energyConsumption", "IND")
    IND = slplot.Axis("India", "MToe", Y, lim)
    x = slplot.Axis("Year", values=X)
    slplot.plot(x, [CHN,USA,WP21,OECD,IND], title="Primary energy")
    return 0

def cmd_plot_energy_brics(args):
    """Plot Consumption of Primary energy for BRICS+ and OSCD"""
    arg_parser().parse_args(args[1:])
    lim=(0,7000)
    X, Y = read_data("data/energyConsumption", "OECD", 2001)
    OECD =  slplot.Axis("OECD", "MToe", Y, lim)
    _, Y = sum_data("data/energyConsumptionBRICS", brics)
    BRICS = slplot.Axis("BRICS", "MToe", Y, lim)
    x = slplot.Axis("Year", values=X)
    slplot.plot(x, [OECD,BRICS], title="Primary energy")
    return 0

def cmd_world_bank_data(args):
    """Print info about a csv file from world-bank"""
    parser = arg_parser()
    parser.add_argument('--key', default="", help="Key to examine")
    args = parser.parse_args(args[1:])
    val = []
    with open(world_bank_csv, newline='') as csvfile:
        rdr = csv.DictReader(csvfile)
        for row in rdr:
            if not args.key:
                val = row.keys()
                break
            v = row[args.key]
            if not v in val:
                val.append(v)
    for v in val:
        print(v)
    return 0

def cmd_plot_gdp(args):
    """Plot GDP the world"""
    arg_parser().parse_args(args[1:])
    X, Y = gdp("World")
    x = slplot.Axis("Year", values=X)
    y1 = slplot.Axis("GDP", "US$", Y, lim=(0, 140e12), formatter=slplot.engfmt)
    slplot.plot(x, [y1], title="GDP for the World")
    return 0

def cmd_plot_gdp_world(args):
    """Plot GDP and Energy for the world relative to y2000"""
    arg_parser().parse_args(args[1:])
    X, Y = gdp("World", end=2023)
    x = slplot.Axis("Year", values=X)
    y1 = slplot.Axis("GDP", "relative to y2000", normalize(Y), lim=(0,4))
    _, Y = read_data("data/energyConsumption", start=2000)
    y2 = slplot.Axis("Energy", "relative to y2000", normalize(Y), lim=(0,4))
    slplot.plot(x, [y1, y2], title="GDP v.s. Energy for the World")
    return 0

def cmd_plot_gdp_chn(args):
    """Plot GDP and Energy for China relative to y2000"""
    arg_parser().parse_args(args[1:])
    lim=(0,20)
    X, Y = gdp("China", end=2023)
    x = slplot.Axis("Year", values=X)
    y1 = slplot.Axis("GDP", "relative to y2000", normalize(Y), lim=lim)
    _, Y = read_data("data/energyConsumption", "CHN", start=2000)
    y2 = slplot.Axis("Energy", "relative to y2000", normalize(Y), lim=lim)
    slplot.plot(x, [y1, y2], title="GDP v.s. Energy for China")
    return 0

def cmd_plot_gdp_usa(args):
    """Plot GDP and Energy for USA relative to y2000"""
    arg_parser().parse_args(args[1:])
    lim=(0,3)
    X, Y = gdp("United States", end=2023)
    x = slplot.Axis("Year", values=X)
    y1 = slplot.Axis("GDP", "relative to y2000", normalize(Y), lim=lim)
    _, Y = read_data("data/energyConsumption", "USA", start=2000)
    y2 = slplot.Axis("Energy", "relative to y2000", normalize(Y), lim=lim)
    slplot.plot(x, [y1, y2], title="GDP v.s. Energy for USA")
    return 0

def cmd_plot_gdp_usa_chn(args):
    """Plot GDP and Energy for USA and China relative to US-y2000"""
    arg_parser().parse_args(args[1:])
    lim=(0,3)
    X, Y = gdp("United States", end=2023)
    x = slplot.Axis("Year", values=X)
    _, Yc = gdp("China", end=2023)
    p = Y[0]
    y1 = slplot.Axis(
        "GDP", "relative to US-y2000", normalize(Y, pivot=p), lim=lim,
        cvalues=normalize(Yc, pivot=p))
    _, Y = read_data("data/energyConsumption", "USA", start=2000)
    _, Yc = read_data("data/energyConsumption", "CHN", start=2000)
    p = Y[0]
    y2 = slplot.Axis(
        "Energy", "relative to US-y2000", normalize(Y, pivot=p), lim=lim,
        cvalues=normalize(Yc, pivot=p))
    
    slplot.plot(x, [y1,y2], title="GDP v.s. Energy for USA and China (dashed)")
    return 0

# ----------------------------------------------------------------------
# Parse args

def parse_args():
    cmdfn = [n for n in globals() if n.startswith('cmd_')]
    cmds = [x.removeprefix('cmd_') for x in cmdfn]

    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('-v', action='count', default=0, help="verbose")
    parser.add_argument('cmd', choices=cmds, nargs=argparse.REMAINDER)
    args = parser.parse_args()

    global dbg
    if args.v:
        dbg = getattr(__builtins__, 'print')
    dbg("Program starting", args, cmds)

    # Why is this necessary? Bug?
    if not args.cmd:
        print(__doc__)
        print("Sub-commands:")
        for c in cmds:
            print("  ", c)
            print("    ", globals()["cmd_"+c].__doc__.splitlines()[0])
        sys.exit(0)
    if args.cmd[0] not in cmds:
        print("Invalid command")
        sys.exit(1)

    cmd_function = globals()["cmd_" + args.cmd[0]]
    sys.exit(cmd_function(args.cmd))


if __name__ == '__main__':
    parse_args()
