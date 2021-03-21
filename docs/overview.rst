Overview
========

.. currentmodule:: thesimulator

Here we describe the design of theSimulator, and how to get started with using
it to run simulations. We also describe how to specify new dispatching
algorithms and new transport spaces.



The setting
-----------
theSimulator does *not* do agent-based simulations. Rather, it starts with a set
of *transportation requests* (denoting the desire of an individual to be
transported from A to B within specified time windows), and a *dispatcher* (an
an algorithm that determines which vehicle should service which requests and in which
order). Then it simply simulates these requests arriving in the system, being
picked up and delivered. Requests that cannot be delivered within the specified
time windows are *rejected*. theSimulator makes it easy to experiment with
different dispatching algorithms, spatiotemporal request densities, fleet sizes
and transport spaces (2-D plane, different graphs). It comes with an `analytics`
module that computes from the simulation output various metrics like the
statistical distributions of occupancies, waiting times and detours.

Since the ability to simulate to simulate many *requests* and many *vehicles*
are important for any quantitative study, we include two powerful ways of
speeding up the simulation:

a. Using parallelism. The dispatcher interface prescribes computing a *cost* for
serving a request with a certain vehicle. Then the vehicle with the minimum cost
is chosen. Since this is an "embarassingly paralizable" operation, theSimulator
provides two parallel ways of computing it, out of the box:

  - `multiprocessing`.
  - `openMPI`.

b. Using `cython <https://cython.readthedocs.io/en/latest/>`. We provide, out of
the box, the ability to choose either pure pythonic or cythonic data structures
and algorithms for running the simulations. See :doc:`/developers/cython` for
details.


Quickstart
----------
An usual way of using theSimulator is as follows:

* Generate a sequence of :class:`TransportationRequest
  <data_structures.TransportationRequest>` s, optionally using the
  :mod:`request_generators <util.request_generators>` module. Each
  ``TransportationRequest`` consists of:

  - ``origin``,
  - ``destination``,
  - ``pickup_timewindow_min``,
  - ``pickup_timewindow_max``,
  - ``delivery_timewindow_min``,
  - ``delivery_timewindow_max``.

  The ``origin`` and ``destination`` must belong to the same :class:`TransportSpace
  <data_structures.TransportSpace>` (e.g. ``Euclidean2D``) where the simulation
  will be run.
* Choose a ``dispatcher`` that matches a request to a vehicle. A few
  dispatchers are provided in the :mod:`dispatchers <util.dispatchers>`
  module, and the user is welcome to implement their own.
* Create a :class:`FleetState <fleet_state.FleetState>` with the desired number
  of vehicles (and the initian positions of the vehicles) and call the
  :meth:`FleetState.simulate <fleet_state.FleetState.simulate>` method.
* The output of the simulation run is an :any:`Iterator
  <python:collections.abc.Iterator>` of ``Event``'s, describing when which
  ``TransportationRequest`` was picked up and delivered.
..
    TODO Cross referencing modules with :mod:`bla` is not working!




How to create your own dispatcher
---------------------------------



How to create your own ``TransportSpace``
-----------------------------------------



Using parallelism
-----------------



Use cythonized data structures and algorithms
---------------------------------------------
