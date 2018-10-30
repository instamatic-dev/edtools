# scedtools
Collection of tools for automated processing and clustering of single-crystal electron diffraction data

### autoindex.py

Looks for files matching `XDS.INP` in all subdirectories and runs them using `XDS`.

### extract_xds_info.py

Looks files matching `CORRECT.LP` in all subdirectories and extracts unit cell/integration info. Summarizes the unit cells in the excel file `cells.xlsx`, and writes input file `CELLPARM.INP` for the program `CELLPARM`. Gathers the corresponding `XDS_ASCII.HKL` files in the local directory, and lists them in `filelist.txt`. The latter can be used as input for further processing (`fitit_permute.py`).

### make_xscale.py

Prepares an input file `XSCALE.INP` for `XSCALE` and corresponding `XDSCONV.INP` for `XDSCONV`. Finds all files matching `*_XDS_ASCII.HKL` in the current directory, or those given as command line arguments. Prompts the user to pick a unit cell, and it will only include the files with matching unit cells. The criterion used is the euclidean distance from the chosen unit cell, with a default threshold of 2.0. Also updates `CELLPARM.INP` with the selected unit cells.

### cluster.py

Parses the `XSCALE.LP` file for the correlation coefficients between reflection files to perform hierarchical cluster analysis (Giordano et al., Acta Cryst. (2012). D68, 649–658). The cutoff threshold can be selected by clicking in the dendrogram window. The program will write new `XSCALE.LP` files to subdirectories `cluster_N`, and run `XSCALE` on them.

### find_cell.py

This program parses `CELLPARM.INP` and shows histogram plots with the unit cell parameters. This program mimicks `CELLPARM` (http://xds.mpimf-heidelberg.mpg.de/html_doc/cellparm_program.html) and calculates the weighted mean lattice parameters, where the weight is typically the number of observed reflections (defaults to 1.0). For each lattice parameter, the mean is calculated in a given range (default range = median+-2). The range can be changed by dragging the cursor on the histogram plots.

### make_shelx.py

Creates a shelx input file. Requires `sginfo` to be available on the system path to generate the SYMM/LATT cards.

Usage:

```
python make_shelx.py -c 10.0 20.0 30.0 90.0 90.0 90.0 -s Cmmm -m Si180 O360
```


## Requirements

- Python3.6 including `numpy`, `scipy`, `matplotlib`, and `pandas` libraries
- Windows 10 with access to [WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux)
- XDS and related tools must be available under WSL
- `sginfo` must be available on the system path
