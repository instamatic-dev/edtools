import subprocess as sp
from pathlib import Path
import yaml
from shutil import which
import sys


if exe := which("sginfo"):
    context = "sginfo"
elif exe := which("cctbx.python"):
    context = "cctbx.python"
else:
    sys.exit("Either sginfo or cctbx.python must be in the path")

fin  = Path(__file__).parent / "atomlib.yaml"
TABLE = yaml.load(open(fin, "r"), Loader=yaml.Loader)


def comp2dict(composition):
    """Takes composition: Si20 O10, returns dict of atoms {'Si':20,'O':10}"""
    import re
    composition = "".join(composition)
    pat = re.compile('([A-z]+|[0-9]+)')
    m = re.findall(pat, composition)
    return dict(zip(m[::2], map(int,m[1::2])))


def get_latt_symm_cards(spgr):
    if context == "sginfo":
        cmd = [exe, spgr, '-Shelx']
    elif context == "cctbx.python":
        script = ("from cctbx import sgtbx;"
                  "from iotbx.shelx.write_ins import LATT_SYMM;"
                  "import sys;"
                  f"space_group_info = sgtbx.space_group_info(symbol='{spgr}');"
                  "LATT_SYMM(sys.stdout, space_group_info.group());")
        cmd = [exe, "-c", script]

    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
    out, err = p.communicate()
    out = out.decode()
    SYMM = []

    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("LATT"):
            LATT = line
        if line.startswith("SYMM"):
            SYMM.append(line)

    return LATT, SYMM


def get_sfac(element):
    d = TABLE[element.lower()]

    radius = d["radius"]
    weight = d["weight"]

    a1, b1, a2, b2, a3, b3, a4, b4, c = d["sfac_electron"]
    SFAC  = f"SFAC {element.upper():3s}{a1:7.4f} {b1:7.4f} {a2:7.4f} {b2:7.4f}         =\n        {a3:7.4f} {b3:7.4f} {a4:7.4f} {b4:7.4f} {c:7.4f} =\n"
    SFAC += f"         0.0000  0.0000  0.0000 {radius:7.4f} {weight:7.4f}"

    return SFAC


def main():
    import argparse

    description = ""
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-s","--spgr",
                        action="store", type=str, dest="spgr",
                        help="Space group (default P1)")

    parser.add_argument("-c","--cell",
                        action="store", type=float, nargs=6, dest="cell",
                        help="Unit cell")

    parser.add_argument("-m","--composition",
                        action="store", type=str, nargs="+", dest="composition",
                        help="Composition should be formatted something like 'Si20 O40'")

    parser.add_argument("-w","--wavelength",
                        action="store", type=float, dest="wavelength",
                        help="Set the wavelength in Ångströms, default=0.02508 [120 kV: 0.03349 Å, 200 kV: 0.02508 Å, 300 kV: 0.01969 Å")

    parser.set_defaults(cell=(10, 10, 10, 90, 90, 90),
                        spgr="P1",
                        composition="",
                        wavelength=0.02508)

    options = parser.parse_args()

    spgr = options.spgr
    cell = options.cell
    composition = options.composition

    atoms = comp2dict(composition)
    wavelength = options.wavelength

    a, b, c, al, be, ga = cell

    out = "shelx.ins"
    f = open(out, "w")

    print(f"TITL {spgr}", file=f)
    print(f"CELL {wavelength:.4f} {a:6.3f} {b:6.3f} {c:6.3f} {al:7.3f} {be:7.3f} {ga:7.3f}", file=f)
    print(f"ZERR 1.00    0.000  0.000  0.000   0.000   0.000   0.000", file=f)

    LATT, SYMM = get_latt_symm_cards(spgr)

    print(LATT, file=f)
    for line in SYMM:
        print(line, file=f)

    UNIT = "UNIT"
    for name, number in atoms.items():
        SFAC = get_sfac(name)
        print(SFAC, file=f)
        UNIT += f" {number}"

    print(UNIT, file=f)
    print("TREF 5000", file=f)
    print("HKLF 4", file=f)
    print("END", file=f)


if __name__ == '__main__':
    main()
