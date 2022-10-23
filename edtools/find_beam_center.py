from .utils import parse_args_for_fns
import numpy as np
from scipy import ndimage
from scipy import interpolate
from skimage.registration import phase_cross_correlation
import scipy.ndimage as ndimage
from .update_xds import update_xds

def read_adsc(fname: str) -> (np.array, dict):
    """read in the file."""
    with open(fname, 'rb', buffering=0) as infile:
        try:
            header = readheader(infile)
        except BaseException:
            raise Exception('Error processing adsc header')
        # banned by bzip/gzip???
        try:
            infile.seek(int(header['HEADER_BYTES']), 0)
        except TypeError:
            # Gzipped does not allow a seek and read header is not
            # promising to stop in the right place
            infile.close()
            infile = open(fname, 'rb', buffering=0)
            infile.read(int(header['HEADER_BYTES']))
        binary = infile.read()
    # infile.close()

    # now read the data into the array
    dim1 = int(header['SIZE1'])
    dim2 = int(header['SIZE2'])
    data = np.frombuffer(binary, np.uint16)
    if swap_needed(header):
        data.byteswap(True)
    try:
        data.shape = (dim2, dim1)
    except ValueError:
        raise OSError(f'Size spec in ADSC-header does not match size of image data field {dim1}x{dim2} != {data.size}')

    return data, header

def write_adsc(fname: str, data: np.array, header: dict = {}):
    """Write adsc format."""
    if 'SIZE1' not in header and 'SIZE2' not in header:
        dim2, dim1 = data.shape
        header['SIZE1'] = dim1
        header['SIZE2'] = dim2

    out = b'{\n'
    for key in header:
        out += '{:}={:};\n'.format(key, header[key]).encode()
    if 'HEADER_BYTES' in header:
        pad = int(header['HEADER_BYTES']) - len(out) - 2
    else:
        #         hsize = ((len(out) + 23) // 512 + 1) * 512
        hsize = (len(out) + 533) & ~(512 - 1)
        out += f'HEADER_BYTES={hsize:d};\n'.encode()
        pad = hsize - len(out) - 2
    out += b'}' + (pad + 1) * b'\x00'
    assert len(out) % 512 == 0, 'Header is not multiple of 512'

    # NOTE: XDS can handle only "SMV" images of TYPE=unsigned_short.
    dtype = np.uint16
    data = np.round(data, 0).astype(dtype, copy=False)  # copy=False ensures that no copy is made if dtype is already satisfied
    if swap_needed(header):
        data.byteswap(True)

    with open(fname, 'wb') as outf:
        outf.write(out)
        outf.write(data.tostring())


def readheader(infile):
    """read an adsc header."""
    header = {}
    line = infile.readline()
    bytesread = len(line)
    while b'}' not in line:
        string = line.decode().strip()
        if '=' in string:
            (key, val) = string.split('=')
            val = val.strip(';')
            key = key.strip()
            header[key] = val
        line = infile.readline()
        bytesread = bytesread + len(line)
    return header
    
def swap_needed(header: dict) -> bool:
    if 'BYTE_ORDER' not in header:
        # logger.warning("No byte order specified, assuming little_endian")
        BYTE_ORDER = 'little_endian'
    else:
        BYTE_ORDER = header['BYTE_ORDER']
    if 'little' in BYTE_ORDER and np.little_endian:
        return False
    elif 'big' in BYTE_ORDER and not np.little_endian:
        return False
    elif 'little' in BYTE_ORDER and not np.little_endian:
        return True
    elif 'big' in BYTE_ORDER and np.little_endian:
        return True

def find_peak_max(arr: np.ndarray, sigma: int, m: int = 50, w: int = 10, kind: int = 3) -> (float, float):
    """Find the index of the pixel corresponding to peak maximum in 1D pattern
    `arr`.

    First, the pattern is smoothed using a gaussian filter with standard
    deviation `sigma` The initial guess takes the position corresponding
    to the largest value in the resulting pattern A window of size 2*w+1
    around this guess is taken and expanded by factor `m` to to
    interpolate the pattern to get the peak maximum position with
    subpixel precision.
    """
    y1 = ndimage.filters.gaussian_filter1d(arr, sigma)
    c1 = np.argmax(y1)  # initial guess for beam center

    win_len = 2 * w + 1

    try:
        r1 = np.linspace(c1 - w, c1 + w, win_len)
        f = interpolate.interp1d(r1, y1[c1 - w: c1 + w + 1], kind=kind)
        r2 = np.linspace(c1 - w, c1 + w, win_len * m)  # extrapolate for subpixel accuracy
        y2 = f(r2)
        c2 = np.argmax(y2) / m  # find beam center with `m` precision
    except ValueError:  # if c1 is too close to the edges, return initial guess
        return c1

    return c2 + c1 - w

def find_beam_center(img: np.ndarray, sigma: int = 30, m: int = 100, kind: int = 3) -> (float, float):
    """Find the center of the primary beam in the image `img` The position is
    determined by summing along X/Y directions and finding the position along
    the two directions independently.

    Uses interpolation by factor `m` to find the coordinates of the
    pimary beam with subpixel accuracy.
    """
    img_thresh = img.copy()
    img_thresh[img_thresh<7000] = 0
    xx = np.sum(img_thresh, axis=1)
    yy = np.sum(img_thresh, axis=0)

    cx = find_peak_max(xx, sigma, m=m, kind=kind)
    cy = find_peak_max(yy, sigma, m=m, kind=kind)

    center = np.array([cx, cy])
    return center
    
def translate_image(arr, shift: np.array) -> np.array:
    """Translate an image according to shift. Shift should be a 2D numpy array"""
    img = np.zeros(arr.shape, dtype=np.uint16)
    shift = np.int16(shift)
    avg = np.uint16(arr.mean())
    if shift[0] >= 0 and shift[1] >= 0:
        if shift[0] == 0 and shift[1] == 0:
            return arr
        elif shift[0] == 0:
            img[:, shift[1]:] = arr[:, :-shift[1]]
            img[:, :shift[1]] = avg
        elif shift[1] == 0:
            img[shift[0]:, :] = arr[:-shift[0], :]
            img[:shift[0], :] = avg
        else:
            img[shift[0]:, shift[1]:] = arr[:-shift[0], :-shift[1]]
            img[:shift[0], :] = avg
            img[:, :shift[1]] = avg
    elif shift[0] >= 0 and shift[1] < 0:
        if shift[0] == 0:
            img[:, :shift[1]] = arr[:, -shift[1]:]
            img[:, shift[1]:] = avg
        else:
            img[shift[0]:, :shift[1]] = arr[:-shift[0], -shift[1]:]
            img[:shift[0], :] = avg
            img[:, shift[1]:] = avg
    elif shift[0] < 0 and shift[1] >= 0:
        if shift[1] == 0:
            img[:shift[0], :] = arr[-shift[0]:, :]
            img[shift[0]:, :] = avg
        else:
            img[:shift[0], shift[1]:] = arr[-shift[0]:, :-shift[1]]
            img[shift[0]:, :] = avg
            img[:, :shift[1]] = avg
    elif shift[0] < 0 and shift[1] < 0:
        img[:shift[0], :shift[1]] = arr[-shift[0]:, -shift[1]:]
        img[shift[0]:, :] = avg
        img[:, shift[1]:] = avg

    return img

def main():
    import argparse

    description = "Program to find beam center and translate sequence of images to this beam center."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
        
    parser.add_argument("args",
                        type=str, nargs="*", metavar="FILE",
                        help="List of XDS.INP files or list of directories. If a list of directories is given "
                        "the program will find all XDS.INP files in the subdirectories. If no arguments are given "
                        "the current directory is used as a starting point.")
    parser.add_argument("-m", "--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")
    parser.add_argument("-stre", "--stretch",
                        action="store", type=float, nargs=2, dest="stretch",
                        help="Correct for the elliptical distortion")

    parser.set_defaults(match=None,
                        stretch=None)

    options = parser.parse_args()
    
    match = options.match
    args = options.args

    XDS_input_path = parse_args_for_fns(args = args, name="XDS.INP", match=match)

    
    for fn in XDS_input_path:
        try:
            data_path = fn.parent/'data'
            print(data_path)
            img_list = list(data_path.glob("*.img"))
            img_first = str(img_list[0])
            data, header = read_adsc(img_first)
            center_x, center_y = find_beam_center(data)
            #center_x, center_y = (268, 249)
            template = data[int(round(center_x-16)):int(round(center_x+16)), 
                            int(round(center_y-16)):int(round(center_y+16))].copy()
            center_x_new, center_y_new = find_beam_center(template, sigma=5)
            print(center_x_new, center_y_new)
            update_xds(fn, jobs=(), center=(center_y-16+center_y_new+0.8, center_x-16+center_x_new+0.8))
            
            for img in img_list[1:]:
                img = str(img)
                data, header = read_adsc(img)
                #center = find_beam_center(data)
                #center_area = data[round(center_y)-10:round(center_y)+10, round(center_x)-10:round(center_x)+10]
                center  = find_beam_center(data[int(round(center_x-16)):int(round(center_x+16)), 
                                            int(round(center_y-16)):int(round(center_y+16))],sigma=5)
                shift = (center_x_new-center[0], center_y_new-center[1])
                #shift, error, phasediff = phase_cross_correlation(template, center_area, upsample_factor=10)
                print(shift)
                data = ndimage.shift(data, shift, output=np.uint16, mode='nearest')
                header['BEAM_CENTER_X'] = center_y
                header['BEAM_CENTER_Y'] = center_x
                write_adsc(img, data, header)
        except:
            print(f'Beam center finding was interrupted: {data_path}')

if __name__ == '__main__':
    main()
