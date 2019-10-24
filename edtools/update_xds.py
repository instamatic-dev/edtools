from pathlib import Path
import shutil
from .utils import parse_args_for_fns


def update_xds(fn, 
               cell=None, 
               spgr=None, 
               comment=False, 
               axis_error=None, 
               angle_error=None, 
               overload=None, 
               lo_res=None, 
               hi_res=None, 
               cut_frames=None, 
               wfac1=None, 
               apd=None,
               jobs=None):
    shutil.copyfile(fn, fn.with_name("XDS.INP~"))
    
    lines = open(fn, "r", encoding = 'cp1252').readlines()
    if not lines:
        return

    pre = "!" if comment else ""

    new_lines = []

    if jobs:
        jobs = [job.upper() for job in jobs]
        jobs_line = "JOB= " + " ".join(jobs) + "\n\n"
        new_lines.append(jobs_line)

    for line in lines:
        if cell and "UNIT_CELL_CONSTANTS" in line:
            cell_str = " ".join((f"{val:.3f}" for val in cell))
            cell_line = f"{pre}UNIT_CELL_CONSTANTS= {cell_str}\n"
            line = cell_line
        elif spgr and "SPACE_GROUP_NUMBER" in line:
            spgr_line = f"{pre}SPACE_GROUP_NUMBER= {spgr}\n"
            line = spgr_line
        elif axis_error and "MAX_CELL_AXIS_ERROR" in line:
            line = f"MAX_CELL_AXIS_ERROR= {axis_error:.2f}\n"
        elif angle_error and "MAX_CELL_ANGLE_ERROR" in line:
            line = f"MAX_CELL_ANGLE_ERROR= {angle_error:.2f}\n"
        elif overload and "OVERLOAD" in line:
            line = f"OVERLOAD= {overload:d}\n"
        elif hi_res and "INCLUDE_RESOLUTION_RANGE" in line:
            line = f"INCLUDE_RESOLUTION_RANGE= {lo_res:.1f} {hi_res:.1f}\n"
        elif wfac1 and "WFAC1" in line:
            line = f"WFAC1= {wfac1:.1f}\n"
        elif cut_frames and any(s in line[0:16] for s in ["DATA_RANGE","SPOT_RANGE","BACKGROUND_RANGE"]):
            data_begin, data_end = line[20:].split()
            data_begin_cf = round(int(data_begin)*0.98)
            data_end_cf = round(int(data_end)*0.98)
            line = f"DATA_RANGE            {data_begin_cf:d} {data_end_cf:d}\n"
        elif comment and "UNIT_CELL_CONSTANTS" in line:
            line = pre + line
        elif comment and "SPACE_GROUP_NUMBER" in line:
            line = pre + line
        elif jobs and ("JOB=" in line):
            continue

        new_lines.append(line)

    if apd:
        line = f"{apd}\n"
        new_lines.append(line)
        
    open(fn, "w").writelines(new_lines)


def main():
    import argparse

    description = "Program to update the cell parameters and space group in all XDS.INP files."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="List of XDS.INP files or list of directories. If a list of directories is given "
                        "the program will find all XDS.INP files in the subdirectories. If no arguments are given "
                        "the current directory is used as a starting point.")

    parser.add_argument("-s","--spgr",
                        action="store", type=str, dest="spgr",
                        help="Update space group")

    parser.add_argument("-c","--cell",
                        action="store", type=float, nargs=6, dest="cell",
                        help="Update unit cell parameters")
    
    parser.add_argument("-m","--comment",
                        action="store_true", dest="comment",
                        help="Comment out unit cell / space group instructions")

    parser.add_argument("-e","--max-error",
                        action="store", type=float, nargs=2, dest="cell_error",
                        help="Update the maximum cell error MAX_CELL_AXIS_ERROR / MAX_CELL_ANGLE_ERROR (default: 0.03 / 2.0)")

    parser.add_argument("-o","--overload",
                        action="store", type=int, dest="overload_value",
                        help="Update the dynamical range max value (default: 130000)")

    parser.add_argument("-r","--resolution",
                        action="store", type=float, nargs=2, dest="resolution",
                        help="Update resolution cut LOW_RES / HIGH_RES (default: 20 0.8)")

    parser.add_argument("-cf","--cut-frames",
                        action="store_true", dest="cut_frames",
                        help="Cut the first and last 2 percent of frames")

    parser.add_argument("-w","--wfac1",
                        action="store", type=float, dest="wfac1",
                        help="parameter used for recognizing MISFITS (default: 1.0)")

    parser.add_argument("-a","--append",
                        action="store", type=str, dest="append",
                        help="Append any VALID XDS input parameters")

    parser.add_argument("-m" "--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.add_argument("-j", "--jobs",
                        action="store", type=str, nargs="+", 
                        help="Specify which JOB should be performed by XDS")

    parser.set_defaults(cell=None,
                        spgr=None,
                        comment=False,
                        cell_error=(None, None),
                        match=None,
                        overload_value=None,
                        resolution=(None, None),
                        wfac1=None,
                        apd=None,
                        jobs=(),
                        )
    
    options = parser.parse_args()
    spgr = options.spgr
    cell = options.cell
    comment = options.comment
    fns = options.args
    axis_error, angle_error = options.cell_error
    match = options.match
    overload = options.overload_value
    lo_res, hi_res = options.resolution
    cut_frames = options.cut_frames
    wfac1 = options.wfac1
    apd = options.append
    jobs = options.jobs

    fns = parse_args_for_fns(fns, name="XDS.INP", match=match)

    for fn in fns:
        print("\033[K", fn, end='\r')  # "\033[K" clears line
        update_xds(fn, 
                   cell=cell, 
                   spgr=spgr, 
                   comment=comment, 
                   axis_error=axis_error, 
                   angle_error=angle_error, 
                   overload=overload, 
                   lo_res=lo_res, 
                   hi_res=hi_res, 
                   cut_frames=cut_frames, 
                   wfac1=wfac1, 
                   apd=apd,
                   jobs=jobs)

    print(f"\033[KUpdated {len(fns)} files")


if __name__ == '__main__':
    main()
