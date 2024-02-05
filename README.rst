|Code style: black| |Tests| |Docs| |wheel| |sdist|

RidePy
======

Simulates a dispatching algorithm serving exogenous transportation requests with a fleet of vehicles. Does not simulate the universe, unlike MATSim. Batteries are included.

The extensive documentation is available at `ridepy.org <https://ridepy.org/>`__. This includes a high-level `overview <https://ridepy.org/overview>`__, as well as a `glossary <https://ridepy.org/glossary>`__ and a detailed `reference <https://ridepy.org/reference>`__.

The source code is hosted on `GitHub <https://github.com/PhysicsOfMobility/ridepy>`__.


Instructions
------------

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
