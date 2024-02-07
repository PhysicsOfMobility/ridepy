Conceptual overview
===================

.. highlight:: python

RidePy is a scientific Python library that simulates transit systems, in particular services such as ride hailing (taxicab-like operations) and ridepooling (trips of similar origin, destination, and time served by the same vehicle, i.e. "pooled"). RidePy provides an interface that allows researchers to replicate the operation of such transport systems and thus study their properties and behavior without ever actually transporting passengers in the real world. This may prove helpful both in theoretical research (sociophysics and econophyics, complexity research) and in estimating operational properties of on-demand transit in realistic scenarios as part of transportation science and transportation engineering.

Basic usage
-----------

Getting started with RidePy is straightforward: The user has to choose a way of generating the virtual customers' requests for transportation and set up a transportation service by specifying its characteristics (e.g., number of vehicles, dispatching algorithm, additional constraints). RidePy will simulate the operation of the service and log all events, e.g., the pick-up of a customer, or the submission of a new request. After the simulation has finished, RidePy can additionally provide structured information about the details of the simulation run (e.g., customer travel times, schedules of the vehicles, ...). These data can then be analyzed further by the user to gain insights into the behavior of the simulated service.

Design choices
--------------

Rather than explicitly modeling the detailed behavior of individuals (classic agent-based simulations), RidePy instead operates on a given set of *transportation requests* (denoting the desire of an individual to be transported from A to B), and a *dispatcher* (an algorithm that determines which vehicle should service which requests and in which order). Managing a fleet (by a `FleetState`) of virtual vehicles (each represented by a `VehicleState`), it simulates these requests entering the system (*submission*), being *picked up*, and being *delivered*, thus leaving the system. Requests that cannot be served without violating constraints such as time windows are *rejected* upon submission and leave the system immediately.

Due to its modular design centered around managing a fleet of vehicles, RidePy makes it quite easy to experiment with different dispatching algorithms, spatio-temporal request densities, fleet sizes and transport spaces (2D plane, graphs). In addition it features an `analytics` package that extracts various metrics like the distributions of vehicle occupancies, waiting times, and detours, and more.

Since the ability to simulate many *requests* and many *vehicles* is important for any quantitative study, RidePy integrates `Cython <https://cython.readthedocs.io/en/latest/>`_ and C++ components to speed up simulations. We provide the ability to choose either pure "pythonic", or "cythonic" data structures and algorithms for running the simulations. This makes development and testing in Python easy even for novice users, while performance-critical parts may be reimplemented in Cython or C++ at a later stage, should the need for larger-scale simulations arise. For more details about Cython, see the :ref:`Cython overview <using_cython>`.

To achieve even higher performance, the central entity controlling the fleet, the `FleetState`, may be parallelized to simultaneously execute the dispatching algorithm on multiple vehicles, using e.g. OpenMPI. Currently, another way of parallelizing operations is implemented using multiprocessing. This feature makes it possible to easily run multiple independent simulations at different parameters simultaneously (`SimulationSet` from the `extras` package).
