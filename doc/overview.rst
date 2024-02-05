Overview
========

.. highlight:: python

RidePy is a Python library that performs mobility simulations; in particular, it is able to simulate on-demand transit services such as ride hailing (taxicab-like operations) and ridepooling (trips of similar origin, destination, and time are served by the same vehicle). RidePy provides an interface that allows researchers to replicate the operation of such transport systems and thus study their properties and behavior without actually transporting passengers in the real world.

Getting started with RidePy is easy: The user just has to choose a way of generating the virtual customers' requests for transportation and set up a transportation service by specifying its characteristics (e.g., number of vehicles, dispatching algorithm, additional constraints). RidePy will simulate the operation of the service and log all events, e.g., the pick-up of a customer or the submission of a new request. After the simulation has finished, RidePy can additionally provide structured information about the details of the simulation run. These data can then be analyzed further by the user to gain insights into the behavior of the simulated service.

In this chapter, we describe the design of RidePy, and how to get started using it to run simulations. We also describe how to specify new dispatching algorithms and new transport spaces.


The setting
-----------

Rather than explicitly modeling the behavior of individuals (classic agent-based simulations), RidePy instead starts with a set of *transportation requests* (denoting the desire of an individual to be transported from A to B within a specified time window), and a *dispatcher* (an algorithm that determines which vehicle should service which requests and in which order). Then it simply simulates these requests arriving in the system, being picked up, and being delivered. Requests that cannot be delivered within the specified time windows are *rejected*.

RidePy makes it easy to experiment with different dispatching algorithms, spatio-temporal request densities, fleet sizes and transport spaces (2D plane, different graphs). It comes with an `analytics` package that from the simulation computes various output metrics like e.g. the statistical distributions of occupancies, waiting times, and detours.

Since the ability to simulate many *requests* and many *vehicles* is important for any quantitative study RidePy uses `Cython <https://cython.readthedocs.io/en/latest/>`_ to achieve very fast simulations. We provide, out of the box, the ability to choose either pure pythonic or cythonic data structures and algorithms for running the simulations. This way, dispatchers can be defined in the C++ language. See the :ref:`cython overview <using_cython>` for more detail.

In addition, the `FleetState` may be parallelized, using e.g. OpenMPI. Currently, another way of running parallelized simulations is implemented by means of multiprocessing. This allows for simultaneous execution of simulations at different parameters (`SimulationSet` from the `extras` package).
