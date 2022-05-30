#!/usr/bin/env python
import os
import setuptools
from Cython.Build import cythonize
from setuptools import Extension

with open("requirements.txt", "r") as f:
    reqs = f.readlines()

with open("requirements-dev.txt", "r") as f:
    dev_reqs = f.readlines()

with open("requirements-doc.txt", "r") as f:
    doc_reqs = f.readlines()


extensions = [
    Extension(
        "*",
        ["ridepy/**/*.pyx"],
        extra_compile_args=["-std=c++17"],
        include_dirs=["ridepy/util/spaces_cython/lru-cache/include"],
    ),
]

setuptools.setup(
    name="ridepy",
    version="0.1",
    python_requires=">=3.9",
    zip_safe=False,
    packages=setuptools.find_packages(),
    # ext_modules=cythonize("ridepy/**/*.pyx", language='c++',),
    ext_modules=cythonize(extensions, compiler_directives={"embedsignature": True}),
    install_requires=reqs,
    extras_require={"dev": dev_reqs, "doc": doc_reqs},
    options={"build_ext": {"inplace": True, "parallel": os.cpu_count() - 1}},
    entry_points={"console_scripts": ["ridepy = ridepy.cli:app"]},
)
