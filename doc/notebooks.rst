Introductory notebooks
======================

This section contains a set of introductory notebooks that will help you get started with RidePy.

You can either view the notebooks as part of this documentation or run them on your machine to try out RidePy yourself.

.. toctree::
    :maxdepth: 1
    :caption: Notebooks included

    Basics <notebooks/introduction>
    Simulations with cython <notebooks/introduction_cython>
    Simulation with cython on graphs <notebooks/introduction_cython_graph>
    Multiple simulations at once <notebooks/introduction_simulation_set>

Executing the notebooks yourself
--------------------------------

To run these notebooks locally, you will first need to install RidePy. Then, either clone the git repository:

.. code:: sh

    git clone --recurse-submodules https://github.com/PhysicsOfMobility/ridepy.git
    cd ridepy

or download the repository as a ZIP archive `here <https://github.com/PhysicsOfMobility/ridepy/archive/refs/heads/master.zip>`_.

To run the notebooks, you will either need `JupyterLab <https://jupyter.org/install#jupyterlab>`_ (recommended) or `Jupyter Notebook <https://jupyter.org/install#jupyter-notebook>`_.

In addition, Jupytext is required to use the MyST-Markdown format in which the notebooks are kept in the repository for easier version control:

.. code:: sh

    pip install -U jupytext

With Jupytext installed, run ``jupyter lab`` or ``jupyter notebook``. Open any of the introductory notebooks in ``doc/notebooks``, either just by clicking on it (in Jupyter Notebook) or by right-clicking and choosing *Open With > Notebook* (in JupyterLab). Now you can run the notebook step-by-step and play around :)
