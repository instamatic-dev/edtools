from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import sys, os
from pathlib import Path
from .utils import parse_args_for_fns

import subprocess as sp
from .extract_xds_info import xds_parser
import platform

try:
    from instamatic import config
    HOST = config.cfg.indexing_server_host
    PORT = config.cfg.indexing_server_port
    BUFF = 1024
except ImportError:
    HOST, PORT = None, None

DEVNULL = open(os.devnull, 'w')
platform_sys = sys.platform

"""Check the bit version of the system so that command bash does not get confused"""
is32bit = (platform.architecture()[0] == '32bit')
system32 = os.path.join(os.environ['SystemRoot'], 'SysNative' if is32bit else 'System32')
bash = os.path.join(system32, 'bash.exe')

rlock = threading.RLock()


def connect(payload):
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


def parse_xds(path, sequence=0):
    """Parse the XDS output file `CORRECT.LP` and print a summary"""
    fn = Path(path) / "CORRECT.LP"
    
    # rlock prevents messages getting mangled with 
    # simultaneous print statements from different threads
    with rlock:
        if not fn.exists():
            msg = f"{path}: Automatic indexing failed..."
        else:
            try:
                p = xds_parser(fn)
            except UnboundLocalError:
                msg = f"{path}: Automatic indexing completed but no cell reported..."
            else:
                msg = "\n"
                msg += p.cell_info(sequence=sequence)
                msg += "\n"
                msg += p.integration_info(sequence=sequence)

    print(msg)


def xds_index(path, i=0):
    corr = path / "CORRECT.LP"
    if corr.exists():
        os.remove(corr)

    cwd = str(path)

    if platform_sys == "win32":
        try:
            p = sp.Popen("%s -ic xds 2>&1 >/dev/null" % bash, cwd=cwd)
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)
    else:
        try:
            p = sp.Popen("xds", cwd=cwd, stdout=DEVNULL)
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)

    try:
        parse_xds(path, sequence=i)
    except Exception as e:
        print("ERROR parsing CORRECT.LP:", e)


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

    parser.add_argument("--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.set_defaults(use_server=False,
                        match=None)
    
    options = parser.parse_args()

    use_server = options.use_server
    match = options.match
    args = options.args

    fns = parse_args_for_fns(args, name="XDS.INP", match=match)

    max_connections = 4

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


if __name__ == '__main__':
    main()
