|Code style: black|

theSimulator
============

Simulates a dispatching algorithm serving exogeneous transportation
requests with a fleet of vehicles. Does not simulate the universe,
unlike MATSIM.

Instructions
------------

Prerequisites
~~~~~~~~~~~~~

-  Python 3.9
-  git

You should probably use an environment. For example, using
`conda <https://www.anaconda.com/>`__:

.. code:: sh

   conda create -n the_simulator python=3.9
   conda activate the_simulator

Installation
~~~~~~~~~~~~

.. code:: sh

   git clone git@github.com:PhysicsOfMobility/theSimulator.git
   cd theSimulator
   pre-commit install
   python setup.py develop
   pytest


Building the Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh
    
    pip install -r requirements-doc.txt
    cd doc
    make html

The documentation can then be found at ``doc/_build/html/index.html``.


First Steps
-----------

-  Start ``jupyter notebook`` or ``jupyter lab``
-  Open one of the introductory notebooks in the ``notebooks``
   subdirectory, either just by clicking on it (``jupyter notebook``) or
   right-clicking and choosing *Open With > Notebook* (``jupyter lab``).
-  Run the notebook and play around :)

Contributing
------------

Generally branch from ``master``, implement stuff® and file a pull
request back to ``master``. Feel free to do the latter at an early
stage, prefixing the pull request with "WIP:".

-  ``master`` should always improve. Incomplete functionality is
   welcome.
-  ``production`` should always be usable and, if possible, not break
   things.

Code style is *black* for Python and *LLVM* for C++. To format your code use

- ``black .`` for Python
- ``find . -regex '.*\.\(cxx\|h\)' -exec clang-format -style=file -i {} \;`` for C++

Testing
~~~~~~~

-  for each new feature introduced, tests should be written, using the
   `pytest <https://docs.pytest.org/en/stable/>`__ framework
-  running tests is easy--just execute ``pytest`` in the project
   directory
-  additional pointers for running pytest:

   -  drop into a debugger on failing test through ``pytest --pdb``
   -  show stdout ``pytest -s``
   -  run specific test by matching test function name string
      ``pytest -k <match expression>``
   -  be more verbose ``pytest -v``

-  Warning 1: Pytest may cause confusion as it automagically imports
   stuff and supplies function with stuff they need based on their
   signature. For this, e.g. see the docs on
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
-  dummy stop **current position element CPE** always must be the first
   entry of each stoplist, denoting the current location of the
   transporter.
-  transporter, vehicle, bus, car

General Things
~~~~~~~~~~~~~~

-  The dispatcher is responsible for keeping the state of the stoplists
   valid. This means e.g. recomputing the estimated arrival times and
   making sure that the order of the stops in the stoplist follows the
   order of the estimated arrival times. It also includes managing the
   CPE.

.. |Code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
