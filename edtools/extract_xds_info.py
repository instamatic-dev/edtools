from pathlib import Path
import os
import time
import shutil
from .utils import volume, parse_args_for_fns
from .utils import space_group_lib

spglib = space_group_lib()


class xds_parser(object):
    """docstring for xds_parser"""
    def __init__(self, filename):
        super(xds_parser, self).__init__()
        self.ios_threshold = 0.8

        self.filename = Path(filename).resolve()
        self.d = self.parse()

    def parse(self):
        ios_threshold = self.ios_threshold

        fn = self.filename

        f = open(fn, "r")

        in_block = False
        block = []

        d = {}

        cell, spgr = None, None
        ISa = None
        Boverall = None

        for line in f:
            if line.startswith(" SUBSET OF INTENSITY DATA WITH SIGNAL/NOISE >= -3.0 AS FUNCTION OF RESOLUTION"):
                in_block = True
                block = []
            elif line.startswith("    total"):
                block.append(line.strip("\n"))
                in_block = False
            elif line.endswith("as used by INTEGRATE\n"):
                raw_cell = list(map(float, line.strip("\n").split()[1:7]))
            elif line.startswith(" UNIT_CELL_CONSTANTS="):
                cell = list(map(float, line.strip("\n").split()[1:7]))
            elif line.startswith(" UNIT CELL PARAMETERS"):
                cell = list(map(float, line.strip("\n").split()[3:9]))
            elif line.startswith(" SPACE GROUP NUMBER"):
                spgr = int(line.strip("\n").split()[-1])
            elif line.startswith(" SPACE_GROUP_NUMBER="):
                spgr = int(line.strip("\n").split()[1])
            elif line.startswith(" DATA_RANGE="):
                datarange = list(map(float, line.strip("\n").split()[1:]))
            elif line.startswith(" OSCILLATION_RANGE"):
                osc_angle = float(line.strip("\n").split()[-1])
            elif line.startswith("     a        b          ISa"):
                line = next(f)
                inp = line.split()
                ISa = float(inp[-1])
            elif line.startswith("   WILSON LINE (using all data)"):
                inp = line.split()
                Boverall = float(inp[-3])
            elif line.startswith("   --------------------------------------------------------------------------"):
                line = next(f)
                inp = line.split()
                resolution_range = float(inp[0]), float(inp[1])

            if in_block:
                if line:
                    block.append(line.strip("\n"))

        d["ISa"] = ISa
        d["Boverall"] = Boverall

        dmin = 999

        for line in block:
            inp = line.split()
            if len(inp) != 14:
                continue

            try:
                res = float(inp[0])
            except ValueError:
                res = inp[0]
                if res != "total":
                    continue

            res = float(inp[0]) if inp[0] != "total" else inp[0]
            ntot, nuniq, completeness = int(inp[1]), int(inp[2]), float(inp[4].strip("%"))
            ios, rmeas, cchalf = float(inp[8]), float(inp[9].strip("%")), float(inp[10].strip("*"))

            if ios < ios_threshold and res != "total":
                continue

            if (res != "total") and (res < dmin):
                shell = (dmin, res)
                dmin = res

            d[res] = {"ntot": ntot, "nuniq": nuniq, "completeness": completeness, "ios": ios, "rmeas": rmeas, "cchalf": cchalf}

        if dmin == 999:
            return

        if not cell:
            raise ValueError("No cell found")
        if not spgr:
            raise ValueError("No space group found")

        d["outer"] = dmin
        d["outer_shell"] = shell
        try:
            d["res_range"] = resolution_range
            d["volume"] = volume(cell)
            d["cell"] = cell
            d["raw_cell"] = raw_cell
            d["raw_volume"] = volume(raw_cell)
            d["spgr"] = spgr
        except UnboundLocalError as e:
            print(e)
            return
        d["fn"] = fn

        nframes = datarange[1] - datarange[0]
        rotationrange = nframes * osc_angle
        d["rot_range"] = rotationrange

        return d

    @staticmethod
    def info_header(hline=True):
        s  = "   #   dmax  dmin    ntot   nuniq   compl   i/sig   rmeas CC(1/2)     ISa   B(ov)\n"
        if hline:
            s += "---------------------------------------------------------------------------------\n"
        return s

    def print_filename(self):
        print("#", self.filename)

    def cell_info(self, sequence=0):
        d = self.d
        i = sequence
        fn = self.filename
        s = f"{i: 4d}: {fn.parents[0]}  # {time.ctime(os.path.getmtime(fn))}\n"
        s += "Spgr {: 4d} - Cell {:10.2f}{:10.2f}{:10.2f}{:10.2f}{:10.2f}{:10.2f} - Vol {:10.2f}\n".format(d["spgr"], *d["cell"], d["volume"])
        return s

    def integration_info(self, sequence=0, outer_shell=True, filename=False):
        d = self.d
        k = sequence

        s = ""

        if k == 0:
            s += self.info_header()

        dmax, dmin = d["res_range"]

        s += "{k: 4d} {dmax: 6.2f}{dmin: 6.2f}{ntot: 8d}{nuniq: 8d}{completeness: 8.1f}{ios: 8.2f}{rmeas: 8.1f}{cchalf: 8.1f}{ISa: 8.2f}{Boverall: 8.2f}".format(
        k=k, dmax=dmax, dmin=dmin, **d["total"], **d)

        if filename:
            s += f"  # {d['fn']}\n"
        else:
            s += "\n"

        if outer_shell:
            outer = d["outer"]
            dmax_sh, dmin_sh = d["outer_shell"]
            s +="   - {dmax: 6.2f}{dmin: 6.2f}{ntot: 8d}{nuniq: 8d}{completeness: 8.1f}{ios: 8.2f}{rmeas: 8.1f}{cchalf: 8.1f}\n".format(
                k=k, dmax=dmax_sh, dmin=dmin_sh, **d[outer])

        return s

    @property
    def volume(self):
        return self.d["volume"]

    @property
    def unit_cell(self):
        return self.d["cell"]

    @property
    def space_group(self):
        return self.d["spgr"]

    def cell_as_dict(self):
        d = dict(zip("a b c al be ga".split(), self.unit_cell))
        d["volume"] = self.volume
        d["spgr"] = self.space_group
        d["rotation_angle"] = self.d["rot_range"]
        d["total_completeness"] = self.d["total"]["completeness"]
        d["file"] = self.d["fn"]
        return d


def cells_to_excel(ps, fn="cells.xlsx"):
    """Takes a list of `xds_parser` instances and writes the cell
    parameters to an excel file `cells.xlsx`.
    """
    d = {}
    for i, p in enumerate(ps):
        i += 1
        d[i] = p.cell_as_dict()

    import pandas as pd
    df = pd.DataFrame(d).T
    df = df["spgr a b c al be ga volume rotation_angle total_completeness file".split()]
    if not os.path.exists(fn):
        df.to_excel(fn)
    else:
        """To address that cells.xlsx does not overwrite"""
        os.remove(fn)
        df.to_excel(fn)

    print(f"Wrote {i} cells to file {fn}")


def cells_to_cellparm(ps):
    """Takes a list of `xds_parser` instances and writes the cell
    parameters to an instruction file `CELLPARM.INP` for the program
    `cellparm`.
    """
    fn = "CELLPARM.INP"
    # write cellparm input file
    with open(fn, "w") as f:
        for i, p in enumerate(ps):
            i += 1
            fn = p.filename
            # cell = p.unit_cell
            cell = p.d["raw_cell"]
            ntot = p.d["total"]["ntot"]
            print(f"! {i: 3d} from {fn}", file=f)
            print("UNIT_CELL_CONSTANTS= {:10.2f}{:10.2f}{:10.2f}{:10.2f}{:10.2f}{:10.2f} WEIGHT= {ntot}".format(*cell, ntot=ntot), file=f)

    print(f"Wrote file {fn}")


def cells_to_yaml(ps, fn="cells.yaml"):
    import yaml
    ds = []
    for i, p in enumerate(ps):
        i += 1
        d = {}
        d["directory"] = str(p.filename.parent)
        d["number"] = i
        d["unit_cell"] = p.d["cell"]
        d["raw_unit_cell"] = p.d["raw_cell"]
        d["space_group"] = p.d["spgr"]
        d["weight"] = p.d["total"]["ntot"]
        ds.append(d)

    yaml.dump(ds, open(fn, "w"))

    print(f"Wrote {i} cells to file {fn}")


def gather_xds_ascii(ps, min_completeness=10.0, min_cchalf=90.0, gather=False):
    """Takes a list of `xds_parser` instances and gathers the
    corresponding `XDS_ASCII.HKL` files into the current directory.
    The data source and numbering scheme is summarized in the file `filelist.txt`.
    """
    fn = "filelist.txt"

    # gather xds_ascii and prepare filelist
    n = 0
    with open(fn, "w") as f:
        for i, p in enumerate(ps):
            i += 1

            completeness = p.d["total"]["completeness"]
            cchalf = p.d["total"]["cchalf"]

            if cchalf < min_cchalf:
                continue

            if completeness < min_completeness:
                continue

            src = p.filename.with_name("XDS_ASCII.HKL")
            dst = f"{i:02d}_XDS_ASCII.HKL"
            if gather:
                shutil.copy(src, dst)
                ascii_name = dst
            else:
                ascii_name = src

            dmax, dmin = p.d["res_range"]
            print(f" {i: 3d} {ascii_name} {dmax:8.2f} {dmin:8.2f}  # {p.filename}", file=f)
            n += 1

    print(f"Wrote {n} entries to file {fn} (completeness > {min_completeness}%, CC(1/2) > {min_cchalf}%)")


def lattice_to_space_group(lattice):
    return { 'aP':  1, 'mP':  3, 'mC':  5, 'mI':  5,
             'oP': 16, 'oC': 21, 'oI': 23, 'oF': 22,
             'tP': 75, 'tI': 79, 'hP':143, 'hR':146,
             'cP':195, 'cF':196, 'cI':197 }[lattice]


def evaluate_symmetry(ps):
    from collections import Counter

    c_score = Counter()
    c_freq = Counter()

    for p in ps:
        spgr = p.d["spgr"]
        weight = p.d["total"]["ntot"]
        d = spglib[spgr]
        lattice = d["lattice"]
        c_score[lattice] += weight
        c_freq[lattice] += 1

    print("\nMost likely lattice types:")
    n = 1
    for lattice, score in c_score.most_common(100):
        count = c_freq[lattice]
        spgr = lattice_to_space_group(lattice)
        print(f"{n:3} Lattice type `{lattice}` (spgr: {spgr:3}) was found {count:3} times (score: {score:7})")
        n += 1

    return lattice_to_space_group(c_score.most_common()[0][0])

def parse_xparm_for_uc(fn):
    with open(fn, "r") as f:
        f.readline()
        f.readline()
        f.readline()

        line = f.readline().split()
        uc = line[1:]
        uc = [float(i) for i in uc]
        return uc

def cells_to_yaml_xparm(uc, fn="cells_xparm.yaml"):
    import yaml
    ds = []
    for i, p in enumerate(uc):
        i += 1
        d = {}

        d["directory"] = str(Path(p[1]).parent.resolve())

        """get rotation range from XDS.INP"""
        xdsinp = Path(p[1]).parent / "XDS.INP"
        with open(xdsinp, "r") as f:
            for line in f:
                if line.startswith("DATA_RANGE="):
                    datarange = list(map(float, line.strip("\n").split()[1:]))
                elif line.startswith("OSCILLATION_RANGE="):
                    osc_angle = float(line.strip("\n").split()[1])

        rr = osc_angle * (datarange[1] - datarange[0] + 1)

        d["number"] = i
        d["rotation_range"] = rr
        d["raw_unit_cell"] = p[0]
        d["space_group"] = "P1"
        d["weight"] = 1
        ds.append(d)

    yaml.dump(ds, open(fn, "w"))

    print(f"Wrote {i} cells to file {fn}")

def main():
    import argparse

    description = "Program to consolidate data from a large series of data sets from a serial crystallography experiment."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="List of CORRECT.LP files or list of directories. If a list of directories is given "
                        "the program will find all CORRECT.LP files in the subdirectories. If no arguments are given "
                        "the current directory is used as a starting point.")

    parser.add_argument("--match",
                        action="store", type=str, dest="match",
                        help="Include the CORRECT.LP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.add_argument("-g", "--gather",
                        action="store_true", dest="gather",
                        help="Gather XDS_ASCII.HKL files in local directory.")

    parser.add_argument("-x", "--xparm",
                        action="store_true", dest="xparm",
                        help="extract unit cell info from XPARM.XDS instead of CORRECT.LP. NOTE!! Only aimed for first step clustering.")

    parser.set_defaults(match=None)

    options = parser.parse_args()

    match = options.match
    gather = options.gather
    xparm = options.xparm
    args = options.args

    if xparm:
        fns = parse_args_for_fns(args, name="XPARM.XDS", match=match)
        foundCells_and_Path = []

        for fn in fns:
            uc = parse_xparm_for_uc(fn)
            foundCells_and_Path.append([uc, fn])

        cells_to_yaml_xparm(uc = foundCells_and_Path, fn = "cells_xparm.yaml")
        print("Cell information from XPARM.XDS parsed to cells_xparm.yaml")

    else:
        fns = parse_args_for_fns(args, name="CORRECT.LP", match=match)

        xdsall = []
        for fn in fns:
            try:
                p = xds_parser(fn)
            except UnboundLocalError as e:
                print(e)
                continue
            else:
                if p and p.d:
                    xdsall.append(p)

        for i, p in enumerate(xdsall):
            i += 1
            print(p.cell_info(sequence=i))

        print(xds_parser.info_header())
        for i, p in enumerate(xdsall):
            i += 1
            print(p.integration_info(sequence=i, filename=True))

        cells_to_excel(xdsall)
        # cells_to_cellparm(xdsall)
        cells_to_yaml(xdsall)

        gather_xds_ascii(xdsall, gather=gather)

        evaluate_symmetry(xdsall)
        print("\n ** the score corresponds to the total number of indexed reflections.")


if __name__ == '__main__':
    main()
