|Code style: black| |Tests| |Docs| |wheel| |sdist|

RidePy
======

RidePy is a scientific Python library for simulating modern on-demand transit systems such as ridepooling.

In short: RidePy simulates a dispatching algorithm serving exogenous transportation requests with a fleet of vehicles. Does not simulate the universe, unlike MATSim. Batteries are included.

Head over to `ridepy.org <ridepy doc_>`__ to get started.

Quickstart
----------

For detailed instructions, see the `installation guide <https://ridepy.org/setup.html>`__ in the documentation.

If you're in a hurry, here's the gist:

- RidePy currently works best with Python 3.9
- If you are on platform other than x86-64 Linux, i.e., one that we don't offer wheels for, you will need to first set up a C++ build environment and the `Boost C++ libraries <https://www.boost.org/>`__. On Debian-like systems, this is easily accomplished with

.. code-block:: bash

   sudo apt-get install build-essential libboost-all-dev

- Install RidePy with

.. code-block:: bash

   pip install ridepy

Contributing
------------

We are always happy for contributions from the community. If you run into a problem, please `report an issue <https://ridepy.org/issues.html>`__ or `ask for help <https://ridepy.org/support.html>`__.

If you are interested in contributing to our codebase, please read our `contributing guide <https://ridepy.org/contributing.html>`__.

Here is a short overview of the most important points:

Resources
~~~~~~~~~

- Documentation: `ridepy.org <ridepy doc_>`__
- Source code: `GitHub <https://github.com/PhysicsOfMobility/ridepy>`__
- Issue tracker: `GitHub <https://github.com/PhysicsOfMobility/ridepy/issues>`__

Code style
~~~~~~~~~~

- Python: `black <https://github.com/psf/black>`__
- C++: `LLVM <https://llvm.org/docs/CodingStandards.html>`__

Development
~~~~~~~~~~~

- Version control: `Git <https://git-scm.com/>`__
- Testing: `pytest <https://docs.pytest.org/en/stable/>`__
- Continuous integration: `GitHub Actions <https://github.com/PhysicsOfMobility/ridepy/actions>`__
- Versioning: `Semantic Versioning <https://semver.org/>`__

.. http://mozillascience.github.io/working-open-workshop/contributing/

..
    ---------
    Badges
    ---------

.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

.. |Docs| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-doc.yml/badge.svg
   :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-doc.yml

.. |Tests| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/python-testing.yml/badge.svg
   :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/python-testing.yml

.. |wheel| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-wheel.yml/badge.svg
   :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-wheel.yml

.. |sdist| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-sdist.yml/badge.svg
   :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-sdist.yml

.. _ridepy doc: https://ridepy.org
