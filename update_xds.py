from pathlib import Path
import shutil


def parse_fns(fns, name="XDS.INP"):
    """Parse list of filenames and resolve wildcards"""
    new_fns = []
    for fn in fns:
        if fn.is_dir():
            new_fns.extend(list(fn.glob(f"**/{name}")))
        else:  
            new_fns.append(fn)
    # new_fns = [fn for fn in new_fns if "reprocess" in str(fn)]
    new_fns = [fn.resolve() for fn in new_fns]
    return new_fns


def update_xds(fn, cell=None, spgr=None, comment=False):
    if not cell:
        cell = (10, 10, 10, 90, 90, 90)
    if not spgr:
        spgr = 1

    shutil.copyfile(fn, fn.with_name("XDS.INP~"))
    
    lines = open(fn, "r").readlines()
    if not lines:
        return

    pre = "!" if comment else ""

    cell_str = " ".join((f"{val:.3f}" for val in cell))
    spgr_line = f"{pre}SPACE_GROUP_NUMBER= {spgr}\n"
    cell_line = f"{pre}UNIT_CELL_CONSTANTS= {cell_str}\n"

    new_lines = []
    for line in lines:
        if "UNIT_CELL_CONSTANTS" in line:
            line = cell_line
        elif "SPACE_GROUP_NUMBER" in line:
            line = spgr_line

        new_lines.append(line)

    open(fn, "w").writelines(new_lines)


def main():
    import argparse

    description = "Program to update the cell parameters and space group in all XDS.INP files."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="Path to XDS.INP")

    parser.add_argument("-s","--spgr",
                        action="store", type=str, dest="spgr",
                        help="Update space group")

    parser.add_argument("-c","--cell",
                        action="store", type=float, nargs=6, dest="cell",
                        help="Update unit cell parameters")
    
    parser.add_argument("-m","--comment",
                        action="store_true", dest="comment",
                        help="Comment out unit cell / space group instructions")

    parser.set_defaults(cell=None,
                        spgr=None,
                        comment=False)
    
    options = parser.parse_args()
    spgr = options.spgr
    cell = options.cell
    comment = options.comment
    fns = options.args

    if not fns:
        fns = [Path(".")]
    else:
        fns = [Path(fn) for fn in fns]

    fns = parse_fns(fns)

    for fn in fns:
        print("\033[K", fn, end='\r')  # "\033[K" clears line
        update_xds(fn, cell=cell, spgr=spgr, comment=comment)


if __name__ == '__main__':
    main()