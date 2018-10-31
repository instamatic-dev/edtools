from concurrent.futures import ThreadPoolExecutor
import threading
import socket
import sys, os
from pathlib import Path

import subprocess as sp
from extract_xds_info import xds_parser

try:
    from instamatic import config
    HOST = config.cfg.indexing_server_host
    PORT = config.cfg.indexing_server_port
    BUFF = 1024
except ImportError:
    pass

DEVNULL = open(os.devnull, 'w')

rlock = threading.RLock()


def parse_fns(fns):
    """Parse list of filenames and resolve wildcards"""
    new_fns = []
    for fn in fns:
        if fn.is_dir():
            new_fns.extend(list(fn.glob("**/XDS.INP")))
        else:  
            new_fns.append(fn)
    new_fns = [fn for fn in new_fns if "reprocess" in str(fn)]
    new_fns = [fn.resolve() for fn in new_fns]
    return new_fns


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


def parse_xds(path):
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
                msg += p.cell_info()
                msg += "\n"
                msg += p.integration_info()

    print(msg)


def xds_index(path):
    plat = sys.platform
    if plat == "linux":
        try:
            p = sp.Popen("xds", cwd=str(path), stdout=DEVNULL)
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)
    elif plat == "win32":
        try:
            p = sp.Popen("bash -c xds 2>&1 >/dev/null", cwd=str(path))
            p.wait()
        except Exception as e:
            print("ERROR in subprocess call:", e)
    else:
        raise RuntimeError

    try:
        parse_xds(path)
    except Exception as e:
        print("ERROR parsing CORRECT.LP:", e)


def main():
    fns = sys.argv[1:]
    
    if not fns:
        fns = [Path(".")]
    else:
        fns = [Path(fn) for fn in fns]

    fns = parse_fns(fns)

    max_connections = 4

    with ThreadPoolExecutor(max_workers=max_connections) as executor:
        futures = []

        for fn in fns:
            drc = fn.parent
            f = executor.submit(connect, drc)
            # f = executor.submit(xds_index, drc)
            futures.append(f)
 
        for future in futures:
            ret = future.result()


if __name__ == '__main__':
    main()
