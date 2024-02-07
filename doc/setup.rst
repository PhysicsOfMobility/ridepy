.. highlight:: bash

Setting up RidePy
=================

This section explains how to set up RidePy on your machine in various ways.

Prerequisites
-------------

Currently, using Python 3.9 is your best option.

In addition, you should probably use a Python environment for keeping things clean. The following commands should work for Linux and macOS. On Windows, things might have to be done marginally different.

We recommend using either `Anaconda <https://www.anaconda.com/>`__ (which has the added benefit of being able to handle different Python versions):

.. code:: sh

    conda create -n ridepy python=3.9
    conda activate ridepy

or simply ``venv`` from the Python standard library (assuming you are already on Python 3.9, alternatively you can additionally use `pyenv <https://github.com/pyenv/pyenv>`__ for managing Python versions):

.. code:: sh

    python -m venv <venv directory path of choice>
    source <venv directory path of choice>/bin/activate

Finally, it may be necessary that you build the Cython/C++ part from source. If you are on a supported platform (currently only x86-64 Linux) and install RidePy via ``pip`` from the PyPI repository, this step can be skipped. Otherwise, you will need a C++ build environment and the `Boost C++ Libraries <https://www.boost.org/>`__.

On Debian-based Linux distributions, both of these can be installed as follows:

.. code:: sh

    sudo apt-get update && sudo apt-get -y install build-essential libboost-all-dev

Installation
------------

User Installation
~~~~~~~~~~~~~~~~~

Just run

.. code:: sh

    pip install ridepy

If you prefer, you can also clone the git repository instead (for which you need ``git``):

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy
    pip install -e .


Developer Installation
~~~~~~~~~~~~~~~~~~~~~~

Note that the editable install (``-e`` flag) does only serve its purpose when editing the Python components. For changes to the Cython/C++ components to come into effect, the ``pip install`` command has to be executed again to build the Cython/C++.

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy
    pip install -e ".[dev,doc]"
    pre-commit install

To build the documentation to ``doc/_build/html``, additionally execute the following command:

.. code:: sh

    sphinx-build -j3 -b html doc doc/_build/html


Testing the installation
------------------------

To check whether the installation was successful, you may run the automated test suite, which should report no errors:

.. code:: sh

    pytest

The built documentation can be found in ``doc/_build/html/index.html``.

Updating the installation
-------------------------

User installation
~~~~~~~~~~~~~~~~~

New PyPI versions of RidePy (after installation using ``pip install ridepy``) can be fetched using

.. code::

    pip install -U ridepy

If you have installed RidePy manually using from git repository, you need to pull the latest version and ``pip``-install the new version:

.. code::

    git pull
    pip install -e .

Developer installation
~~~~~~~~~~~~~~~~~~~~~~

Pull the latest version and ``pip``-install the new version:

.. code::

    git pull
    pip install -e ".[dev,doc]"
    pre-commit install

To update the documentation, additionally execute the following command:

.. code:: sh

    sphinx-build -j3 -b html doc doc/_build/html
