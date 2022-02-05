from pathlib import Path
import shutil
from .utils import parse_args_for_fns
import numpy as np

def update_cif(fn, 
               wavelength=None,
               description=None,
               color=None,
               remove_hkl=None,
               reply=None,
               instrument=None,):
    shutil.copyfile(fn, fn.with_name("~"+fn.name))
    
    lines = open(fn, "r", encoding='cp1252').readlines()
    if not lines:
        return

    new_lines = []
    reflection_num = np.random.randint(1000, 10000)
    cif_wavelength = 0
    reflection_theta_min = 0
    reflection_theta_max = 0
    file_name = fn.stem
    aniso = False

    if instrument:
        instrument_path = Path(__file__).parent / 'instrument'
        instruments = instrument_path.glob('*.cif')
        instrument_lines = None
        for instru in instruments:
            if instrument == instru.stem:
                instrument_lines = open(instru, "r", encoding='cp1252').readlines()
                break
        for line in instrument_lines:
            try:
                if "_diffrn_detector" == line.split()[0]:
                    detector = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_detector_type" in line:
                    detector_type = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_measurement_device" == line.split()[0]:
                    measurement_device = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_measurement_device_type" in line:
                    measurement_device_type = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_measurement_method" in line:
                    measurement_method = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_radiation_monochromator" in line:
                    radiation_monochromator = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_radiation_probe" in line:
                    radiation_probe = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_radiation_type" in line:
                    radiation_type = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_radiation_wavelength" in line:
                    radiation_wavelength = float(line.split()[-1])
                elif "_diffrn_source" == line.split()[0]:
                    source = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_source_type" in line:
                    source_type = "'" + line.split("'")[-2] + "'"
                elif "_diffrn_source_target" in line:
                    source_target = "'" + line.split("'")[-2] + "'"
            except IndexError:
                pass

    for line in lines:
        if "_diffrn_reflns_number" in line:
            reflection_num = int(line.split()[-1])
        elif "_diffrn_radiation_wavelength" in line:
            cif_wavelength = float(line.split()[-1])
        elif "_diffrn_reflns_theta_min" in line:
            reflection_theta_min =  float(line.split()[-1])
        elif "_diffrn_reflns_theta_max" in line:
            reflection_theta_max =  float(line.split()[-1])
        elif "_diffrn_reflns_theta_full" in line:
            reflection_theta_full =  float(line.split()[-1])
        elif "_diffrn_reflns_av_R_equivalents" in line:
            Rint = float(line.split()[-1])
        elif "_refine_ls_wR_factor_ref" in line:
            wR2 = float(line.split()[-1])
        elif "_refine_ls_R_factor_gt" in line:
            R1 = float(line.split()[-1])
        elif "_atom_site_aniso_label" in line:
            aniso = True
        elif "_diffrn_measured_fraction_theta_full" in line:
            completeness = float(line.split()[-1])
        elif "_refine_ls_shift/su_max" in line:
            shift = float(line.split()[-1])

    for line in lines:
        try:
            if line.startswith('data_'):
                line = f"data_{file_name}"
            elif "_cell_measurement_reflns_used" in line:
                cell_measurement_line = f"_cell_measurement_reflns_used   {reflection_num}\n"
                line = cell_measurement_line
            elif "_cell_measurement_theta_min" in line:
                cell_theta_min_line = f"_cell_measurement_theta_min   {reflection_theta_min:.3f}\n"
                if wavelength:
                    cell_theta_min_line = f"_cell_measurement_theta_min   {reflection_theta_min*wavelength/cif_wavelength:.3f}\n"
                line = cell_theta_min_line
            elif "_cell_measurement_theta_max" in line:
                cell_theta_max_line = f"_cell_measurement_theta_max   {reflection_theta_max:.3f}\n"
                if wavelength:
                    cell_theta_max_line = f"_cell_measurement_theta_max   {reflection_theta_max*wavelength/cif_wavelength:.3f}\n"
                line = cell_theta_max_line
            elif description and "_exptl_crystal_description" in line:
                description_line = f"_exptl_crystal_description        '{description}'\n"
                line = description_line
            elif color and "_exptl_crystal_colour" in line:
                color_line = f"_exptl_crystal_colour             '{color}'\n"
                line = color_line
            elif "_diffrn_radiation_wavelength" in line:
                line = f"_diffrn_radiation_wavelength   {wavelength:.4f}\n"
            elif "_diffrn_reflns_theta_min" in line:
                if wavelength:
                    line = f"_diffrn_reflns_theta_min   {reflection_theta_min*wavelength/cif_wavelength:.3f}\n"
            elif "_diffrn_reflns_theta_max" in line:
                if wavelength:
                    line = f"_diffrn_reflns_theta_max   {reflection_theta_max*wavelength/cif_wavelength:.3f}\n"
            elif "_diffrn_reflns_theta_full" in line:
                if wavelength:
                    line = f"_diffrn_reflns_theta_full   {reflection_theta_full*wavelength/cif_wavelength:.3f}\n"
            elif "_exptl_absorpt_correction_type" in line:
                line = f"_exptl_absorpt_correction_type   'none'\n"
            elif instrument and "_diffrn_measurement_device_type" in line:
                line = f"_diffrn_measurement_device_type   {measurement_device_type}\n"
            elif instrument and "_diffrn_measurement_method" in line:
                line = f"_diffrn_measurement_method   {measurement_method}\n"
            elif instrument and "_diffrn_radiation_monochromator" in line:
                line = f"_diffrn_radiation_monochromator   {radiation_monochromator}\n"
            elif instrument and "_diffrn_radiation_type" in line:
                line = f"_diffrn_radiation_type   {radiation_type}\n"
            elif instrument and "_diffrn_radiation_wavelength" in line:
                line = f"_diffrn_radiation_wavelength   {radiation_wavelength}\n"
            elif instrument and "_diffrn_source" == line.split()[0]:
                line = f"_diffrn_source   {source}\n"
            elif instrument and "_reflns_special_details" in line:
                line = f"_diffrn_detector   {detector}\n"
                new_lines.append(line)
                line = f"_diffrn_detector_type   {detector_type}\n"
                new_lines.append(line)
                line = f"_diffrn_measurement_device   {measurement_device}\n"
                new_lines.append(line)
                line = f"_diffrn_radiation_probe   {radiation_probe}\n"
                new_lines.append(line)
                line = f"_diffrn_source_type   {source_type}\n"
                new_lines.append(line)
                line = f"_diffrn_source_target   {source_target}\n"
                new_lines.append(line)
                new_lines.append("\n")
                new_lines.append("_reflns_special_details\n")
                continue
        except IndexError:
            pass

        if remove_hkl and "_shelx_hkl_file" in line:
            break

        new_lines.append(line)
        
    # start to answer the common problems in electron diffraction
    if reply:
        new_lines.append("# start Validation Reply Form\n")

        if Rint > 0.12 and Rint <= 0.18:
            answer = f"_vrf_RINTA01_{file_name}\n;PROBLEM: The value of Rint is greater than 0.12\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n"
        elif Rint > 0.18 and Rint <= 0.25:
            answer = f"_vrf_RINTA01_{file_name}\n;PROBLEM: The value of Rint is greater than 0.18\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n"
        elif Rint > 0.25:
            answer = f"_vrf_RINTA01_{file_name}\n;PROBLEM: The value of Rint is greater than 0.25\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n"
        new_lines.append(answer)

        if Rint > 0.12:
            answer = f"_vrf_PLAT020_{file_name}\n;PROBLEM: The Value of Rint is Greater Than 0.12 .........      {Rint:.3f} Report\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n" 
            new_lines.append(answer)

        if R1 > 0.1:
            answer = f"_vrf_PLAT082_{file_name}\n;PROBLEM: High R1 Value ..................................       {R1:.2f} Report\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n" 
            new_lines.append(answer)

        if wR2 > 0.25:
            answer = f"_vrf_PLAT084_{file_name}\n;PROBLEM: High wR2 Value (i.e. > 0.25) ...................       {wR2:.2f} Report\nRESPONSE: Relatively higher R-values are common for electron diffraction due \nto multiple scattering.\n;\n" 
            new_lines.append(answer)

        if aniso == False:
            answer = f"_vrf_ATOM007_{file_name}\n;PROBLEM: _atom_site_aniso_label is missing\nRESPONSE: The structure is only refined isotropically.\n;\n" 
            new_lines.append(answer)

        if completeness < 0.9:
            answer = f"_vrf_PLAT029_{file_name}\n;PROBLEM: _diffrn_measured_fraction_theta_full value Low .      {completeness:.3f} Why?\nRESPONSE: The tilting range of the TEM sample holder is limited.\n;\n" 
            new_lines.append(answer)

        if reply == "porous":
            answer = f"_vrf_PLAT602_{file_name}\n;PROBLEM: VERY LARGE Solvent Accessible VOID(S) in Structure        ! Info \nRESPONSE: Many of the guest species in the pores are disordered and were \nnot included in the structure model.\n;\n" 
            new_lines.append(answer)

        if shift > 0.2:
            answer = f"_vrf_SHFSU01_{file_name}\n;PROBLEM: The absolute value of parameter shift to su ratio > 0.20\nRESPONSE: The shift is originated from unreasonable ADP values.\n;\n" 
            new_lines.append(answer)
            answer = f"_vrf_PLAT080_{file_name}\n;PROBLEM: Maximum Shift/Error ............................       {shift:.2f} Why ? \nRESPONSE: The shift is originated from unreasonable ADP values.\n;\n" 
            new_lines.append(answer)

        new_lines.append("# end Validation Reply Form\n")

    open(fn, "w").writelines(new_lines)

def add_instrument():
    pass

def delete_instrument():
    pass

def list_instrument():
    pass

def main():
    import argparse

    description = "Program to update necessary information in all CIF files."
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument("args", type=str, nargs="*", metavar="FILE",
                        help="List of CIF files or list of directories. If a list of directories is given "
                        "the program will find all CIF files in the subdirectories. If no arguments are given "
                        "the current directory is used as a starting point.")

    parser.add_argument("-m", "--match",
                        action="store", type=str, dest="match",
                        help="Include the XDS.INP files only if they are in the given directories (i.e. --match SMV_reprocessed)")

    parser.add_argument("-u", "--update",
                        action="store_true", dest="update",
                        help="Update cif files")

    parser.add_argument("-w", "--wavelength",
                        action="store", type=float, dest="wavelength",
                        help="Update theta values according to the target wavelength")

    parser.add_argument("-d", "--description",
                        action="store", type=str, dest="description",
                        help="Update description of the crystal")

    parser.add_argument("-c", "--color",
                        action="store", type=str, dest="color",
                        help="Update the color of crystal")

    parser.add_argument("-r", "--remove_hkl",
                        action="store_true", dest="remove_hkl",
                        help="Remove hkl in a cif")

    parser.add_argument("-combi", "--combine",
                        action="store_true", dest="combine",
                        help="Combine all cif files into one file")

    parser.add_argument("-reply", "--reply_validation",
                        action="store", type=str, dest="reply",
                        help="Add checkcif validation reply form")

    parser.add_argument("-i", "--instrument",
                        action="store", type=str, dest="instrument",
                        help="Update instrument related information using a predefined file")

    parser.add_argument("-a", "--add_instrument",
                        action="store_true", dest="add_instrument",
                        help="Add a predefined instrument file")

    parser.add_argument("-del", "--delete_instrument",
                        action="store_true", dest="delete_instrument",
                        help="Delete a predefined instrument file")

    parser.add_argument("-l", "--list_instrument",
                        action="store_true", dest="list_instrument",
                        help="List predefined instrument files")

    parser.add_argument("-revert", "--revert",
                        action="store_true", dest="revert",
                        help="Revert all the cif files back to the version before update ")

    parser.set_defaults(match=None,
                        wavelength=None,
                        description=None,
                        color=None,
                        remove_hkl=None,
                        update=None,
                        combine=None,
                        instrument=None,
                        add_instrument=None,
                        delete_instrument=None,
                        list_instrument=None,
                        revert=None)
    
    options = parser.parse_args()
    fns = options.args
    match = options.match
    wavelength = options.wavelength
    description = options.description
    color = options.color
    remove_hkl = options.remove_hkl
    update = options.update
    combine = options.combine
    reply = options.reply
    instrument = options.instrument
    add_instrument = options.add_instrument
    delete_instrument = options.delete_instrument
    list_instrument = options.list_instrument
    revert = options.revert

    fns = parse_args_for_fns(fns, name="*.cif", match=match)

    if update:
        for fn in fns:
            print("\033[K", fn, end='\r')  # "\033[K" clears line
            update_cif(fn, 
                       wavelength=wavelength,
                       description=description,
                       color=color,
                       remove_hkl=remove_hkl,
                       reply=reply,
                       instrument=instrument)
        print(f"\033[KUpdated {len(fns)} files")

    if combine:
        with open("combine.cif", "wb") as outfile:
            for f in fns:
                with open(f, "rb") as infile:
                    outfile.write(infile.read())

    if add_instrument:
        pass

    if delete_instrument:
        pass

    if list_instrument:
        pass

    if revert:
        for fn in fns:
            if fn.stem.startswith('~'):
                target_name = fn.name[1:]
                if Path(target_name).is_file():
                    Path(target_name).unlink()
                fn.rename(target_name)


if __name__ == '__main__':
    main()
