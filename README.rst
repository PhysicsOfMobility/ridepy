|Code style: black| |Tests| |Docs| |wheel| |sdist|

RidePy
======

Simulates a dispatching algorithm serving exogenous transportation requests with a fleet of vehicles. Does not simulate the universe, unlike MATSim. Batteries are included.

The extensive documentation is available at `ridepy.org <https://ridepy.org/>`__. This includes a high-level `overview <https://ridepy.org/overview>`__, as well as a `glossary <https://ridepy.org/glossary>`__ and a detailed `reference <https://ridepy.org/reference>`__.

The source code is hosted on `GitHub <https://github.com/PhysicsOfMobility/ridepy>`__.


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


Finally, a C++ build environment and the `Boost C++ Libraries <https://www.boost.org/>`__
are necessary if you want or need to build the Cython/C++ part from source. This step
can be skipped when installing the Python Wheel via ``pip`` on supported platforms
(currently only x86-64 Linux).

On Debian-based Linux distributions, these dependencies may be installed as follows:

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

.. _first_steps:

First Steps
-----------

-  Start ``jupyter notebook`` or ``jupyter lab``
-  Open one of the introductory notebooks in the ``notebooks``
   subdirectory, either just by clicking on it (in ``jupyter notebook``) or
   right-clicking and choosing *Open With > Notebook* (for ``jupyter lab``).
-  Run the notebook step-by-step and play around :)

Reporting a Problem
-------------------

Should you encounter any problems when using RidePy or have a feature request, 
please don't hesitate to `submit an issue <https://github.com/PhysicsOfMobility/ridepy/issues/new>`__.

Contributing
------------

Generally, branch off from ``master``, implement stuff® and file a pull
request back to ``master``. Feel free to do the latter at an early
stage using the GitHub's "Submit Draft" feature.

Versioning Philosophy:

- ``master`` should always improve. Incomplete functionality is welcome.
- API-breaking changes imply transition to a new major version
- We use `Semantic Versioning <https://semver.org/>`__

Code style is *black* for Python and *LLVM* for C++. To format your code, use

- ``black .`` for Python. Make sure to use the correct version as specified in
  ``pyproject.toml``. It is automatically installed when installing the ``dev``
  extras via ``pip install -e .[dev]``. Also, consider using the pre-commit hook
  (``pre-commit install``).
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
