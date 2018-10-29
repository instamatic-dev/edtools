from pathlib import Path, PurePosixPath
from sys import argv
import os, time
from math import radians, cos
import numpy as np

threshold = 2.0


def cell_to_np(cell):
    return np.array([float(val) for val in cell.split()])


def volume(cell):
    """Returns volume for the general case from cell parameters"""
    a, b, c, al, be, ga = cell
    al = radians(al)
    be = radians(be)
    ga = radians(ga)
    vol = a*b*c * \
        ((1+2*cos(al)*cos(be)*cos(ga)-cos(al)**2-cos(be)**2-cos(ga)**2)
         ** .5)
    return vol


def get_cells(fns):
    cells = []

    for i, fn in enumerate(fns):
        mtime = time.ctime(os.path.getmtime(fn))
        print(i, fn, "-", mtime)
        cell, spgr = extract_cell(fn)

        cells.append((cell, spgr))

    print()
    return cells


def choose_cell(cells):
    for i, (cell, spgr) in enumerate(cells):
        vol = volume(cell_to_np(cell))
        print(f"{i:2d} - SPGR {spgr:>3s} CELL {cell} VOL {vol:.2f}")

    num = int(input("\nChoose cell [0]: ") or 0)
    print()

    return cells[num]


def extract_cell(fn):
    f = open(fn, "r")
    for line in f:
        if line.startswith("!UNIT_CELL_CONSTANTS="):
            cell = line.strip()
        elif line.startswith("!SPACE_GROUP_NUMBER="):
            spgr = line.strip()
        elif line.startswith("!END_OF_HEADER"):
            break

    cell = cell[24:]
    spgr = spgr.split()[-1]

    return cell, spgr


def write_xscale_inp(fns, cells, target_cell, target_spgr):
    c = cell_to_np(target_cell)
    with open("XSCALE.INP", "w") as f:

        print("MINIMUM_I/SIGMA= 2", file=f)
        print(f"SPACE_GROUP_NUMBER= {target_spgr}", file=f)
        print(f"UNIT_CELL_CONSTANTS= {target_cell}", file=f)
        print(file=f)
        print("OUTPUT_FILE= MERGED.HKL", file=f)
        print(file=f)
        
        for i, fn in enumerate(fns):
            other_cell, other_spgr = cells[i]
            o = cell_to_np(other_cell)
            dist = np.linalg.norm(c-o, axis=0)

            print(f"    !SPGR {other_spgr:>3s} CELL {other_cell} DIST {dist:.2f}", file=f)

            pre = "!" if dist > threshold else ""

            print(f"    {pre}INPUT_FILE= {fn.as_posix()}", file=f)
            print(f"    {pre}INCLUDE_RESOLUTION_RANGE= 20 0.8", file=f)
            print(file=f)

    print(f"Wrote file {f.name}")


def write_cellparm_inp(fns, cells, target_cell):
    c = cell_to_np(target_cell)

    with open("CELLPARM.INP", "w") as f:
        for i, fn in enumerate(fns):
            arr = np.loadtxt(fn, comments="!")
            ntot = len(arr)

            other_cell, other_spgr = cells[i]
            o = cell_to_np(other_cell)
            dist = np.linalg.norm(c-o, axis=0)

            if dist < threshold:
                print(f"! {i} from {fn}", file=f)
                print(f"UNIT_CELL_CONSTANTS= {other_cell} WEIGHT= {ntot}", file=f)

    print(f"Wrote file {f.name}")


def write_xdsconv_inp():
    with open("XDSCONV.INP", "w") as f:
        print("""
INPUT_FILE= MERGED.HKL
INCLUDE_RESOLUTION_RANGE= 20 0.8 ! optional 
OUTPUT_FILE= shelx.hkl  SHELX    ! Warning: do _not_ name this file "temp.mtz" !
FRIEDEL'S_LAW= FALSE             ! default is FRIEDEL'S_LAW=TRUE""", file=f)

    print(f"Wrote file {f.name}")


def main():
    fns = argv[1:]

    if not fns:
        fns = list(Path(".").glob("*XDS_ASCII.HKL"))
        print(f"Found {len(fns)} files matching XDS_ASCII.HKL\n")
    else:
        fns = [Path(fn) for fn in fns]

    cells = get_cells(fns)

    target_cell, target_spgr = choose_cell(cells)

    write_xscale_inp(fns, cells, target_cell, target_spgr)
    write_cellparm_inp(fns, cells, target_cell)
    write_xdsconv_inp()


if __name__ == '__main__':
    main()
