#!/usr/bin/env python
import os
import setuptools
from Cython.Build import cythonize
from setuptools import Extension


with open("requirements.txt", "r") as f:
    reqs = f.readlines()

with open("requirements-dev.txt", "r") as f:
    dev_reqs = f.readlines()


extensions = [
    Extension(
        "*",
        ["thesimulator/**/*.pyx"],
        extra_compile_args=["-std=c++17"],
    ),
]

setuptools.setup(
    name="thesimulator",
    version="0.1",
    zip_safe=False,
    packages=setuptools.find_packages(),
    # ext_modules=cythonize("thesimulator/**/*.pyx", language='c++',),
    ext_modules=cythonize(extensions, compiler_directives={"embedsignature": True}),
    install_requires=reqs,
    extras_require={"dev": dev_reqs},
    options={"build_ext": {"inplace": True, "parallel": os.cpu_count()}},
)
