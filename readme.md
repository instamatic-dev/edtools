[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/instamatic-dev/edtools/build)](https://github.com/instamatic-dev/edtools/actions)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edtools)](https://pypi.org/project/edtools/)
[![PyPI](https://img.shields.io/pypi/v/edtools.svg?style=flat)](https://pypi.org/project/edtools/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/edtools)](https://pypi.org/project/edtools/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5727188.svg)](https://doi.org/10.5281/zenodo.5727188)

# edtools

Collection of tools for automated processing and clustering of batch 3-dimensional electron diffraction (3D ED) datasets.

[The source for this project is available here][src].

[src]: https://github.com/instamatic-dev/edtools

## Installation

Install using `pip install edtools`. Installation should take less than 20 seconds on a normal desktop.

Find the latest [releases](https://github.com/instamatic-dev/edtools/releases) for the versions that have been tested on.

## OS Requirement

Windows 10 or newer.

## Software Requirements

- Python 3.6+ including `numpy`, `scipy`, `matplotlib`, and `pandas` libraries
- [`sginfo`](https://github.com/rwgk/sginfo) or [`cctbx.python`](https://cctbx.github.io/installation.html#installation) must be available on the system path for `edtools.make_shelx`
- Access to [WSL](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux)
- XDS package must be installed properly under WSL

## Package dependencies

Check [pyproject.toml](pyproject.toml) for the full dependency list and versions.

## Documentation

See the documentation at https://edtools.readthedocs.io.

## Pipeline tools

At any step, run *edtools.xxx -h* for help with possible arguments.

### autoindex.py

Looks for files matching `XDS.INP` in all subdirectories and runs them using `XDS`.

	In:  XDS.INP
	Out: XDS data processing on all files

Usage:

```
edtools.autoindex
```

### extract_xds_info.py

Looks files matching `CORRECT.LP` in all subdirectories and extracts unit cell/integration info. Summarizes the unit cells in the excel file `cells.xlsx` and `cells.yaml`. XDS_ASCII.HKL files matching the completeness / CC(1/2) criteria are listed in `filelist.txt`. Optionally, gathers the corresponding `XDS_ASCII.HKL` files in the local directory. The `cells.yaml` file can be used as input for further processing.

	In:  CORRECT.LP
	Out: cells.yaml
	     cells.xlsx
	     filelist.txt

Usage:

```
edtools.extract_xds_info
```

### find_cell.py

This program a cells.yaml file and shows histogram plots with the unit cell parameters. This program mimicks [`CELLPARM`](http://xds.mpimf-heidelberg.mpg.de/html_doc/cellparm_program.html) and calculates the weighted mean lattice parameters, where the weight is typically the number of observed reflections (defaults to 1.0). For each lattice parameter, the mean is calculated in a given range (default range = median+-2). The range can be changed by dragging the cursor on the histogram plots.

Alternatively, the unit cells can be clustered by giving the `--cluster` command, in which a dendrogram is shown. The cluster cutoff can be selected by clicking in the dendrogram. The clusters will be written to `cells_cluster_#.yaml`.

	In:  cells.yaml
	Out: mean cell parameters
	     cells_*.yaml (clustering only)

Usage:

```
edtools.find_cell cells.yaml --cluster
```

### make_xscale.py

Prepares an input file `XSCALE.INP` for `XSCALE` and corresponding `XDSCONV.INP` for `XDSCONV`. Takes a `cells.yaml` file or a series of `XDS_ASCII.HKL` files as input, and uses those to generate the `XSCALE.INP` file.

	In:  cells.yaml / XDS_ASCII.HKL
	Out: XSCALE.INP

Usage:

```
edtools.make_xscale cells.yaml -c 10.0 20.0 30.0 90.0 90.0 90.0 -s Cmmm
```

### cluster.py

Parses the `XSCALE.LP` file for the correlation coefficients between reflection files to perform hierarchical cluster analysis (Giordano et al., Acta Cryst. (2012). D68, 649–658). The cutoff threshold can be selected by clicking in the dendrogram window. The program will write new `XSCALE.LP` files to subdirectories `cluster_#`, and run `XSCALE` on them, and (if available), pointless.

	In:  XSCALE.LP
	Out: cluster_n/
		filelist.txt
		*_XDS_ASCII.HKL
		XSCALE processing
		Pointless processing
		shelx.hkl
		shelx.ins (optional)

Usage:

```
edtools.cluster
```


## Helper tools

### make_shelx.py

Creates a shelx input file. Requires `sginfo` to be available on the system path to generate the SYMM/LATT cards.

	In:  cell, space group, composition
	Out: shelx.ins

Usage:

```
edtools.make_shelx -c 10.0 20.0 30.0 90.0 90.0 90.0 -s Cmmm -m Si180 O360
```

### run_pointless.py

Looks for XDS_ASCII.HKL files specified in the cells.yaml, or on the command line and runs Pointless on them.

	In:  cells.yaml / XDS_ASCII.HKL
	Out: Pointless processing

### update_xds.py

Looks files matching `CORRECT.LP` in all subdirectories, and updates the cell parameters / space group as specified.

	In:  XDS.INP
	Out: XDS.INP

Usage:

```
edtools.update_xds -c 10.0 20.0 30.0 90.0 90.0 90.0 -s Cmmm
```

### find_rotation_axis.py

Finds the rotation axis and prints out the inputs for several programs (XDS, PETS, DIALS, Instamatic, and RED). Implements the algorithm from Gorelik et al. (Introduction to ADT/ADT3D. In Uniting Electron Crystallography and Powder Diffraction (2012), 337-347). The program reads `XDS.INP` to get information about the wavelength, pixelsize, oscillation angle, and beam center, and `SPOT.XDS` (generated by COLSPOT) for the peak positions. If the `XDS.INP` file is not specified, the program will try to look for it in the current directory.

	In:  XDS.INP, SPOT.XDS
	Out: Rotation axis

Usage:

```
edtools.find_rotation_axis [XDS.INP]
```

## Demo of using edtools to process batch 3D electron diffraction datasets

See the demo at https://edtools.readthedocs.io/en/latest/examples/edtools_demo.html.
