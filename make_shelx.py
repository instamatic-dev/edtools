import subprocess as sp

exe = "sginfo"
fin  = "C:/Program Files (x86)/Sir2014/share/Sir2014/files/Sir.xen"
TABLE = [line.strip() for line in open(fin, "r")]


def comp2dict(composition):
    """Takes composition: Si20 O10, returns dict of atoms {'Si':20,'O':10}"""
    import re
    composition = " ".join(composition)
    pat = re.compile('([A-z]+|[0-9]+)')
    m = re.findall(pat, composition)
    return dict(zip(m[::2], map(int,m[1::2])))


def get_latt_symm_cards(spgr):
    cmd = [exe, spgr, '-Shelx']

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
    key = element.lower() + " "

    block = [line for line in TABLE if line.startswith(key)]
    
    number, weight, radius, vdw_radius = block[0].split()[1:5]
    number = int(number)
    weight = float(weight)
    radius = float(radius)
    vdw_radius = float(vdw_radius)
    
    a1, b1, a2, b2, a3, b3, a4, b4, c = [float(val) for val in block[5].split()[1:] + block[6].split()[1:]]
    SFAC  = f"SFAC {key.upper():3s}{a1:7.4f} {b1:7.4f} {a2:7.4f} {b2:7.4f}         =\n        {a3:7.4f} {b3:7.4f} {a4:7.4f} {b4:7.4f} {c:7.4f} =\n"
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
                        help="Unit cell, can be minimal representation")

    parser.add_argument("-m","--composition",
                        action="store", type=str, nargs="+", dest="composition",
                        help="Composition should be formatted something like 'Si20 O40'")

    parser.set_defaults(cell=None,
                        spgr="P1",
                        composition="")
    
    options = parser.parse_args()

    spgr = options.spgr
    cell = options.cell
    composition = options.composition

    atoms = comp2dict(composition)
    wavelength = 0.02508
    
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
