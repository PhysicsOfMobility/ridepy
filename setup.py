#!/usr/bin/env python
import setuptools
from Cython.Build import cythonize


with open("requirements.txt", "r") as f:
    reqs = f.readlines()

with open("requirements-dev.txt", "r") as f:
    dev_reqs = f.readlines()

extensions = [
    setuptools.Extension(
        name="thesimulator.cvehicle_state",
        sources=[
           "thesimulator/cvehicle_state/cvehicle_state.pyx",
           "thesimulator/cvehicle_state/cstuff.cpp",
        ],
        language="c++",
    )
]

setuptools.setup(
    name="thesimulator",
    version="0.1",
    zip_safe=False,
    packages=setuptools.find_packages(),
    ext_modules=cythonize(extensions),
    install_requires=reqs,
    extras_require={"dev": dev_reqs}
)
