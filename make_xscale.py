from pathlib import Path, PurePosixPath
from sys import argv
import os, time
from math import radians, cos
import numpy as np

threshold = 2.0


def write_xscale_inp(fns, unit_cell, space_group):
    cwd = Path(".").resolve()

    cell_str = " ".join((f"{val:.3f}" for val in unit_cell))
    with open("XSCALE.INP", "w") as f:

        print("MINIMUM_I/SIGMA= 2", file=f)
        print("SAVE_CORRECTION_IMAGES= FALSE", file=f)  # prevent local directory being littered with .cbf files
        #print(f"SPACE_GROUP_NUMBER= {space_group}", file=f)
        #print(f"UNIT_CELL_CONSTANTS= {cell_str}", file=f)
        print(file=f)
        print("OUTPUT_FILE= MERGED.HKL", file=f)
        print(file=f)
        
        for i, fn in enumerate(fns):
            fn = fn.relative_to(cwd)
            print(f"    INPUT_FILE= {fn.as_posix()}", file=f)
            print(f"    INCLUDE_RESOLUTION_RANGE= 20 0.8", file=f)
            print(file=f)

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
    import yaml

    args = argv[1:]

    if not args:
        fn = "cells.yaml"
    else:
        fn = args[0]

    ds = yaml.load(open(fn, "r"))

    fns = [Path(d["directory"]) / "XDS_ASCII.HKL" for d in ds]

    cells = np.array([d["unit_cell"] for d in ds])
    unit_cell = np.mean(cells, axis=0)
    space_group = 16

    write_xscale_inp(fns, unit_cell=unit_cell, space_group=space_group)
    write_xdsconv_inp()


if __name__ == '__main__':
    main()
