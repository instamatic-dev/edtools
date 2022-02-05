from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from collections import defaultdict
from pathlib import Path
import shutil
import subprocess as sp
import numpy as np
import matplotlib.pyplot as plt
from types import SimpleNamespace
import sys

platform = sys.platform

if platform == "win32":
    from .wsl import bash_exe

def check_for_pointless():
    if platform == "win32":
        # -i to run bash in interactive mode, i.e. .bashrc is loaded
        p = sp.run(f'{bash_exe} -ic which pointless', stdout=sp.PIPE)  # check if pointless can be run
    else:
        p = sp.run("which pointless", stdout=sp.PIPE, shell=True)  # check if pointless can be run

    if p.stdout:
        return True
    else:
        return False

POINTLESS = check_for_pointless()


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
    
    d = {key: 0 for key in xscale_keys}
    
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


def run_pointless(filepat, verbose=True, i=0):
    drc = filepat.parent
    with open(drc / "pointless.sh", "w") as f:
        print(f"""pointless {filepat.name} << eof
SETTING SYMMETRY-BASED
CHIRALITY NONCHIRAL
NEIGHBOUR 0.02
RESOLUTION 10.0 1.0
SYSTEMATICABSENCES OFF
XMLOUT pointless.xml
eof""", file=f)

    d = {}

    if POINTLESS:
        print(f"Running pointless on cluster {i}\n")
        if platform == "win32":
            sp.run(f"{bash_exe} -ic ./pointless.sh > pointless.log", cwd=drc)
        else:
            sp.run("bash ./pointless.sh > pointless.log", cwd=drc, shell=True)

        with open(drc / "pointless.log", "r") as f:
            output = False
            for line in f:
                if "Best Solution" in line:
                    # output = True
                    d["laue_group"] = line.split("point group")[-1].replace(" ", "").strip()
                elif "Laue Group        Lklhd" in line:
                    output = verbose
                
                if line.startswith("   Reindex operator:"):
                    d["reindex_operator"] = line.split(":")[-1].strip()
                if line.startswith("   Laue group probability:"):
                    d["probability"] = float(line.split(":")[-1])
                if line.startswith("   Confidence:"):
                    d["confidence"] = float(line.split(":")[-1])
                if line.startswith("   Unit cell:"):
                    d["unit_cell"] = line.split(":")[-1].strip()

                if "<!--SUMMARY_END-->" in line:
                    output = False

                if output and line.strip():
                    print(line, end="")
        print("-----\n")

        return d

    else:
        return {}


def run_xscale(clusters, cell, spgr, resolution=(20.0, 0.8), ioversigma=2):
    results = []
    
    dmax, dmin = resolution

    keys = sorted(clusters.keys())
    
    for i in keys:
        item = clusters[i]
        
        fns = item["files"]
        drc = Path(f"cluster_{i}")
        drc.mkdir(parents=True, exist_ok=True)
    
        f = open(drc / "XSCALE.INP", "w")
        filelist = open(drc / "filelist.txt", "w")
    
        print(f"! Clustered data from {item['n_clust']} data sets", file=f)
        # print(f"! Cluster score: {item['score']:.3f}", file=f)
        # print(f"! Cluster CC(I): {item['CC(I)']:.3f}", file=f)
        print(f"! Cluster items: {item['clust']}", file=f)
        print(f"! Cluster distance cutoff: {item['distance_cutoff']}", file=f)
        print(f"! Cluster method: {item['method']}", file=f)
        print(file=f)
        print(f"SNRC= {ioversigma}", file=f)
        print("SAVE_CORRECTION_IMAGES= FALSE", file=f)  # prevent local directory being littered with .cbf files
        print(f" {spgr}", file=f)
        print(f" {cell}", file=f)
        print(file=f)
        print("OUTPUT_FILE= MERGED.HKL", file=f)
        print(file=f)
    
        for j, fn in enumerate(fns):
            if (platform == "win32") and (str(fn).startswith("/mnt/")):
                s = str(fn)
                drive_letter = s[5]
                drive = f"{drive_letter.upper()}:"
                fn = s.replace(f"/mnt/{drive_letter}", drive)
            j += 1
            fn = Path(fn)
            dst = drc / f"{j}_{fn.name}"
            shutil.copy(fn, dst)
            print(f"    ! {fn}", file=f)
            print(f"    INPUT_FILE= {dst.name}", file=f)
            print(f"    INCLUDE_RESOLUTION_RANGE= {dmax:8.2f} {dmin:8.2f}", file=f)
            print(file=f)

            print(f" {j: 3d} {dst.name} {dmax:8.2f} {dmin:8.2f}  # {fn.parent}", file=filelist)  
    
        f.close()
        filelist.close()

        item.update(run_pointless(drc / "*_XDS_ASCII.HKL"))

        print(f"Running XSCALE on cluster {i}")
        if platform == "win32":
            sp.run(f"{bash_exe} -ic xscale 2>&1 >/dev/null", cwd=drc)
        else:
            sp.run("xscale 2>&1 >/dev/null", cwd=drc, shell=True)
    
        with open(drc / "XDSCONV.INP", "w") as f:
            print(f"""
INPUT_FILE= MERGED.HKL
INCLUDE_RESOLUTION_RANGE= {dmax:8.2f} {dmin:8.2f} ! optional 
OUTPUT_FILE= shelx.hkl  SHELX    ! Warning: do _not_ name this file "temp.mtz" !
FRIEDEL'S_LAW= FALSE             ! default is FRIEDEL'S_LAW=TRUE""", file=f)
        
        if platform == "win32":
            sp.run(f"{bash_exe} -ic xdsconv 2>&1 >/dev/null", cwd=drc)
        else:
            sp.run("xdsconv 2>&1 >/dev/null", cwd=drc, shell=True)

        item.update(parse_xscale_lp(drc / "XSCALE.LP"))
        item["number"] = i
        results.append(item)

        shelx_ins = Path("shelx.ins")
        if shelx_ins.exists():
            shutil.copy(shelx_ins, drc)

    return results


def get_clusters(z, distance=0.5, fns=[], method="average", min_size=1):
    clusters = fcluster(z, distance, criterion='distance')
    
    grouped = defaultdict(list)
    for i, c in enumerate(clusters):
        grouped[c].append(i)
    
    ignored = []

    cluster_dict = {}
    for key, items in grouped.items():
        if len(items) <= min_size:
            continue

        cluster_dict[key] = {"n_clust": len(items), "clust": [item+1 for item in items],  # use 1-based indexing for output
                             "files": [fns[i] for i in items], "distance_cutoff":distance,
                             "method": method}
    
    for key in ignored:
        print(f"Ignored {len(ignored)} clusters smaller than {min_size} items")

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

    # clip negative values to 0
    corrmat = corrmat.clip(min=0)

    obj = SimpleNamespace()
    obj.filenames = fns
    obj.correlation_matrix = corrmat
    obj.unit_cell = cell
    obj.space_group = spgr

    return obj


def get_condensed_distance_matrix(corrmat):
    dmat = np.sqrt(1 - corrmat**2)
    
    # array must be a condensed distance matrix
    tri = np.triu_indices_from(dmat, k=1)
    d = dmat[tri]
    return d


def distance_from_dendrogram(z, distance=None):
    # corresponding with MATLAB behavior
    if not distance:
        distance = round(0.7*max(z[:,2]), 4)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    labels = range(1, int(max(z[:,3]))+1)

    tree = dendrogram(z, color_threshold=distance, ax=ax, above_threshold_color="lightblue", labels=labels)

    ax.set_xlabel("Index")
    ax.set_ylabel("Distance $(1-CC^2)^{1/2}$")
    ax.set_title(f"Dendrogram ($t={distance:.2f}$)")
    hline = ax.axhline(y=distance)

    def get_cutoff(event):
        nonlocal hline
        nonlocal tree
        nonlocal distance

        if event.ydata:
            distance = round(event.ydata, 4)
            ax.set_title(f"Dendrogram ($t={distance:.2f}$)")
            hline.remove()
            hline = ax.axhline(y=distance)

            for c in ax.collections:
                c.remove()

            tree = dendrogram(z, color_threshold=distance, ax=ax, above_threshold_color="lightblue", labels=labels)

            fig.canvas.draw()
    
    fig.canvas.mpl_connect('button_press_event', get_cutoff)
    plt.show()

    return distance


def main():
    import argparse

    description = ""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
        
    parser.add_argument("-d","--distance",
                        action="store", type=float, dest="distance",
                        help="Use this to set the cut-off distance to use. This will bypass the dendrogram. If '-g' is also given, this will put the bar at the given value.")

    parser.add_argument("-s","--min_size",
                        action="store", type=int, dest="min_size",
                        help="Ignore clusters smaller than the given size (default=1).")

    parser.add_argument("-m","--method",
                        action="store", type=str, dest="method",
                        choices="single average complete median weighted centroid ward".split(),
                        help="Method for calculating the clustering distance (see `scipy.cluster.hierarchy.linkage`). The default (`average`) is usually a good choice.")
    
    parser.add_argument("-r","--resolution",
                        action="store", type=float, nargs=2, dest="resolution",
                        help="The script will run XSCALE on every cluster, and this option sets the resolution range for scaling _only_ (defaults: dmax=20.0, dmin=0.80). Note that it does not affect the merged data resolution (which is defined by XDSCONV).")

    parser.add_argument("-i","--ioversigma",
                        action="store", type=float, dest="ioversigma",
                        help="Run XSCALE with the given i/sigma. As with the resolution above, this selects the reflections for scaling _only_ (default: 2).")

    parser.add_argument("-g","--dendrogram",
                        action="store_true", dest="show_dendrogram_only",
                        help="Just show the dendrogram and then quit.")

    parser.set_defaults(distance=None,
                        method="average",
                        resolution=(20, 0.8),
                        ioversigma=2,
                        show_dendrogram_only=False,
                        min_size=1)

    options = parser.parse_args()
    distance = options.distance
    min_size = options.min_size
    method = options.method
    dmax, dmin = options.resolution
    ioversigma = options.ioversigma
    show_dendrogram_only = options.show_dendrogram_only

    sort_key = "Completeness"

    obj = parse_xscale_lp_initial(fn="XSCALE.LP")
    d = get_condensed_distance_matrix(obj.correlation_matrix)

    z = linkage(d, method=method)

    if show_dendrogram_only:
        distance_from_dendrogram(z, distance=distance)
        exit()
    elif not distance:
        distance = distance_from_dendrogram(z, distance=distance)

    clusters = get_clusters(z, distance=distance, fns=obj.filenames, method=method, min_size=min_size)
    results = run_xscale(clusters, cell=obj.unit_cell, spgr=obj.space_group, resolution=(dmax, dmin), ioversigma=ioversigma)

    print("")
    print("Clustering results")
    print("")
    print(f"Cutoff distance: {distance:.3f}")
    print(f"Equivalent CC(I): {(1-distance**2)**0.5:.3f}")
    print(f"Method: {method}")
    print("")
    print("  #  N_clust   CC(1/2)    N_obs   N_uniq   N_poss    Compl.   N_comp    R_meas    d_min  i/sigma  | Lauegr.  prob. conf.  idx")
    
    for d in sorted(results, key=lambda x: x[sort_key]):
        p1 = "*" if d["CC(1/2)"] > 90 else " "
        p2 = "*" if d["Completeness"] > 80 else " "
        p3 = "*" if d["R_meas"] < 0.30 else " "
        p0 = "".join(sorted(p1+p2+p3, reverse=True))

        try:
            print("{number:3d}{p0} {n_clust:5d} {CC(1/2):8.1f}{p1} {N_obs:8d} {N_uniq:8d} {N_possible:8d} \
{Completeness:8.1f}{p2} {N_comp:8d} {R_meas:8.3f}{p3} {d_min:8.2f} {i/sigma:8.2f}  | \
{laue_group:>7s} {probability:5.2f} {confidence:6.2f}  {reindex_operator}".format(p0=p0, p1=p1, p2=p2, p3=p3, **d))
        except KeyError:
            print("{number:3d}{p0} {n_clust:5d} {CC(1/2):8.1f}{p1} {N_obs:8d} {N_uniq:8d} {N_possible:8d} \
{Completeness:8.1f}{p2} {N_comp:8d} {R_meas:8.3f}{p3} {d_min:8.2f} {i/sigma:8.2f}".format(p0=p0, p1=p1, p2=p2, p3=p3, **d))

    print(f"(Sorted by '{sort_key}')")
    print()
    for d in results:
        print("Cluster {number}: {clust}".format(**d))


if __name__ == '__main__':
    main()
