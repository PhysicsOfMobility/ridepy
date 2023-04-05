|Code style: black| |Tests| |Docs| |wheel| |sdist|

RidePy
======

Simulates a dispatching algorithm serving exogenous transportation
requests with a fleet of vehicles. Does not simulate the universe,
unlike MATSim. Batteries are included.

The documentation is available at `ridepy.org <https://ridepy.org/>`__,
the source code is hosted on `GitHub <https://github.com/PhysicsOfMobility/ridepy>`__.

Instructions
------------

Prerequisites
~~~~~~~~~~~~~

-  Python 3.9
-  git

You should probably use an environment. For example, using
`conda <https://www.anaconda.com/>`__:

.. code:: sh

    conda create -n ridepy python=3.9
    conda activate ridepy


Finally, a C++ build environment and the `Boost C++ Libraries <https://www.boost.org/>`__ are necessary.
On Debian-based Linux distributions, these may be installed as follows:

.. code:: sh

    sudo apt-get update && sudo apt-get -y install libboost-all-dev build-essential

User Installation
~~~~~~~~~~~~~~~~~

Just run

.. code:: sh

    pip install ridepy

If you prefer, you can also use clone the git repository instead:

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy
    pip install -e .


Developer Installation
~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy
    pip install -e ".[dev,doc]"
    make -C doc html
    pre-commit install
    pytest

The built documentation can be found in ``doc/_build/html/index.html``.


First Steps
-----------

-  Start ``jupyter notebook`` or ``jupyter lab``
-  Open one of the introductory notebooks in the ``notebooks``
   subdirectory, either just by clicking on it (in ``jupyter notebook``) or
   right-clicking and choosing *Open With > Notebook* (for ``jupyter lab``).
-  Run the notebook step-by-step and play around :)

Contributing
------------

Generally, branch off from ``master``, implement stuff® and file a pull
request back to ``master``. Feel free to do the latter at an early
stage using the GitHub's "Submit Draft" feature.

Versioning Philosophy:

-  ``master`` should always improve. Incomplete functionality is welcome.
-  API-breaking changes imply transition to a new major version

Code style is *black* for Python and *LLVM* for C++. To format your code use

- ``black .`` for Python. Make sure to use the correct version as specified in ``requirements-dev.txt``.
- ``find . -regex '.*\.\(cxx\|h\)' -exec clang-format -style=file -i {} \;`` for C++

Testing
~~~~~~~

-  For each new feature introduced, tests should be written, using the
   `pytest <https://docs.pytest.org/en/stable/>`__ framework
-  Running tests is easy---just execute ``pytest`` in the project
   directory
-  Additional pointers for running pytest:

   -  Drop into a debugger on failing test using ``pytest --pdb``
   -  Show stdout with ``pytest -s``
   -  Run only specific tests by matching the test function name
      ``pytest -k <match expression>``
   -  Be more verbose with ``pytest -v``

-  Warning 1: Pytest may cause confusion as it automagically imports
   stuff and supplies functions with things they need based on their
   signature. For this, see e.g. the docs on
   `fixtures <https://docs.pytest.org/en/stable/fixture.html>`__.
-  Warning 2: Warning 1 applies in particular to stuff hiding in
   innocent-looking files named ``conftest.py``. See docs on
   `conftest <https://docs.pytest.org/en/2.7.3/plugins.html>`__.

Principles
----------

Jargon
~~~~~~

-  **estimated arrival time**, also Cached Predicted Arrival Time CPAT
-  **time window min**, also Earliest Allowed Service Time EAST
-  **time window max**, also Latest Allowed Service Time LAST
-  **stoplist**, a sequence of scheduled stops that a transporter must
   *service*, i.e. perform the action defined in the respective stop's
   ``Stop.action``
-  The dummy stop **current position element CPE** always must be the first
   entry of each stoplist. It is used to denote the current location of the
   transporter.
-  Transporter, the same as vehicle, bus, or car

General Things
~~~~~~~~~~~~~~

-  The **dispatcher** is responsible for keeping the state of the stoplists
   valid. This includes recomputing the estimated arrival times and
   making sure that the order of the stops in the stoplist follows the
   order of the estimated arrival times. It also means managing the
   CPE.


.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |Docs| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/docs-gh-pages.yml/badge.svg
    :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/docs-gh-pages.yml

.. |Tests| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/python-testing.yml/badge.svg
    :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/python-testing.yml

.. |wheel| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-pypi-wheel.yml/badge.svg
    :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-pypi-wheel.yml

.. |sdist| image:: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-pypi-sdist.yml/badge.svg
    :target: https://github.com/PhysicsOfMobility/ridepy/actions/workflows/build-pypi-sdist.yml
