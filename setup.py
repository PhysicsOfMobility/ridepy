#!/usr/bin/env python
import os
from Cython.Build import cythonize
from setuptools import Extension, setup

setup(
    ext_modules=cythonize(
        [
            Extension(
                name="*",
                sources=["src/ridepy/**/*.pyx"],
                extra_compile_args=["-std=c++17"],
                include_dirs=[
                    "src/lru-cache/include",
                    "src/ridepy/util/spaces_cython",
                    "src/ridepy/util/dispatchers_cython",
                    "src/ridepy/data_structures_cython",
                ],
            ),
        ],
        compiler_directives={"embedsignature": True},
    ),
    options={
        "build_ext": {
            "inplace": True,
            "parallel": os.cpu_count() - 1,
        }
    },
)
