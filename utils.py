from math import radians, cos
from pathlib import Path


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
        fns = [Path(fn) for fn in fns]

    new_fns = []
    for fn in fns:
        if fn.is_dir():
            new_fns.extend(list(fn.rglob(f"{name}")))
        else:  
            new_fns.append(fn)
    if match:
        new_fns = [fn for fn in new_fns if fn.match(f"{match}/*")]
    new_fns = [fn.resolve() for fn in new_fns]
    print(f"{len(new_fns)} files found.")

    return new_fns

