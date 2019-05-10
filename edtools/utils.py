from math import radians, cos
from pathlib import Path
import yaml


def space_group_lib():
    """Initialize simple space group library mapping the space group 
    number to a dict with information on the `class` (crystal class),
    `lattice` (lattice symbol), `laue_symmetry` (number of the lowest 
    symmetry space group for this lattice), `name` (space group name), 
    and `number` (space group number)."""
    fn = Path(__file__).parent / "spglib.yaml"
    return yaml.load(open(fn, "r"), Loader=yaml.Loader)


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


def parse_args_for_fns(args, name="XDS.INP", match=None):
    """Parse list of filenames and resolve wildcards
    name:
        Name of the file to locate
    match:
        Match the file list against the provided glob-style pattern.
        If the match is False, the path is removed from the list.
        example:
            match="SMV_reprocessed"
        """
    if not args:
        fns = [Path(".")]
    else:
        fns = [Path(fn) for fn in args]

    new_fns = []
    for fn in fns:
        if fn.is_dir():
            new_fns.extend(list(fn.rglob(f"{name}")))
        else:  
            new_fns.append(fn)
    
    if match:
        new_fns = [fn for fn in new_fns if fn.match(f"{match}/*")]
    
    new_fns = [fn.resolve() for fn in new_fns]

    print(f"{len(new_fns)} files named {name} (subdir: {match}) found.")

    return new_fns

