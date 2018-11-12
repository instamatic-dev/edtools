from setuptools import setup

setup(
    name="scedtools",
    version="0.1.0",
    description="Collection of tools for automated processing and clustering of single-crystal electron diffraction data",

    author="Stef Smeets",
    author_email="stef.smeets@mmk.su.se",
    url="https://github.com/stefsmeets/scedtools",

    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],

    install_requires=["numpy", "matplotlib", "scipy", "pandas"],

    package_data={
        "": ["setup.py"],
    },

    entry_points={
        'console_scripts': [
            "scedtools.autoindex        = autoindex:main",
            "scedtools.cluster          = cluster:main",
            "scedtools.find_cell        = find_cell:main",
            "scedtools.extract_xds_info = extract_xds_info:main",
            "scedtools.run_pointless    = run_pointless:main",
            "scedtools.make_xscale      = make_xscale:main",
            "scedtools.make_shelx       = make_shelx:main",
            "scedtools.update_xds       = update_xds:main",
        ]
    }
)

