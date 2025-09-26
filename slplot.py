#!/usr/bin/env python
"""
Provides a very simple line plot function using "matplotlib".
The function allows multiple Y-axis with individual value ranges, and
optionally a secondary line (dashed) for comparison.

The plot is displayed and let the user save with the built-in save function.
Simple animations are possible.

The __main__ function in this file serves as test and example.
"""

# https://matplotlib.org/stable/gallery/spines/multiple_yaxis_with_spines.html
# https://matplotlib.org/stable/gallery/text_labels_and_annotations/engineering_formatter.html

import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
from typing import NamedTuple

engfmt = EngFormatter(places=1, sep="\N{THIN SPACE}")

class Axis(NamedTuple):
    """
    Describes an axis. The X-axis uses only values and title.
    The length of the values (and cvalues) *must* be the same for
    all axis in the plot. However, value items may be None.
    """
    title: str = ""
    unit: str = ""
    values: [any] = []
    lim: any = None
    # Offset from the previous Y-axis
    y_offset: int = 50
    formatter: any = None
    cvalues: [any] = []

# x: Axis, y: Axis[]
def plot(x, y, title=None, size=(10,5), show=True):
    """
    Create a line plot with multiple Y-axis.

    :param x: The X-axis. Only values and title are used
    :param y: An array of Y-axis
    :param title: The title of the figure
    :param size: Size of the figure (inches)
    :param show: If the plot should be shown. Set to False for automatic saves and animations
    """
    fig = plt.gcf()         # (Get Current Figure)
    fig.set_size_inches(size)
    fig.clear()
    if title:
        fig.suptitle(title)
    ax = plt.axes()
    ax.set(xlabel=x.title)
    ax.grid(axis='x', linestyle=':')
    offset = 0
    for i, Y in enumerate(y):
        if i > 1:
            offset += Y.y_offset
        plotY(ax, x.values, Y, i, offset)
    fig.tight_layout()
    if show:
        plt.show()

def plotY(ax, vx, y, i, offset):
    """
    Internal function. Adds an Y-axis
    """
    if i > 0:
        ax = ax.twinx()
        ax.spines['right'].set_position(("outward", offset))
    if y.lim:
        ax.set_ylim(y.lim)
    if y.formatter:
        ax.yaxis.set_major_formatter(y.formatter)
    if y.unit:
        ax.set(ylabel=f'{y.title} ({y.unit})')
    else:
        ax.set(ylabel=f'{y.title}')
    p, = ax.plot(vx, y.values, f'C{i}')
    ax.yaxis.label.set_color(p.get_color())
    ax.tick_params(axis='y', colors=p.get_color())
    # Compare values
    if y.cvalues:
        ax.plot(vx, y.cvalues, f'C{i}--', linewidth=0.5)


if __name__ == '__main__':
    import os
    match os.getenv("SLPLOT_TEST", ""):
        case "incomplete":
            # Y-values may not exist for certain X-values
            x = Axis("Year", values=[1960,1970,1980,1990,2000,2010])
            y1 = Axis("USSR", "mtoe", [10,40,45,30,None,None],(0,100))
            y2 = Axis("USA", "mtoe", [60,50,65,65,68,72],(0,100))
            plot(x, [y1,y2], title="Incomplete values")
        case _:
            x = Axis("Year", values=[2020,2021,2022,2023,2024])
            # Plot compare values
            y1 = Axis("Apples", "ton", [5,5,3,6,10],(0,12),cvalues=[4,6,3,7,5])
            # Very high values looks weird without a formatter.
            y2 = Axis(
                "High values", "#", [4e8,5.4e8,2e8,7e7,8e7], formatter=engfmt)
            # The strings may require a higher y_offset for the next axis
            y3 = Axis("Energy", "mtoe", [10,40,45,20,30],(0,100), y_offset=65)
            plot(x, [y1, y2, y3], title="Basic test")

