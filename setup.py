from setuptools import setup

setup(
    name="edtools",
    version="0.1.0",
    description="Collection of tools for automated processing and clustering of single-crystal electron diffraction data",

    author="Stef Smeets",
    author_email="stef.smeets@mmk.su.se",
    url="https://github.com/stefsmeets/edtools",

    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],

    install_requires=["numpy", "matplotlib", "scipy", "pandas"],

    extras_require = {
        'uncertainties':  ["uncertainties"]
    },

    package_data={
        "": ["setup.py"],
    },

    entry_points={
        'console_scripts': [
            "edtools.autoindex        = edtools.autoindex:main",
            "edtools.cluster          = edtools.cluster:main",
            "edtools.find_cell        = edtools.find_cell:main",
            "edtools.extract_xds_info = edtools.extract_xds_info:main",
            "edtools.run_pointless    = edtools.run_pointless:main",
            "edtools.make_xscale      = edtools.make_xscale:main",
            "edtools.make_shelx       = edtools.make_shelx:main",
            "edtools.update_xds       = edtools.update_xds:main",
        ]
    }
)

