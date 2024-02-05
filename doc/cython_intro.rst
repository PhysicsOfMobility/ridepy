.. _using_cython:

Overview of the cythonic components
===================================
As we described in :doc:`overview`, ridepy enables the users to run a
simulation using either pure pythonic components, or using cythonic
components. Using a :ref:`dispatcher <desc_dispatcher>` implemented in C++ and
exposed to python using cython can dramatically speed up the simulation runs.

In order to make it happen, ridepy contains C++ implementations of all
its components i.e.

* `data_structures`,
* `spaces`,
* and `dispatchers`,

as well as cython wrappers thereof.

The module structure of the cythonic components mimics exactly that of their pythonic
counterparts, so that in most cases a user wishing to switch to cythonic components can
just change their import statements from

.. code-block:: python

    from ridepy.data_structures import Stop

to

.. code-block:: python

    from ridepy.data_structures_cython import Stop

A concrete example of how to switch from a pure python simulation to a
cythonic simulation is provided in :doc:`overview`.

.. warning::
   Add a list of all user-facing cythonic components for ease of discoverability.
