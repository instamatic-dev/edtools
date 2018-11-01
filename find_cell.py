import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from collections import defaultdict
import yaml


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
    
        ax.set_ylabel("Frequency")
        if i < 3:
            xlim = latt_xlim
            ax.set_xlabel("Length ($\mathrm{\AA}$)")
        if i >=3:
            xlim = ang_xlim
            ax.set_xlabel("Angle ($\mathrm{^\circ}$)")
        
        ax.set_xlim(*xlim)
        onselect = get_spanfunc(i, ax)
        
        span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                    rectprops=dict(alpha=0.2, facecolor='red'), span_stays=True, minspan=1.0)
        
        spans[i] = span  # keep a reference in memory
        params[i] = mu, sigma
    
    plt.show()

    constants, esds = list(zip(*params.values()))

    return constants, esds


def d_calculator(uc):
    a,b,c,alpha,beta,gamma = uc
    dab = np.sqrt(a**2 + b**2 - 2*a*b*np.cos(np.deg2rad(180 - gamma)))
    dac = np.sqrt(a**2 + c**2 - 2*a*c*np.cos(np.deg2rad(180 - beta)))
    dbc = np.sqrt(b**2 + c**2 - 2*b*c*np.cos(np.deg2rad(180 - alpha)))
    return dab, dac, dbc


def unit_cell_lcv_distance(uc1, uc2):
    dab1, dac1, dbc1 = d_calculator(uc1)
    dab2, dac2, dbc2 = d_calculator(uc2)
    Mab = abs(dab1 - dab2)/min(dab1, dab2)
    Mac = abs(dac1 - dac2)/min(dac1, dac2)
    Mbc = abs(dbc1 - dbc2)/min(dbc1, dbc2)
    return max(Mab, Mac, Mbc)


def get_clusters(z, cells, distance=0.5):
    clusters = fcluster(z, distance, criterion='distance')
    grouped = defaultdict(list)
    for i, c in enumerate(clusters):
        grouped[c].append(i)
    
    print("-"*40)
    np.set_printoptions(formatter={'float': '{:7.2f}'.format})
    for i in sorted(grouped.keys()):
        cluster = grouped[i]
        clustsize = len(cluster)
        if clustsize == 1:
            del grouped[i]
            continue
        print(f"\nCluster #{i} ({clustsize} items)")
        for j in cluster:
            print(f"{j:5d}", cells[j])
        print(" ---")
        print("Mean:", np.mean(cells[cluster], axis=0))
        print(" Min:", np.min(cells[cluster], axis=0))
        print(" Max:", np.max(cells[cluster], axis=0))
    
    print("")

    return grouped


def distance_from_dendrogram(z):
    # corresponding with MATLAB behavior
    distance = round(0.7*max(z[:,2]), 4)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    tree = dendrogram(z, color_threshold=distance, ax=ax)
    ax.set_xlabel("Index")
    ax.set_ylabel("Distance (LCV)")
    ax.set_title(f"Dendrogram (cutoff={distance:.2f})")
    hline = ax.axhline(y=distance)
    
    def get_cutoff(event):
        nonlocal hline
        nonlocal tree
        nonlocal distance

        if event:
            distance = round(event.ydata, 4)
            ax.set_title(f"Dendrogram (cutoff={distance:.2f})")
            hline.remove()
            hline = ax.axhline(y=distance)
        
            for c in ax.collections:
                c.remove()

            tree = dendrogram(z, color_threshold=distance, ax=ax)

            fig.canvas.draw()
    
    fig.canvas.mpl_connect('button_press_event', get_cutoff)
    plt.show()

    return distance


def cluster_cell(cells, weights=None, distance=None, method="average"):
    from scipy.spatial.distance import pdist

    dist = pdist(cells, metric=unit_cell_lcv_distance)

    z = linkage(dist,  metric='euclidean', method=method)

    if not distance:
        distance = distance_from_dendrogram(z)

    print(f"Linkage method = {method}")
    print(f"Cutoff distance = {distance}")
    print("")

    return get_clusters(z, cells, distance=distance)


def main():
    import argparse

    description = "Program for finding the unit cell from a serial crystallography experiment."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
        
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="Path to CELLPARM.INP")

    parser.add_argument("-b","--binsize",
                        action="store", type=float, dest="binsize",
                        help="Binsize for the histogram, default=0.5")

    parser.add_argument("-c","--cluster",
                        action="store_true", dest="cluster",
                        help="Apply cluster analysis")

    parser.add_argument("-d","--distance",
                        action="store", type=float, dest="distance",
                        help="Cutoff distance to use for clustering, bypass dendrogram")

    parser.add_argument("-m","--method",
                        action="store", type=str, dest="method",
                        choices="single average complete median weighted centroid ward".split(),
                        help="Method for calculating the clustering distance (see `scipy.cluster.hierarchy.linkage`)")


    parser.set_defaults(binsize=0.5,
                        cluster=False,
                        distance=None)
    
    options = parser.parse_args()

    distance = options.distance
    binsize = options.binsize
    cluster = options.cluster
    args = options.args

    if args:
        fn = args[0]
    else:
        fn = "cells.yaml"

    ds = yaml.load(open(fn, "r"))

    cells = np.array([d["raw_unit_cell"] for d in ds])
    weights = np.array([d["weight"] for d in ds])

    if cluster:
        clusters = cluster_cell(cells, weights=weights, distance=distance)
        for i, idx in clusters.items():
            clustered_ds = [ds[i] for i in idx]
            fout = f"cells_cluster_{i}_{len(idx)}-items.yaml"
            yaml.dump(clustered_ds, open(fout, "w"))
            print(f"Wrote cluster {i} to file `{fout}`")
    
    else:
        constants, esds = find_cell(cells, weights, binsize=binsize)
        
        print()
        print("Weighted mean of histogram analysis")
        print("---")
        print("Unit cell parameters: ", end="")
        for c in constants:
            print(f"{c:8.3f}", end="")
        print()
        print("Unit cell esds:       ", end="")
        for e in esds:
            print(f"{e:8.3f}", end="")
        print()
        print()
        print("UNIT_CELL_CONSTANTS= " + " ".join(f"{val:.3f}" for val in constants))


if __name__ == '__main__':
    main()
