from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from collections import defaultdict
from pathlib import Path
import shutil
import subprocess as sp
import numpy as np
import matplotlib.pyplot as plt


xscale_keys = (
'd_min',
'N_obs',
'N_uniq',
'N_possible',
'Completeness',
#'R_obs',
#'R_exp',
'N_comp',
'i/sigma',
'R_meas',
'CC(1/2)',
)


def clean_params(inp):
    return [
    float(inp[0]),                          # d_min
    int(inp[1]),                            # N_obs
    int(inp[2]),                            # N_uniq
    int(inp[3]),                            # N_possible
    float(inp[4].replace("%", "")),  # Completeness
    # 0.01 * float(inp[5].replace("%", "")),  # R_obs
    # 0.01 * float(inp[6].replace("%", "")),  # R_exp
    int(inp[7]),                            # N_comp
    float(inp[8]),                          # i/sigma
    0.01 * float(inp[9].replace("%", "")),  # R_meas
    float(inp[10].replace("*", ""))         # CC(1/2)
    ]


def parse_xscale_lp(fn):
    f = open(fn, "r")
    
    d = {}
    
    prev = ""
    
    for line in f:
        if line.startswith("    total"):
            inp = line.split()
            inp[0] = prev.split()[0]
            inp = clean_params(inp)
            
            d = dict(zip(xscale_keys, inp))
            break
        prev = line
    return d


def run_xscale(clusters, cell, spgr):
    results = []
    
    keys = sorted(clusters.keys())
    
    for i in keys:
        item = clusters[i]
        
        fns = item["files"]
        drc = Path(f"cluster_{i}")
        drc.mkdir(parents=True, exist_ok=True)
    
        f = open(drc / "XSCALE.INP", "w")
    
        print(f"! Clustered data from {item['n_clust']} data sets", file=f)
        print(f"! Cluster score: {item['score']:.3f}", file=f)
        print(f"! Cluster CC(I): {item['CC(I)']:.3f}", file=f)
        print(f"! Cluster items: {item['clust']}", file=f)
        print(f"! Cluster distance cutoff: {item['distance_cutoff']}", file=f)
        print(f"! Cluster method: {item['method']}", file=f)
        print(file=f)
        print("MINIMUM_I/SIGMA= 2", file=f)
        print("SAVE_CORRECTION_IMAGES= FALSE", file=f)  # prevent local directory being littered with .cbf files
        print(f"! {spgr}", file=f)
        print(f"! {cell}", file=f)
        print(file=f)
        print("OUTPUT_FILE= MERGED.HKL", file=f)
        print(file=f)
    
        for j, fn in enumerate(fns):
            fn = Path(fn)
            dst = drc / f"{j}_{fn.name}"
            shutil.copy(fn, dst)
            print(f"    ! {fn}", file=f)
            print(f"    INPUT_FILE= {dst.name}", file=f)
            print(f"    INCLUDE_RESOLUTION_RANGE= 20 1.0", file=f)
            print(file=f)
    
        f.close()
    
        sp.run("bash -c xscale 2>&1 >/dev/null", cwd=drc)
    
        with open(drc / "XDSCONV.INP", "w") as f:
            print("""
    INPUT_FILE= MERGED.HKL
    INCLUDE_RESOLUTION_RANGE= 20 0.8 ! optional 
    OUTPUT_FILE= shelx.hkl  SHELX    ! Warning: do _not_ name this file "temp.mtz" !
    FRIEDEL'S_LAW= FALSE             ! default is FRIEDEL'S_LAW=TRUE""", file=f)
    
        sp.run("bash -c xdsconv 2>&1 >/dev/null", cwd=drc)
    
        d = parse_xscale_lp(drc / "XSCALE.LP")
        d["number"] = i
        d["n_clust"] = item["n_clust"]
        results.append(d)

        shelx_ins = Path("shelx.ins")
        if shelx_ins.exists():
            shutil.copy(shelx_ins, drc)

    return results


def get_clusters(z, dmat, distance=0.5, fns=[], method="average"):
    clusters = fcluster(z, distance, criterion='distance')
    
    grouped = defaultdict(list)
    for i, c in enumerate(clusters):
        grouped[c].append(i)
    
    cluster_dict = {}
    for key, items in grouped.items():
        sel = dmat[items][:,items]
        tri = np.triu_indices_from(sel, k=1)
        dsel = sel[tri]
        if len(items) == 1:
            continue

        score = linkage(dsel, method=method)[-1][2]
        cc = np.sqrt(1-score**2)

        cluster_dict[key] = {"score": score, "CC(I)": cc, "n_clust": len(items), "clust": items, 
                             "files": [fns[i] for i in items], "distance_cutoff":distance,
                             "method": method}
    
    return cluster_dict


def parse_xscale_lp_initial(fn="XSCALE.LP"):
    with open(fn, "r") as f:
        for line in f:
            # read filenames
            if line.startswith(" SPACE_GROUP_NUMBER="):
                spgr = line.strip()
            if line.startswith(" UNIT_CELL_CONSTANTS="):
                cell = line.strip()
            
            if "READING INPUT REFLECTION DATA FILES" in line:
                next(f)
                next(f)
                next(f)
                next(f)
                fns = {}
                for line in f:
                    line = line.strip()
                    inp = line.split()
                    if len(inp) == 5:
                        idx = int(inp[0]) - 1  # XSCALE is 1-indexed
                        fns[idx] = inp[4]
                    
                    if "******************************************************************************" in line:
                        break
            
            # read correlation coefficients CC(I)
            if "CORRELATIONS BETWEEN INPUT DATA SETS AFTER CORRECTIONS" in line:
                next(f)
                next(f)
                next(f)
                next(f)
                ccs = []
                for line in f:
                    line = line.strip()
                    if not line:
                        break
                    ccs.append(line)
                break
    return fns, ccs, cell, spgr


def main():
    method = "average"

    fns, ccs, cell, spgr = parse_xscale_lp_initial()

    arr = np.loadtxt(ccs)
    i = arr[:,0].astype(int) - 1  # XSCALE is 1-indexed
    j = arr[:,1].astype(int) - 1  # XSCALE is 1-indexed
    ccs = arr[:,3].astype(float)
    n = max(max(j), max(i)) + 1
    # fill with zeros, because some data sets cannot be compared (no common reflections)
    corrmat = np.zeros((n, n))
    corrmat[i,j] = ccs
    corrmat[j,i] = ccs
    np.fill_diagonal(corrmat, 1.0)
    
    dmat = np.sqrt(1 - corrmat**2)
    
    # array must be a condensed distance matrix
    tri = np.triu_indices_from(dmat, k=1)
    d = dmat[tri]
    
    z = linkage(d, method=method)
    # corresponding with MATLAB behavior
    distance = round(0.7*max(z[:,2]), 4)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    tree = dendrogram(z, color_threshold=distance, ax=ax)
    ax.set_xlabel("Index")
    ax.set_ylabel("Distance $(1-CC^2)^{1/2}$")
    ax.set_title(f"Dendrogram (cutoff={distance:.2f})")
    hline = ax.axhline(y=distance)
    
    def get_cutoff(event):
        nonlocal hline
        nonlocal tree
        nonlocal distance

        if event.ydata:
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

    clusters = get_clusters(z, dmat=dmat, distance=distance, fns=fns, method=method)
    results = run_xscale(clusters, cell=cell, spgr=spgr)
    
    print(f"Cutoff distance: {distance}")
    print()
    print("  #  N_clust  CC(1/2)    N_obs   N_uniq   N_poss   Compl.   N_comp   R_meas   d_min   i/sigma")
    for d in results:
        print("{number:3d} {n_clust:8d} {CC(1/2):8.1f} {N_obs:8d} {N_uniq:8d} {N_possible:8d} \
{Completeness:8.1f} {N_comp:8d} {R_meas:8.3f} {d_min:8.2f} {i/sigma:8.2f}".format(**d))


if __name__ == '__main__':
    main()
