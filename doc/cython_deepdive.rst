Cython wrapping internals
=========================
Here we will detail the design decisions we made while implementing the core
components of `theSimulator` in cython. Our goals were

* The calling code would require minimal changes while switching from pure python
  components  to their cython equivalents.
* The core C++ implementation should be as lightweight as possible.
* Reducing the runtime of the typical simulation runs is the foremost efficiency criterion.

As a result of these goals, our cython wrapping code unfortunately is not so
lightweight and contains quite some boilerplate code. Here we will explain
why and explain how to extend these components.

Handling different types of location objects
--------------------------------------------
The pure pythonic parts of `theSimulator` can handle simulation runs in any
`.TransportSpace`, e.g. `Euclidean2D`, where location objects are `Tuple[float,
float]` or a `.Graph` where the nodes are arbitrary python objects. It is not
so easy to expose similar functionalities in a cython-wrapped python module.

C++ allows one to write data structures and algorithms using templates, so
there's no need to duplicate the same code to handle two different kind of
location object. Cython can wrap `templated C++ data structures
<https://cython.readthedocs.io/en/latest/src/userguide/wrapping_CPlusPlus.html#templates>`_
just fine, but such a templated data structure/function cannot be exposed
to the python side directly. An extension type cannot be templated (at compile time, 
all possible variations of a template must be known). There is no really elegant way 
of doing it in cython as of `v3.0a6`. So we will use the `Explicit Run-Time Dispatch approach
<https://martinralbrecht.wordpress.com/2017/07/23/adventures-in-cython-templating>`_.

.. _desc_runtime_dispatch:

The Explicit Runtime Dispatch approach
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In short, the enum `.data_structures_cython.LocType` contains all
template types `Loc` we are likely to need.  The extension type for e.g. the C++
struct `data_structures_cython.cdata_structures.pyx::Request[Loc]`
then will contain **a union** holding one of the variants (e.g. `Request[int]`,
`Request[tuple(double, double)]`) etc. Then each member function will check the
`LocType`, and dispatch the method call to the appropriate object inside that
union.



Instantiating Extension dtypes from existing C++ objects
--------------------------------------------------------
