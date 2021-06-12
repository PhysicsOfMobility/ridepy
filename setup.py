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
        # extra_compile_args=["-std=c++17 -Wl,-rpath,/usr/local/lib /usr/local/lib/libortools.so.9.0.9050 -ldl /usr/local/lib/libabsl_flags_parse.a /usr/local/lib/libabsl_flags_usage.a /usr/local/lib/libabsl_flags_usage_internal.a /usr/local/lib/libabsl_flags.a /usr/local/lib/libabsl_flags_internal.a /usr/local/lib/libabsl_flags_marshalling.a /usr/local/lib/libabsl_flags_reflection.a /usr/local/lib/libabsl_flags_config.a /usr/local/lib/libabsl_flags_private_handle_accessor.a /usr/local/lib/libabsl_flags_commandlineflag.a /usr/local/lib/libabsl_flags_commandlineflag_internal.a /usr/local/lib/libabsl_flags_program_name.a /usr/local/lib/libabsl_random_distributions.a /usr/local/lib/libabsl_random_seed_sequences.a /usr/local/lib/libabsl_random_internal_pool_urbg.a /usr/local/lib/libabsl_random_internal_randen.a /usr/local/lib/libabsl_random_internal_randen_hwaes.a /usr/local/lib/libabsl_random_internal_randen_hwaes_impl.a /usr/local/lib/libabsl_random_internal_randen_slow.a /usr/local/lib/libabsl_random_internal_platform.a /usr/local/lib/libabsl_random_internal_seed_material.a /usr/local/lib/libabsl_random_seed_gen_exception.a /usr/local/lib/libabsl_raw_hash_set.a /usr/local/lib/libabsl_hashtablez_sampler.a /usr/local/lib/libabsl_exponential_biased.a /usr/local/lib/libabsl_hash.a /usr/local/lib/libabsl_city.a /usr/local/lib/libabsl_wyhash.a /usr/local/lib/libabsl_leak_check.a /usr/local/lib/libabsl_statusor.a /usr/local/lib/libabsl_status.a /usr/local/lib/libabsl_cord.a /usr/local/lib/libabsl_bad_optional_access.a /usr/local/lib/libabsl_bad_variant_access.a /usr/local/lib/libabsl_str_format_internal.a /usr/local/lib/libabsl_synchronization.a /usr/local/lib/libabsl_stacktrace.a /usr/local/lib/libabsl_symbolize.a /usr/local/lib/libabsl_debugging_internal.a /usr/local/lib/libabsl_demangle_internal.a /usr/local/lib/libabsl_graphcycles_internal.a /usr/local/lib/libabsl_malloc_internal.a /usr/local/lib/libabsl_time.a /usr/local/lib/libabsl_strings.a /usr/local/lib/libabsl_strings_internal.a /usr/local/lib/libabsl_base.a /usr/local/lib/libabsl_spinlock_wait.a -lrt /usr/local/lib/libabsl_throw_delegate.a /usr/local/lib/libabsl_int128.a /usr/local/lib/libabsl_civil_time.a /usr/local/lib/libabsl_time_zone.a /usr/local/lib/libabsl_bad_any_cast_impl.a /usr/local/lib/libabsl_raw_logging_internal.a /usr/local/lib/libabsl_log_severity.a /usr/local/lib/libprotobuf.a /usr/local/lib/libCbcSolver.a /usr/local/lib/libOsiCbc.a /usr/local/lib/libCbc.a /usr/local/lib/libCgl.a /usr/local/lib/libClpSolver.a /usr/local/lib/libOsiClp.a /usr/local/lib/libClp.a /usr/local/lib/libOsi.a /usr/local/lib/libCoinUtils.a /usr/local/lib/libscip.a /usr/lib/x86_64-linux-gnu/libz.so -lpthread"],
        extra_compile_args=[
            "-std=c++17",
            "-Wl,-rpath,/usr/local/lib",
            "-fPIC",
            "-O4",
            "-DARCH_K8",
            "-Wno-deprecated",
            "-DUSE_BOP",
            "-DUSE_GLOP",
            "-DUSE_CBC",
            "-DUSE_CLP",
            "-DUSE_SCIP",
        ],
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
)
