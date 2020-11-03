#!/usr/bin/env python

from setuptools import Extension, setup, find_packages
from Cython.Build import cythonize

setup(
    name="thesimulator",
    version="0.1",
    zip_safe=False,
    ext_modules=cythonize(Extension(
        name="thesimulator.cvehicle_state",
        sources=[
            "thesimulator/cvehicle_state/cvehicle_state.pyx",
            "thesimulator/cvehicle_state/vstate.cpp"],
        language="c++"),
        language_level=3
    ),

    packages=find_packages(),
    install_requires=[
        "numpy>=1.19.1",
        "mpi4py>=3.0.3",
        "scipy>=1.5.2",
        "wheel>=0.35.1",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.1",
            "black>=19.10b0",
            "ipython>=7.16.1",
            "pdbpp>=0.10.2",
            "pre-commit>=2.7.1",
            "tabulate>=0.8.7",
            "commitizen>=2.4.1",
        ]
    },
)
