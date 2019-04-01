from pathlib import Path
import matplotlib.pyplot as plt
from scipy import ndimage
import yaml
import numpy as np
import os, sys


def rotation_axis_to_xyz(rotation_axis, invert=False, setting='xds'):
    """Convert rotation axis angle to XYZ vector compatible with 'xds', or 'dials'
    Set invert to 'True' for anti-clockwise rotation
    """
    if invert:
        rotation_axis += np.pi

    rot_x = np.cos(rotation_axis)
    rot_y = np.cos(rotation_axis+np.pi/2)
    rot_z = 0

    if setting == 'dials':
        return rot_x, -rot_y, rot_z
    elif setting == 'xds':
        return rot_x, rot_y, rot_z
    else:
        raise ValueError("Must be one of {'dials', 'xds'}")


def rotation_matrix(axis, theta):
    """Calculates the rotation matrix around axis of angle theta (radians)"""

    # axis = axis/np.sqrt(np.dot(axis,axis))

    l = np.sqrt(np.dot(axis, axis))
    axis = axis/l

    a = np.cos(theta/2)
    b, c, d = -1*axis*np.sin(theta/2)

    return np.array([[a*a+b*b-c*c-d*d,      2*(b*c-a*d),          2*(b*d+a*c)],
                     [    2*(b*c+a*d),  a*a+c*c-b*b-d*d,          2*(c*d-a*b)],
                     [    2*(b*d-a*c),      2*(c*d+a*b),     a*a+d*d-b*b-c*c]])

def make_2d_rotmat(theta):
    """Take angle in radians, and return 2D rotation matrix"""
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])
    return R


def random_sample(arr, n):
    """Select random sample of `n` rows from array"""
    indices = np.random.choice(arr.shape[0], n, replace=False)
    return arr[indices]


def xyz2cyl(arr):
    """Take a set of reflections in XYZ and convert to polar (cylindrical) coordinates"""
    sx, sy, sz = arr.T
    out = np.empty((len(arr), 2))
    np.hypot(sx, sy, out=out[:,0])
    np.arctan2(sz, out[:,0], out=out[:,1])
    np.arctan2(sy, sx, out=out[:,0])
    return out


def cylinder_histo(xyz, bins=(1000, 500)):
    """Take reciprocal lattice vectors in XYZ format and output cylindrical projection.
    `Bins` gives the resolution of the 2D histogram."""
    i,j = np.triu_indices(len(xyz), k=1)
    diffs = xyz[i] - xyz[j]
    polar = xyz2cyl(diffs)
    
    px, py = polar.T
    H, xedges, yedges = np.histogram2d(px, py, bins=bins, range=[[-np.pi,np.pi,],[-np.pi/2,np.pi/2]])
    
    return H, xedges, yedges


def plot_histo(H, xedges, yedges, title="Histogram"):
    """Plot the histogram of the cylindrical projection."""
    plt.imshow(H.T, interpolation='nearest', origin='low',
            extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
              vmax=np.percentile(H, 99))
    plt.title(title)
    plt.xlim(-np.pi, np.pi)
    plt.ylim(-np.pi/2, np.pi/2)
    plt.xlabel("phi ($\pi$)")
    plt.ylabel("theta ($\pi$)")
    plt.show()


def make(arr, omega: float, beam_center: [float, float], osc_angle: float, pixelsize: float, wavelength: float):  
    """
    Prepare xyz (reciprocal space coordinates) from `arr`, 
    which is the list of reflections read from XDS (SPOT.XDS)

    omega: rotation axis (degrees), which is defined by the angle between x 
        (horizontal axis pointing right) and the rotation axis going in clockwise direction
    beam_center: coordinates of the primary beam, read from XDS.INP
    osc_angle: oscillation_angle (degrees) per frame, multiplied by the average frame number
        that a reflection appears on (column 3 in arr)
    pixelsize: defined in px/Angstrom
    wavelength: in Angstrom

    Note that:
        1. omega is flipped
        2. x<->y are flipped
    This is to ensure to match the XDS convention with the one I'm used to
    """

    omega = -omega  # NOTE 1

    osc_angle_rad = np.radians(osc_angle)
    omega_rad = np.radians(omega)
    r = make_2d_rotmat(omega_rad)
    
    reflections = arr[:,0:2] - beam_center
    angle = arr[:,2] * osc_angle_rad
    
    reflections *= pixelsize
    refs_ = np.dot(reflections, r)
    
    y, x = refs_.T  # NOTE 2

    R = 1/wavelength
    C = R - np.sqrt(R**2 - x**2 - y**2).reshape(-1,1)
    xyz = np.c_[x * np.cos(angle), y, -x*np.sin(angle)] + C * np.c_[-np.sin(angle), np.zeros_like(angle), -np.cos(angle)]
    
    return xyz, angle


def optimize(arr, omega_start: float, beam_center: [float, float], osc_angle: float, pixelsize: float, wavelength: float, 
             plusminus: int=180, step: int=10, hist_bins: (int, int)=(1000, 500), plot: bool=False) -> float:
    """
    Optimize the value of omega around the given point.

    omega_start: defines the starting angle
    step, plusminus: together with omega_start define the range of values to loop over
    hist_bins: size of the 2d histogram to produce the final phi/theta plot
    plot: toggle to plot the histogram after each step
    """

    r = np.arange(omega_start-plusminus, omega_start+plusminus, step)
    
    best_score = 0
    best_omega = 0
    
    for omega in r:
        xyz, c = make(arr, omega, beam_center, osc_angle, pixelsize, wavelength)
        
        nvectors = sum(range(len(xyz)))
        
        H, xedges, yedges = cylinder_histo(xyz, bins=hist_bins)
      
        var = np.var(H)
        
        print(f"Omega: {omega:8.2f}, variance: {var:5.2f}")
      
        if plot:
            plot_histo(H, xedges, yedges, title=f"omega={omega:.2f}$^\circ$ | variance: {var:.2f}")

        xvals.append(omega)
        vvals.append(var)
        
        if var > best_score:
            best_omega = omega
            best_score = var
    
    print(f"Best omega: {best_omega:.2f}; score: {best_score:.2f}")    
    
    return best_omega


def parse_xds_inp(fn):
    """
    Parse the XDS.INP file to find the required numbers for the optimization
    Looks for wavelength, pixelsize, beam_center, oscillation range
    """
    with open(fn, "r") as f:
        for line in f:
            line = line.split("!", 1)[0]
            
            if "X-RAY_WAVELENGTH" in line:
                wavelength = float(line.rsplit("X-RAY_WAVELENGTH=")[1].split()[0])
            if "ORGX=" in line:
                orgx = float(line.rsplit("ORGX=")[1].split()[0])
            if "ORGY=" in line:
                orgy = float(line.rsplit("ORGY=")[1].split()[0])
            if "OSCILLATION_RANGE=" in line:
                osc_angle = float(line.rsplit("OSCILLATION_RANGE=")[1].split()[0])
            if "QX=" in line:
                qx = float(line.rsplit("QX=")[1].split()[0])
            if "QY=" in line:
                qy = float(line.rsplit("QY=")[1].split()[0])
            if "DETECTOR_DISTANCE=" in line:
                distance = float(line.rsplit("DETECTOR_DISTANCE=")[1].split()[0])

    pixelsize = qx / (distance * wavelength)

    return np.array((orgx, orgy)), osc_angle, pixelsize, wavelength


def main():
    usage = """Use this script to find the rotation axis
Reads XDS.INP for parameters and SPOT.XDS (COLSPOT) for spot positions

Usage: python find_rotation_axis.py XDS.INP"""

    xds_inp = sys.argv[1:2]
    if not xds_inp:
        xds_inp = Path("XDS.INP")
    else:
        xds_inp = Path(xds_inp[0])

    if not xds_inp.exists():
        print(f"No such file: {xds_inp}\n")
        print(usage)
        sys.exit()

    beam_center, osc_angle, pixelsize, wavelength = parse_xds_inp(xds_inp)

    print(f"Beam center: {beam_center[0]:.2f} {beam_center[1]:.2f}")
    print(f"Oscillation angle (degrees): {osc_angle}")
    print(f"Pixelsize: {pixelsize:.4f} px/Angstrom")
    print(f"Wavelength: {wavelength:.5f} Angstrom")

    spot_xds = xds_inp.with_name("SPOT.XDS")

    if not spot_xds.exists():
        print(f"Cannot find file: {spot_xds}")
        sys.exit()

    arr = np.loadtxt(spot_xds)
    print(arr.shape)

    hist_bins = 1000, 500
    
    global xvals
    global vvals
    xvals = []
    vvals = []
    
    omega_start = omega_tmp = 0
    omega_global = omega_local = omega_fine = 0
    
    omega_global = omega_tmp = optimize(arr, omega_tmp, beam_center, osc_angle, pixelsize, wavelength, plusminus=180, step=5, hist_bins=hist_bins)
    
    omega_local = omega_tmp = optimize(arr, omega_tmp, beam_center, osc_angle, pixelsize, wavelength, plusminus=5, step=1, hist_bins=hist_bins)
    
    omega_fine = omega_tmp = optimize(arr, omega_tmp, beam_center, osc_angle, pixelsize, wavelength, plusminus=1, step=0.1, hist_bins=hist_bins)
    
    omega_final = omega_tmp
    
    print("---")
    print(f"Best omega (global search): {omega_global:.3f}")
    print(f"Best omega (local search): {omega_local:.3f}")
    print(f"Best omega (fine search): {omega_fine:.3f}")
    
    xyz, c = make(arr, omega_final, beam_center, osc_angle, pixelsize, wavelength)
    H, xedges, yedges = cylinder_histo(xyz)
    plot_histo(H, xedges, yedges, title=f"omega={omega_final:.2f}$^\circ$")

    # Plot rotation axis distribution curve
    plt.scatter(xvals, vvals, marker="+", lw=1.0, color="red")
    plt.xlabel("Rotation axis position ($^\circ$)")
    plt.ylabel("Variance of the polar coordinate histogram")
    plt.title(f"Rotation axis determination | Maximum @ {omega_final:.2f}$^\circ$")
    plt.show()

    omega_deg = omega_final
    omega_rad = np.radians(omega_final)
    
    print(f"\nRotation axis found: {omega_deg:.2f} deg. / {omega_rad:.3f} rad.")
    
    print(" - Instamatic (config/camera/camera_name.yaml)")
    omega_instamatic = omega_rad
    print(f"    rotation_axis_vs_stage_xy: {omega_instamatic:.3f}")
    
    print(" - XDS (positive rotation)")
    rot_x_xds, rot_y_xds, rot_z_xds = rotation_axis_to_xyz(omega_rad, setting="xds")
    print(f"    ROTATION_AXIS= {rot_x_xds:.4f} {rot_y_xds:.4f} {rot_z_xds:.4f}")
    print(" - XDS (negative rotation)")
    rot_x_xds, rot_y_xds, rot_z_xds = rotation_axis_to_xyz(omega_rad, setting="xds", invert=True)
    print(f"    ROTATION_AXIS= {rot_x_xds:.4f} {rot_y_xds:.4f} {rot_z_xds:.4f}")
    
    print(" - DIALS (positive rotation)")
    rot_x_dials, rot_y_dials, rot_z_dials = rotation_axis_to_xyz(omega_rad, setting="dials")
    print(f"    geometry.goniometer.axes={rot_x_dials:.4f},{rot_y_dials:.4f},{rot_z_dials:.4f}")
    print(" - DIALS (negative rotation)")
    rot_x_dials, rot_y_dials, rot_z_dials = rotation_axis_to_xyz(omega_rad, setting="dials", invert=True)
    print(f"    geometry.goniometer.axes={rot_x_dials:.4f},{rot_y_dials:.4f},{rot_z_dials:.4f}")
    
    print(" - PETS (.pts)")
    omega_pets = omega_deg
    if omega_pets < 0:
        omega_pets += 360 
    print(f"    omega {omega_pets:.2f}")
    
    print(" - RED (.ed3d)")
    omega_red = omega_deg
    print(f"    ROTATIONAXIS    {omega_red:.4f}")


if __name__ == '__main__':
    main()