#!/usr/bin/env python
import os

from collections import defaultdict
from Cython.Build import cythonize
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext

BUILD_ARGS = defaultdict(lambda: ["-std=c++17", "-O3"], msvc=["/std:c++17"])


class build_ext_w_compiler_check(build_ext):
    # Adapted from <https://stackoverflow.com/questions/30985862/how-to-identify- \
    #   compiler-before-defining-cython-extensions/32192172#32192172>
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        args = BUILD_ARGS[compiler]
        for ext in self.extensions:
            ext.extra_compile_args = args
        build_ext.build_extensions(self)


setup(
    package_dir={"": "src"},  # Necessary for `python setup.py develop` to work
    ext_modules=cythonize(
        [
            Extension(
                name="*",
                sources=["src/ridepy/**/*.pyx"],
                include_dirs=[
                    "src/lru-cache/include",
                    "src/ridepy/util/spaces_cython",
                    "src/ridepy/util/dispatchers_cython",
                    "src/ridepy/data_structures_cython",
                ],
            )
        ],
        compiler_directives={"embedsignature": True},
        language_level=3,
    ),
    options={
        "build_ext": {
            "inplace": True,
            "parallel": os.cpu_count() - 1,
        }
    },
    cmdclass={"build_ext": build_ext_w_compiler_check},
)
