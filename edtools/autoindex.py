from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import sys, os
from pathlib import Path
from .utils import parse_args_for_fns

import subprocess as sp

from .extract_xds_info import xds_parser

try:
    from instamatic import config
    HOST = config.settings.indexing_server_host
    PORT = config.settings.indexing_server_port
    BUFF = 1024
except ImportError:
    HOST, PORT = None, None

DEVNULL = open(os.devnull, 'w')
platform = sys.platform

if platform == "win32":
    from .wsl import bash_exe


XDSJOBS = ("XYCORR", "INIT", "COLSPOT", "IDXREF", "DEFPIX", "INTEGRATE", "CORRECT")

rlock = threading.RLock()


def clear_files(path: str) -> None:
    """Clear  LP files"""
    for job in "DEFPIX", "INTEGRATE", "CORRECT":
        fn = (path / job).with_suffix(".LP")
        if fn.exists():
            os.remove(fn)


def connect(payload: str) -> None:
    """Try to connect to `instamatic` indexing server

    Parameters
    ----------
    payload : str
        Directory where XDS should be run.
    """
    payload = str(payload).encode()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        with rlock:
            print("Sending job to server...", end=" ")
            s.connect((HOST, PORT))
            s.send(payload)
            data = s.recv(BUFF).decode()
            print(data)

        data = s.recv(BUFF).decode()

        with rlock:
            print(data)


def parse_xds(path: str, sequence: int=0) -> None:
    """Parse XDS output (CORRECT.LP) and print summary about indexing progress
    to the screen.
    
    Parameters
    ----------
    path : str
        Path in which XDS has been run
    sequence : int
        Sequence number, needed for output and house-keeping
    """
    drc = Path(path)
    correct_lp = drc / "CORRECT.LP"

    lookBack = 160

    # rlock prevents messages getting mangled with 
    # simultaneous print statements from different threads
    with rlock:
        if correct_lp.exists():
        # if all files exist, try parsing CORRECT.LP
            try:
                p = xds_parser(correct_lp)
            except UnboundLocalError:
                msg = f"{sequence: 4d}: {drc} -> Indexing completed but no cell reported..."
            else:
                msg = "\n"
                msg += p.cell_info(sequence=sequence)
                msg += "\n"
                msg += p.info_header(hline=False)
                msg += p.integration_info(sequence=sequence)

            print(msg)
        else:
            for i, job in enumerate(XDSJOBS):
                error = None
                fn = (drc / job).with_suffix(".LP")
                if fn.exists():
                    with open(fn, "rb") as f:
                        f.seek(-lookBack, 2)
                        lines = f.readlines()

                    for line in lines:
                        if b"ERROR" in line:
                            error = line.decode()
                            error = error.split("!!!")[-1].strip()

                    if error:
                        msg = f"{sequence: 4d}: {drc} -> Error in {job}: {error}"
                        print(msg)
                        return



def xds_index(path: str, sequence: int=0, clear: bool=True, parallel: bool=True) -> None:
    """Run XDS at given path.
    
    Parameters
    ----------
    path : str
        Run XDS in this directory, expects XDS.INP in this directory
    sequence : int
        Sequence number, needed for output and house-keeping
    clear : bool
        Clear some LP files before running XDS
    parallel : bool
        Call `xds_par` rather than `xds`
    """
    if clear:
        clear_files(path)

    cmd = "xds_par" if parallel else "xds"

    cwd = str(path)

    if platform == "win32":
        try:
            p = sp.Popen(f"{bash_exe} -ic {cmd} 2>&1 >/dev/null", cwd=cwd)
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)
    else:
        try:
            p = sp.Popen(cmd, cwd=cwd, stdout=DEVNULL)
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)

    try:
        parse_xds(path, sequence=sequence)
    except Exception as e:
        print("ERROR:", e)



def main():
    import argparse

    description = "Program to automate the indexing of a large series of data sets from a serial crystallography experiment."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
        
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="List of XDS.INP files or list of directories. If a list of directories is given "
                        "the program will find all XDS.INP files in the subdirectories. If no arguments are given "
                        "the current directory is used as a starting point.")

    parser.add_argument("-s","--server",
                        action="store_true", dest="use_server",
                        help="Use instamatic server for indexing")

    parser.add_argument("-m", "--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.add_argument("-u", "--unprocessed_only",
                        action="store_true", dest="unprocessed_only",
                        help="Run XDS only in unprocessed directories (i.e. no XYCORR.LP)")

    parser.add_argument("-j", "--jobs",
                        action="store", type=int, dest="n_jobs",
                        help="Number of jobs to run in parallel")

    parser.set_defaults(use_server=False,
                        match=None,
                        unprocessed_only=False,
                        n_jobs=1,
                        )
    
    options = parser.parse_args()

    use_server = options.use_server
    match = options.match
    unprocessed_only = options.unprocessed_only
    n_jobs = options.n_jobs
    args = options.args

    fns = parse_args_for_fns(args, name="XDS.INP", match=match)

    if unprocessed_only:
        fns = [fn for fn in fns if not fn.with_name("XYCORR.LP").exists()]
        print(f"Filtered directories which have already been processed, {len(fns)} left")

    max_connections = 1

    with ThreadPoolExecutor(max_workers=max_connections) as executor:
        futures = []

        for i, fn in enumerate(fns):
            drc = fn.parent

            if use_server:
                f = executor.submit(connect, drc)
            else:
                f = executor.submit(xds_index, drc, i)
            futures.append(f)
 
        for future in futures:
            ret = future.result()

    for i, fn in enumerate(fns):
        drc = fn.parent

        with open(drc / "XDSCONV.INP", "w") as f:
            print(f"""
INPUT_FILE= XDS_ASCII.HKL
OUTPUT_FILE= shelx.hkl  SHELX    ! Warning: do _not_ name this file "temp.mtz" !
FRIEDEL'S_LAW= FALSE             ! default is FRIEDEL'S_LAW=TRUE""", file=f)
            
        if platform == "win32":
            sp.run(f"{bash_exe} -ic xdsconv 2>&1 >/dev/null", cwd=drc)
        else:
            sp.run("xdsconv 2>&1 >/dev/null", cwd=drc, shell=True)


if __name__ == '__main__':
    main()
