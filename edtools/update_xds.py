from pathlib import Path
import shutil
from .utils import parse_args_for_fns

XDSJOBS = ("XYCORR", "INIT", "COLSPOT", "IDXREF", "DEFPIX", "INTEGRATE", "CORRECT")


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
               jobs=None,
               sp=None, 
               indnumthre=None, 
               d=False, 
               dl=None,
               processors=None,
               center=None,
               axis=None,
               cam_len=None,
               mosaicity=None,
               pixel_size=None,
               untrusted=None,
               corr=None,
               refine_idx=None,
               refine_integrate=None,
               refine_corr=None,
               trusted_region=None,
               trusted_pixels=None,
               reidx=None):
    shutil.copyfile(fn, fn.with_name("XDS.INP~"))
    
    lines = open(fn, "r", encoding = 'cp1252').readlines()
    if not lines:
        return

    pre = "!" if comment else ""

    new_lines = []
    HAS_BEAM_DIV_RELF_RANGE = False

    if "all" in jobs:
        jobs = XDSJOBS

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
            line = f"INCLUDE_RESOLUTION_RANGE= {lo_res:.2f} {hi_res:.2f}\n"
        elif wfac1 and "WFAC1" in line:
            line = f"WFAC1= {wfac1:.1f}\n"
        elif sp and "STRONG_PIXEL" in line:
            sp_line = f"{pre}STRONG_PIXEL= {sp}\n"
            line = sp_line
        elif indnumthre and "MINIMUM_FRACTION_OF_INDEXED_SPOTS" in line:
            line = f"MINIMUM_FRACTION_OF_INDEXED_SPOTS= {indnumthre:.2f}\n" 
        elif d and "J. Appl. Cryst. (2018)." in line:
            line = ""
        elif cut_frames:
            try:
                keyword = line.strip().split()[0]
            except IndexError:
                pass
            else:
                if keyword in ("DATA_RANGE=", "SPOT_RANGE=", "BACKGROUND_RANGE="):
                    data_begin, data_end = line[20:].split()
                    data_begin_cf = round(int(data_begin))
                    data_end_cf = round(int(data_end)*(1-cut_frames))
                    line = f"{keyword:20s}        {data_begin_cf:d} {data_end_cf:d}\n"
        elif comment and "UNIT_CELL_CONSTANTS" in line:
            line = pre + line
        elif comment and "SPACE_GROUP_NUMBER" in line:
            line = pre + line
        elif comment and "REIDX" in line:
            line = pre + line
        elif comment and "STRONG_PIXEL" in line:
            line = pre + line
        elif comment and "MINIMUM_FRACTION_OF_INDEXED_SPOTS" in line:
            line = pre + line
        elif dl and dl in line:
            line = ""
        elif jobs and ("JOB=" in line):
            continue
        elif processors:
            try:
                keyword = line.strip().split("=")[0]
            except IndexError:
                pass
            else:
                if keyword in ("MAXIMUM_NUMBER_OF_JOBS", "MAXIMUM_NUMBER_OF_PROCESSORS"):
                    line = f"{keyword}={processors:d}\n"
        elif center and "ORGX" in line and "ORGY" in line:
            line = f"ORGX= {center[0]:.2f}    ORGY= {center[1]:.2f}\n"
        elif untrusted and "UNTRUSTED_RECTANGLE" in line:
            line = "!" + line
        elif corr and "GEO_CORR=" in line:
            line = "!" + line
        elif axis and "ROTATION_AXIS" in line:
            line = f"ROTATION_AXIS= {axis[0]} {axis[1]} {axis[2]}\n"
        elif cam_len and "DETECTOR_DISTANCE" in line:
            line = f"DETECTOR_DISTANCE= {cam_len}\n"
        elif pixel_size and "QX" in line:
            line = f"QX= {pixel_size[0]}  QY= {pixel_size[1]}\n"
        elif refine_idx and "REFINE(IDXREF)" in line:
            line = f"REFINE(IDXREF)=   {' '.join(refine_idx)}\n"
        elif refine_integrate and "REFINE(INTEGRATE)" in line:
            line = f"REFINE(INTEGRATE)=   {' '.join(refine_integrate)}\n"
        elif refine_corr and "REFINE(CORRECT)" in line:
            line = f"REFINE(CORRECT)=   {' '.join(refine_corr)}\n"
        elif trusted_region and "TRUSTED_REGION" in line:
            line = f"TRUSTED_REGION= {trusted_region[0]} {trusted_region[1]}\n"
        elif trusted_pixels and "VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS" in line:
            line = f"VALUE_RANGE_FOR_TRUSTED_DETECTOR_PIXELS= {trusted_pixels[0]} {trusted_pixels[1]}\n"
        elif mosaicity and "BEAM_DIVERGENCE_E.S.D." in line:
            HAS_BEAM_DIV_RELF_RANGE = True
            line = f"BEAM_DIVERGENCE_E.S.D.= {mosaicity[0]:.3f}\n"
        elif mosaicity and "REFLECTING_RANGE_E.S.D." in line:
            HAS_BEAM_DIV_RELF_RANGE = True
            line = f"REFLECTING_RANGE_E.S.D.= {mosaicity[1]:.3f}\n"
        elif reidx and "REIDX=" in line:
            line = f"REIDX= {' '.join(reidx)}\n"
        if "Cryst." in line:
            line = ""


        new_lines.append(line)

    if apd:
        line = f"{apd}\n"
        new_lines.append(line)

    if mosaicity and HAS_BEAM_DIV_RELF_RANGE is False:
        line = f"BEAM_DIVERGENCE_E.S.D.=   {mosaicity[0]:.3f}\nREFLECTING_RANGE_E.S.D.=   {mosaicity[1]:.2f}\n"
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

    parser.add_argument("-s", "--spgr",
                        action="store", type=str, dest="spgr",
                        help="Update space group")

    parser.add_argument("-c", "--cell",
                        action="store", type=float, nargs=6, dest="cell",
                        help="Update unit cell parameters")
    
    parser.add_argument("-n", "--comment",
                        action="store_true", dest="comment",
                        help="Comment out unit cell / space group instructions")

    parser.add_argument("-e", "--max-error",
                        action="store", type=float, nargs=2, dest="cell_error",
                        help="Update the maximum cell error MAX_CELL_AXIS_ERROR / MAX_CELL_ANGLE_ERROR (default: 0.03 / 2.0)")

    parser.add_argument("-o", "--overload",
                        action="store", type=int, dest="overload_value",
                        help="Update the dynamical range max value (default: 130000)")

    parser.add_argument("-r", "--resolution",
                        action="store", type=float, nargs=2, dest="resolution",
                        help="Update resolution cut LOW_RES / HIGH_RES (default: 20 0.8)")

    parser.add_argument("-f", "--cut-frames",
                        action="store", type=float, dest="cut_frames",
                        help="Cut the last n*100 percent of frames (deault: 0.0)")

    parser.add_argument("-w", "--wfac1",
                        action="store", type=float, dest="wfac1",
                        help="parameter used for recognizing MISFITS (default: 1.0)")

    parser.add_argument("-a", "--append",
                        action="store", type=str, dest="append",
                        help="Append any VALID XDS input parameters")

    parser.add_argument("-dl","--delete_line",
                        action="store", type=str, dest="delete_line",
                        help="delete any line that is in the input file. BE CAREFUL when using this. Use it only to delete appended lines.")

    parser.add_argument("-sp","--StrongPixel",
                        action="store", type=float, dest="StrongPixel",
                        help="Parameter used for strong pixel threshold")

    parser.add_argument("-it", "--indexingNumberThreshold",
                        action="store", type=float, dest="indexingNumberThreshold",
                        help="Parameter to tune the threshold for percentage of spots that is indexed")

    parser.add_argument("-d","--delete_ref_line",
                        action="store_true", dest="delete_ref_line",
                        help="Delete the reference line since it is sometimes problematic")

    parser.add_argument("-m", "--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.add_argument("-j", "--jobs",
                        action="store", type=str, nargs="+", 
                        help="Specify which JOB should be performed by XDS: XYCORR, INIT, COLSPOT, IDXREF, DEFPIX, INTEGRATE, CORRECT. Specify `all` for all jobs.")
    parser.add_argument("-p", "--processors",
                        action="store", type=int, dest="processors", 
                        help="Specify MAXIMUM_NUMBER_OF_JOBS and MAXIMUM_NUMBER_OF_PROCESSORS.")

    parser.add_argument("-cen", "--center",
                        action="store", type=float, nargs=2, dest="center",
                        help="Update beam center positio.")

    parser.add_argument("-ax", "--axis",
                        action="store", type=float, nargs=3, dest="axis",
                        help="Update the rotation axis.")
                        
    parser.add_argument("-cam", "--cam_len",
                        action="store", type=float, dest="cam_len",
                        help="Update the camera length.")
                        
    parser.add_argument("-mos", "--mosaicity",
                        action="store", type=float, nargs=2, dest="mosaicity",
                        help="Update BEAM_DIVERGENCE_E.S.D. and REFLECTING_RANGE_E.S.D.")
                        
    parser.add_argument("-px", "--pixel_size",
                        action="store", type=float, nargs=2, dest="pixel_size",
                        help="Update camera physical pixel size")
                        
    parser.add_argument("-un", "--untrusted",
                        action="store", type=bool, dest="untrusted",
                        help="Comment UNTRUSTED_RECTANGLE")

    parser.add_argument("-co", "--corr",
                        action="store", type=bool, dest="corr",
                        help="Comment GEO_CORR")

    parser.add_argument("-ridx", "--refine_index",
                        action="store", type=str, nargs="*", dest="refine_index",
                        help="Comment refine index")

    parser.add_argument("-rint", "--refine_integrate",
                        action="store", type=str, nargs="*", dest="refine_integrate",
                        help="Comment refine integrate")

    parser.add_argument("-rcorr", "--refine_corr",
                        action="store", type=str, nargs="*", dest="refine_corr",
                        help="Comment refine correct")

    parser.add_argument("-tr", "--trusted_region",
                        action="store", type=float, nargs=2, dest="trusted_region",
                        help="Update the trusted region.")

    parser.add_argument("-tr_pix", "--trusted_pixels",
                        action="store", type=float, nargs=2, dest="trusted_pixels",
                        help="Update the trusted pixels.")

    parser.add_argument("-reidx", "--reidx",
                        action="store", type=str, nargs=12, dest="reidx",
                        help="Update the trusted pixels.")

    parser.set_defaults(cell=None,
                        spgr=None,
                        comment=False,
                        cell_error=(None, None),
                        match=None,
                        overload_value=None,
                        resolution=(None, None),
                        cut_frames=None,
                        wfac1=None,
                        append=None,
                        StrongPixel=None,
                        indexingNumberThreshold=None,
                        delete_ref_line=False,
                        delete_line=None,
                        jobs=(),
                        processors=None,
                        center=None,
                        axis=None,
                        cam_len=None,
                        mosaicity=None,
                        pixel_size=None,
                        untrusted=None,
                        corr=None,
                        refine_index=None,
                        trusted_region=None,
                        trusted_pixels=None,
                        reidx=None)
    
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
    append = options.append
    StrongPixel = options.StrongPixel
    indnumthre = options.indexingNumberThreshold
    del_ref = options.delete_ref_line
    del_line = options.delete_line
    jobs = options.jobs
    processors = options.processors
    center = options.center
    axis = options.axis
    cam_len = options.cam_len
    mosaicity = options.mosaicity
    pixel_size = options.pixel_size
    untrusted = options.untrusted
    corr = options.corr
    refine_index = options.refine_index
    refine_integrate = options.refine_integrate
    refine_corr = options.refine_corr
    trusted_region = options.trusted_region
    trusted_pixels = options.trusted_pixels
    reidx = options.reidx

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
                   apd=append,
                   jobs=jobs,
                   sp=StrongPixel, 
                   indnumthre = indnumthre, 
                   d=del_ref, 
                   dl=del_line,
                   processors = processors,
                   center=center,
                   axis=axis,
                   cam_len=cam_len,
                   mosaicity=mosaicity,
                   pixel_size=pixel_size,
                   untrusted=untrusted,
                   corr=corr,
                   refine_idx=refine_index,
                   refine_integrate=refine_integrate,
                   refine_corr=refine_corr,
                   trusted_region=trusted_region,
                   trusted_pixels=trusted_pixels,
                   reidx=reidx)

    print(f"\033[KUpdated {len(fns)} files")


if __name__ == '__main__':
    main()
