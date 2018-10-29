import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import sys


def weighted_average(values, weights=None):
    """Returns weighted mean and standard deviation"""
    mean = np.average(values, weights=weights)
    variance = np.average((values - mean)**2, weights=weights)
    std = np.sqrt(variance)
    return mean, std


def parse_cellparm(fn):
    cells = []
    weights = []
    
    with open(fn, "r") as f:
        for line in f:
            line = line.strip().rsplit("!")[0].upper()
            if not line:
                continue
            line = line.replace("=", "")
            line = line.split()
            i = line.index("UNIT_CELL_CONSTANTS")
            cell = [float(val) for val in line[i+1:i+7]]
            try:
                j = line.index("WEIGHT")
                weight = int(line[j+1])
            except ValueError:
                weight = 1
            
            cells.append(cell)
            weights.append(weight)

    print(f"Loaded {len(cells)} unit cells from file {fn}")
    cells = np.array(cells)
    weights = np.array(weights)

    return cells, weights


def find_cell(cells, weights, binsize=0.5):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    ang_par = cells[:,3:6]
    ang_xlim = int(np.percentile(ang_par, 5)) - 2, int(np.percentile(ang_par, 95)) + 2
    
    latt_parr = cells[:,0:3]
    latt_xlim = int(np.percentile(latt_parr, 5)) - 2, int(np.percentile(latt_parr, 95)) + 2
    
    spans = {}
    lines = {}
    variables  = {}
    names = "a b c \\alpha \\beta \\gamma".split()
    params = {}
    
    def get_spanfunc(i, ax):
        def onselect(xmin, xmax):
            # print(i, xmin, xmax)
            update(i, ax, xmin, xmax)
            fig.canvas.draw()
        return onselect
    
    def update(i, ax, xmin, xmax):
        par, bins = variables[i]
        idx = (par > xmin) & (par < xmax)
        sel_par = par[idx]
        sel_w = weights[idx]
        if len(sel_par) == 0:
            return 0, 0
        mu, sigma = weighted_average(sel_par, sel_w)
        x = np.arange(xmin-10, xmax+10, binsize/2)
        y = stats.norm.pdf(x, mu, sigma)
        if i in lines:
            for item in lines[i]:
                item.remove()
        l = ax.plot(x, y, 'r--', linewidth=1.5)
        lines[i] = l
        name = names[i]
        ax.set_title(f"${name}$: $\mu={mu:.2f}$, $\sigma={sigma:.2f}$")
        params[i] = mu, sigma
        return mu, sigma
    
    for i in range(6):
        ax = axes[i]
        
        par = cells[:,i]
    
        median = np.median(par)
        bins = np.arange(0, max(par), binsize)
        n, bins, patches = ax.hist(par, bins, rwidth=0.8, density=True)
        
        variables[i] = par, bins
    
        mu, sigma = update(i, ax, median-2, median+2)
    
        if i < 3:
            xlim = latt_xlim
        if i >=3:
            xlim = ang_xlim
        
        ax.set_xlim(*xlim)
        onselect = get_spanfunc(i, ax)
        
        span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                    rectprops=dict(alpha=0.5, facecolor='red'), span_stays=True, minspan=1.0)
        
        spans[i] = span  # keep a reference in memory
        params[i] = mu, sigma
    
    plt.show()

    constants, esds = list(zip(*params.values()))

    return constants, esds


def main():
    binsize = 0.5
    
    args = sys.argv[1:]
    if args:
        fn = args[1]
    else:
        fn = "CELLPARM.INP"
    
    cells, weights = parse_cellparm(fn)
    
    constants, esds = find_cell(cells, weights, binsize=binsize)
    
    print()
    print("Unit cell parameters: ", end="")
    for c in constants:
        print(f"{c:8.2f}", end="")
    print()
    print("Unit cell esds:       ", end="")
    for e in esds:
        print(f"{e:8.2f}", end="")
    print()
    print()
    print("UNIT_CELL_CONSTANTS= " + " ".join(f"{val:.2f}" for val in constants))


if __name__ == '__main__':
    main()
