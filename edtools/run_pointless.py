from pathlib import Path
import yaml
import os
from .cluster import run_pointless


def main():
    import argparse

    description = "Program for running pointless on a large number of files"
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
        
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="Path to a cells.yaml XDS_ASCII.HKL files")
   
    options = parser.parse_args()

    args = options.args

    if not args:  # attempt to populate args
        if os.path.exists("cells.yaml"):
            args = ["cells.yaml"]
        else:
            args = list(Path(".").glob("*XDS_ASCII.HKL"))
        
    if not args:
        exit()
    else:
        lst = []
        for arg in args:
            fn = Path(arg)
            extension = fn.suffix.lower()
            if extension == ".yaml":
                cells = yaml.load(open(fn, "r"), Loader=yaml.Loader)
                lst.extend([Path(cell["directory"]) / "XDS_ASCII.HKL" for cell in cells])
            if extension == ".hkl":
                lst.append(fn)

    print(f"{len(lst)} XDS_ASCII.HKL files found.\n")

    ds = []
    for i, fn in enumerate(lst):
        print(fn)
        print(f"Running pointless on data set #{i}\n")
        d = run_pointless(fn)
        d["filename"] = fn.name
        ds.append(d)

    print("  # Filename             Lauegr.  prob.  conf. - cell                                             | idx")
    for i, d in enumerate(ds):
        try:
            print("{i:3d} {filename:20s} {laue_group:>7s} {probability:6.2f} {confidence:6.2f} - {unit_cell} | {reindex_operator:20s}".format(i=i, **d))
        except KeyError:
            print("{i:3d} {filename:20s} {msg:>7s}".format(i=i, filename=d["filename"], msg="fail"))



if __name__ == '__main__':
    main()
