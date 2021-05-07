Cython Data Structures
~~~~~~~~~~~~~~~~~~~~~~
This cython module wraps the struct templates exposed from C++ by
`data_structures_cython.pxd` into extension types.  Since an extension type
obviously cannot be templated, we will use the :ref:`desc_runtime_dispatch` approach.

.. py:class:: ridepy.data_structures_cython.LocType

    Representing the kind of location objects the simulator supports. either of:

    1. `R2LOC` (for points in :math:`\mathbb{R}^2`, holds a `tuple[float, float]`).
    2. `INT` (for e.g. graphs).

    .. note::
       Use this for simulations using the cythonic components. For simulations using pure pythonic components,
       the python version of this enum i.e. `.data_structures.LocType` has to be used.


.. automodule:: ridepy.data_structures_cython
    :members: TransportationRequest, InternalRequest, Stop, Stoplist
    :special-members: __len__, __getitem__



