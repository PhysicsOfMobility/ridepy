.. _using_cython:

Overview of the cythonic components
===================================
As we described in the :doc:`conceptual overview <overview>`, RidePy enables the users to run a simulation using either pure pythonic components, or using cythonic components. Using a :ref:`dispatcher <desc_dispatcher>` implemented in C++ and exposed to Python using Cython can dramatically speed up the simulation runs.

In order to make it happen, RidePy contains C++ implementations of all
its core components, i.e.

* `data_structures`
* `spaces`
* and `dispatchers`,

as well as Cython wrappers thereof.

The module structure of the cythonic components mimics exactly that of their pythonic
counterparts, so that in most cases, a user wishing to switch to cythonic components can
simply change their ``import`` statements from

.. code-block:: python

    from ridepy.data_structures import Stop

to

.. code-block:: python

    from ridepy.data_structures_cython import Stop

A concrete example of how to transition from a pure python simulation to a
cythonic simulation is provided in :doc:`tutorial 2 <notebooks/introduction_cython>`.
